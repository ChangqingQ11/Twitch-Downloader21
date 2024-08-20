import os
import threading
import subprocess
import signal
import tkinter as tk  # 导入 tkinter
from utils import sanitize_filename, create_output_dir, update_output, load_config, save_config

process = None  # 全局变量用于控制下载进程
paused = False  # 全局变量用于表示是否处于暂停状态
stop_flag = False  # 添加一个全局变量用于控制停止操作
progress_file = "download_progress.txt"  # 用于保存下载进度的文件

def format_time_string(hour, minute, second):
    """将小时、分钟和秒组合成 hh:mm:ss 格式的字符串"""
    h = hour.zfill(2) if hour else "00"
    m = minute.zfill(2) if hour else "00"
    s = second.zfill(2) if hour else "00"
    return f"{h}:{m}:{s}"

def download_twitch_video(entry_video_id, quality_var, start_hour, start_minute, start_second,
                          end_hour, end_minute, end_second, output_dir_var, format_var, 
                          split_var, split_duration_var, merge_var, output_text):
    # 加载配置
    config = load_config()
    config['video_id'] = entry_video_id.get().strip()
    config['quality'] = quality_var.get()
    config['start_time'] = format_time_string(start_hour, start_minute, start_second)
    config['end_time'] = format_time_string(end_hour, end_minute, end_second)
    config['output_dir'] = output_dir_var.get().strip()
    config['file_format'] = format_var.get().strip()
    config['split_duration'] = split_duration_var.get() * 60  # 分割时间转换为秒
    config['merge_option'] = merge_var.get()

    if not config['video_id']:
        update_output("错误: 请输入视频ID或URL\n", output_text)
        return

    if not config['output_dir']:
        config['output_dir'] = create_output_dir()

    # 保存配置
    save_config(config)

    if split_var.get():
        threading.Thread(target=split_download_logic, args=(
            config['video_id'], config['quality'], config['start_time'], config['end_time'], 
            config['output_dir'], config['file_format'], config['split_duration'], 
            config['merge_option'], output_text)).start()
    else:
        command = ['twitch-dl', 'download', config['video_id'], '-q', config['quality']]
        if config['start_time'] != "00:00:00":
            command.extend(['-s', config['start_time']])
        if config['end_time'] != "00:00:00":
            command.extend(['-e', config['end_time']])

        sanitized_video_id = sanitize_filename(config['video_id'])
        output_path = os.path.join(config['output_dir'], f"{sanitized_video_id}.{config['file_format']}")
        command.extend(['-o', output_path])

        threading.Thread(target=execute_download, args=(command, config['output_dir'], output_text)).start()

def split_download_logic(video_id, quality, start_time, end_time, output_dir, 
                         file_format, split_duration, merge_option, output_text):
    """处理分割下载逻辑"""
    start_seconds = convert_to_seconds(start_time)
    end_seconds = convert_to_seconds(end_time) if end_time else None
    video_parts = []

    # 恢复下载进度
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            last_downloaded = int(f.read().strip())
            start_seconds = last_downloaded

    global stop_flag  # 引入全局 stop_flag 变量
    stop_flag = False  # 每次调用时重置 stop_flag

    while True:
        if stop_flag:
            update_output("下载已停止。\n", output_text)
            return

        if paused:
            update_output("下载已暂停。\n", output_text)
            return

        segment_end_seconds = start_seconds + split_duration
        if end_seconds and segment_end_seconds > end_seconds:
            segment_end_seconds = end_seconds

        segment_start_time = format_time_string(
            str(start_seconds // 3600), str((start_seconds % 3600) // 60), str(start_seconds % 60))
        segment_end_time = format_time_string(
            str(segment_end_seconds // 3600), str((segment_end_seconds % 3600) // 60), str(segment_end_seconds % 60))

        command = ['twitch-dl', 'download', video_id, '-q', quality, '-s', segment_start_time, '-e', segment_end_time]
        sanitized_video_id = sanitize_filename(video_id)
        output_path = os.path.join(output_dir, f"{sanitized_video_id}_part{start_seconds // split_duration + 1}.{file_format}")
        command.extend(['-o', output_path])

        execute_download(command, output_dir, output_text)
        video_parts.append(output_path)

        # 保存下载进度
        with open(progress_file, "w") as f:
            f.write(str(segment_end_seconds))

        start_seconds += split_duration

        if end_seconds and start_seconds >= end_seconds:
            break

    if merge_option != "无":
        merge_videos(video_parts, output_dir, sanitized_video_id, file_format, merge_option, output_text)

def merge_videos(video_parts, output_dir, base_name, file_format, merge_option, output_text):
    """合并视频片段"""
    update_output("开始合并视频片段...\n", output_text)
    output_file = os.path.join(output_dir, f"{base_name}_merged.{file_format}")
    with open(os.path.join(output_dir, "file_list.txt"), "w") as file_list:
        for part in video_parts:
            file_list.write(f"file '{part}'\n")
    
    command = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', os.path.join(output_dir, 'file_list.txt'),
               '-c', 'copy', output_file]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    process.wait()

    if process.returncode == 0:
        update_output(f"合并完成！输出文件: {output_file}\n", output_text)
        if merge_option == "合并删除":
            for part in video_parts:
                os.remove(part)
            os.remove(os.path.join(output_dir, 'file_list.txt'))
            update_output("原始片段已删除。\n", output_text)
    else:
        update_output(f"合并失败，错误码: {process.returncode}\n", output_text)

def convert_to_seconds(time_str):
    """将 hh:mm:ss 或 hh:mm 格式的时间转换为秒"""
    parts = list(map(int, time_str.split(":")))
    if len(parts) == 2:
        return parts[0] * 3600 + parts[1] * 60  # hh:mm
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]  # hh:mm:ss
    return 0

def execute_download(command, output_dir, output_text):
    global process
    try:
        update_output("下载开始...\n", output_text)

        # 设置环境变量 PYTHONIOENCODING 为 utf-8
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

        # 实时读取 stdout 并更新 UI
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                update_output(line, output_text)

        # 读取剩余的错误输出
        error_output = process.stderr.read()
        if error_output:
            update_output(f"错误输出: {error_output}\n", output_text)

        process.wait()
        if process.returncode == 0:
            update_output("下载完成！\n", output_text)
        else:
            update_output(f"下载过程中出现错误，返回码: {process.returncode}\n", output_text)
    except Exception as e:
        update_output(f"程序运行中出现异常: {str(e)}\n", output_text)


def pause_or_resume(pause_button, output_text):
    global paused
    config = load_config()  # 从配置文件中加载所有变量
    if not paused:
        paused = True
        pause_button.config(text="●")  # 切换为继续图标
        update_output("下载已暂停。\n", output_text)
    else:
        paused = False
        pause_button.config(text="■")  # 切换为暂停图标
        update_output("继续下载...\n", output_text)
        # 继续执行下载逻辑
        threading.Thread(target=split_download_logic, args=(
            config['video_id'], config['quality'], config['start_time'], config['end_time'], 
            config['output_dir'], config['file_format'], config['split_duration'], 
            config['merge_option'], output_text)).start()

def stop_download(pause_button, output_text):
    global process, stop_flag
    stop_flag = True  # 设置停止标志
    if process and process.poll() is None:
        process.terminate()
        update_output("下载已停止。\n", output_text)
        pause_button.config(text="■", state=tk.DISABLED)  # 重置暂停按钮的文本和状态
        if os.path.exists(progress_file):
            os.remove(progress_file)
