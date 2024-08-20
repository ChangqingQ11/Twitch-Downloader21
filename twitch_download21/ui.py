import tkinter as tk
from tkinter import filedialog, scrolledtext
from downloader import download_twitch_video, pause_or_resume, stop_download
from utils import load_config, save_config

def format_time_string(hour, minute, second):
    """将小时、分钟和秒组合成 hh:mm:ss 格式的字符串"""
    h = hour.zfill(2) if hour else "00"
    m = minute.zfill(2) if minute else "00"
    s = second.zfill(2) if hour else "00"
    return f"{h}:{m}:{s}"

def create_ui(reset_config=False):
    # 加载或重置配置
    if reset_config:
        config = load_config(reset=True)  # 重置配置
    else:
        config = load_config()  # 加载配置

    root = tk.Tk()
    root.title("Twitch 视频下载器")

    # 视频ID/URL
    tk.Label(root, text="视频ID或URL:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
    entry_video_id = tk.Entry(root, width=40)
    entry_video_id.insert(0, config.get('video_id', ''))
    entry_video_id.grid(row=0, column=1, padx=10, pady=10)

    # 视频清晰度
    tk.Label(root, text="视频清晰度:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
    quality_var = tk.StringVar(value=config.get('quality', 'source'))
    quality_menu = tk.OptionMenu(root, quality_var, "source", "720p", "480p", "360p", "audio_only")
    quality_menu.grid(row=1, column=1, padx=10, pady=10, sticky="w")

    # 起始时间输入
    tk.Label(root, text="起始时间:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
    start_hour = tk.Entry(root, width=5)
    start_minute = tk.Entry(root, width=5)
    start_second = tk.Entry(root, width=5)
    start_time = config.get('start_time', '00:00:00').split(':')
    start_hour.insert(0, start_time[0])
    start_minute.insert(0, start_time[1])
    start_second.insert(0, start_time[2])
    tk.Label(root, text="hh").grid(row=2, column=1, padx=5, pady=10, sticky="w")
    start_hour.grid(row=2, column=1, padx=(30, 5), pady=10, sticky="w")
    tk.Label(root, text="mm").grid(row=2, column=1, padx=(90, 5), pady=10, sticky="w")
    start_minute.grid(row=2, column=1, padx=(120, 5), pady=10, sticky="w")
    tk.Label(root, text="ss").grid(row=2, column=1, padx=(180, 5), pady=10, sticky="w")
    start_second.grid(row=2, column=1, padx=(210, 5), pady=10, sticky="w")

    # 结束时间输入
    tk.Label(root, text="结束时间:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
    end_hour = tk.Entry(root, width=5)
    end_minute = tk.Entry(root, width=5)
    end_second = tk.Entry(root, width=5)
    end_time = config.get('end_time', '00:00:00').split(':')
    end_hour.insert(0, end_time[0])
    end_minute.insert(0, end_time[1])
    end_second.insert(0, end_time[2])
    tk.Label(root, text="hh").grid(row=3, column=1, padx=5, pady=10, sticky="w")
    end_hour.grid(row=3, column=1, padx=(30, 5), pady=10, sticky="w")
    tk.Label(root, text="mm").grid(row=3, column=1, padx=(90, 5), pady=10, sticky="w")
    end_minute.grid(row=3, column=1, padx=(120, 5), pady=10, sticky="w")
    tk.Label(root, text="ss").grid(row=3, column=1, padx=(180, 5), pady=10, sticky="w")
    end_second.grid(row=3, column=1, padx=(210, 5), pady=10, sticky="w")

    # 输出路径
    tk.Label(root, text="视频下载路径:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
    output_dir_var = tk.StringVar(value=config.get('output_dir', ''))
    entry_output_dir = tk.Entry(root, textvariable=output_dir_var, width=40)
    entry_output_dir.grid(row=4, column=1, padx=10, pady=10)
    tk.Button(root, text="选择路径", command=lambda: choose_output_dir(output_dir_var)).grid(row=4, column=2, padx=10, pady=10)

    # 输出格式
    tk.Label(root, text="输出格式:").grid(row=5, column=0, padx=10, pady=10, sticky="e")
    format_var = tk.StringVar(value=config.get('file_format', 'mp4'))
    format_menu = tk.OptionMenu(root, format_var, "mp4", "mkv", "ts")
    format_menu.grid(row=5, column=1, padx=10, pady=10, sticky="w")

    # 分割下载
    split_var = tk.BooleanVar()
    split_check = tk.Checkbutton(root, text="启用分割下载", variable=split_var, command=lambda: toggle_pause_button(pause_button, split_var))
    split_check.grid(row=6, column=0, sticky="e", padx=10, pady=10)
    split_duration_var = tk.IntVar(value=config.get('split_duration', 300) // 60)
    tk.Entry(root, textvariable=split_duration_var, width=5).grid(row=6, column=1, sticky="w")
    tk.Label(root, text="分钟").grid(row=6, column=1, padx=40, sticky="w")

    # 合并选项
    merge_var = tk.StringVar(value=config.get('merge_option', '无'))
    tk.Label(root, text="视频合并选项:").grid(row=7, column=0, sticky="e", padx=10, pady=10)
    merge_menu = tk.OptionMenu(root, merge_var, "无", "仅合并", "合并删除")
    merge_menu.grid(row=7, column=1, padx=10, pady=10, sticky="w")

    # 输出文本框（用于显示下载进度）
    output_text = scrolledtext.ScrolledText(root, width=60, height=15, state=tk.DISABLED)
    output_text.grid(row=10, column=0, columnspan=3, padx=10, pady=10)

    # 下载按钮
    tk.Button(root, text="下载视频", command=lambda: download_twitch_video(
        entry_video_id, quality_var,
        start_hour.get(), start_minute.get(), start_second.get(),
        end_hour.get(), end_minute.get(), end_second.get(),
        output_dir_var, format_var, split_var, 
        split_duration_var, merge_var, output_text
    )).grid(row=8, column=0, columnspan=3, pady=10)

    # 暂停/继续按钮
    pause_button = tk.Button(root, text="■", font=("Arial", 14), command=lambda: pause_or_resume(
        pause_button, output_text))
    pause_button.grid(row=9, column=0, padx=10, pady=10)
    pause_button.config(state=tk.DISABLED)  # 初始化为禁用状态

    # 停止按钮
    tk.Button(root, text="停止", command=lambda: stop_download(pause_button, output_text)).grid(row=9, column=1, padx=10, pady=10)

    return root

def toggle_pause_button(pause_button, split_var):
    """根据分割下载选项启用或禁用暂停按钮"""
    if split_var.get():
        pause_button.config(state=tk.NORMAL)
    else:
        pause_button.config(state=tk.DISABLED)

def choose_output_dir(output_dir_var):
    """选择视频下载路径"""
    dir_path = filedialog.askdirectory()
    output_dir_var.set(dir_path)
    config = load_config()
    config['output_dir'] = dir_path
    save_config(config)
