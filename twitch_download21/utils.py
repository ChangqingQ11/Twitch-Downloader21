import os
import re
import json
from datetime import datetime
import tkinter as tk  # 导入 tkinter

def sanitize_filename(filename):
    """移除或替换文件名中的非法字符"""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def create_output_dir():
    """创建以月-日-时间命名的新文件夹"""
    now = datetime.now()
    dir_name = now.strftime("%m-%d-%H-%M-%S")
    output_dir = os.path.join(os.getcwd(), dir_name)
    os.makedirs(output_dir)
    return output_dir

def update_output(message, output_text):
    """更新文本框中的输出"""
    output_text.config(state=tk.NORMAL)
    output_text.insert(tk.END, message)
    output_text.see(tk.END)  # 滚动到最后
    output_text.config(state=tk.DISABLED)

def load_config(reset=False):
    """加载配置文件。如果 reset=True，将配置文件重置为默认值"""
    default_config = {
        "video_id": "",
        "quality": "source",
        "start_time": "00:00:00",
        "end_time": "00:00:00",
        "output_dir": "",
        "file_format": "mp4",
        "split_duration": 300,
        "merge_option": "无"
    }
    
    if reset or not os.path.exists('config.json'):
        save_config(default_config)
        return default_config

    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """保存配置到文件"""
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
