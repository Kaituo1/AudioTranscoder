import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import subprocess
import wave
import struct
import math
import time


class FixedAudioConverter:
    def __init__(self, root):
        self.root = root
        
        # ========== 定义统一的颜色方案 ==========
        self.colors = {
            "primary": "#4CAF50",  # 主色调 - 绿色
            "secondary": "#2196F3",  # 辅助色 - 蓝色
            "accent": "#FF9800",  # 强调色 - 橙色
            "text": "#333333",  # 主文本色 - 深灰色
            "text_light": "#666666",  # 次要文本色 - 中灰色
            "background": "#f5f5f5",  # 背景色 - 浅灰色
            "white": "#ffffff",  # 白色
            "success": "#4CAF50",  # 成功色 - 绿色
            "warning": "#FFC107",  # 警告色 - 黄色
            "error": "#F44336",  # 错误色 - 红色
        }
        
        self.root.title("音频格式转换器v2.0.0")
        # 设置合适的窗口大小，确保所有内容完整显示
        # 适应分类后的格式选项
        self.root.geometry("750x1150")
        # 不允许拖动调整窗口大小，但保留最大化功能（全屏）
        self.root.resizable(False, False)
        # 设置统一的背景色
        self.root.configure(background=self.colors["background"])

        # 存储选择的音视频文件列表
        self.media_files = []

        # ========== 界面组件 ==========
        # 说明文字 - 美化字体和颜色
        self.desc_label = tk.Label(
            root,
            text="原理: 基于FFmpeg实现高质量音频转换，支持多种音频和视频格式，\n支持批量处理，所有格式均采用最高质量设置",
            justify="left",
            font=("微软雅黑", 10),
            fg=self.colors["text"],
            bg=self.colors["background"]
        )
        self.desc_label.pack(pady=8, padx=15, anchor="w")

        # 支持的音频和视频格式
        self.supported_formats = [
            # 音频格式
            "wav", "mp3", "flac", "aac", "ogg", "wma", "m4a", "aiff", "alac", "ape", "opus",
            "wv", "dsf", "dff", "mpc", "speex", "ra", "cda",
            # 视频格式
            "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "mpg", "mpeg", "ts", "m2ts",
            "3gp", "vob", "ogv", "rm", "rmvb"
        ]
        
        # 输入文件列表框
        self.file_list_frame = tk.Frame(root)
        # 让文件列表框架能够垂直扩展
        self.file_list_frame.pack(pady=3, fill="both", expand=True, padx=10)
        self.file_list_label = tk.Label(
            self.file_list_frame, 
            text="已选择文件:",
            font=("微软雅黑", 11, "bold"),
            fg=self.colors["text"],
            bg=self.colors["background"]
        )
        self.file_list_label.pack(anchor="w", pady=(5, 5))
        
        # 创建表格框架
        self.tree_frame = tk.Frame(self.file_list_frame, bg=self.colors["white"])
        self.tree_frame.pack(fill="both", expand=True, pady=2)
        
        # 创建滚动条
        self.tree_scroll = tk.Scrollbar(self.tree_frame)
        self.tree_scroll.pack(side="right", fill="y")
        
        # 创建Treeview表格
        self.file_listbox = ttk.Treeview(
            self.tree_frame, 
            columns=("文件名", "大小", "格式"),
            show="headings",
            yscrollcommand=self.tree_scroll.set,
            selectmode="extended",
            height=1  # 减小高度，只显示1行
        )
        
        # 配置列宽和对齐方式
        self.file_listbox.column("文件名", width=250, anchor="w")
        self.file_listbox.column("大小", width=100, anchor="e")
        self.file_listbox.column("格式", width=80, anchor="center")
        
        # 配置表头
        self.file_listbox.heading("文件名", text="文件名", anchor="w")
        self.file_listbox.heading("大小", text="大小", anchor="center")
        self.file_listbox.heading("格式", text="格式", anchor="center")
        
        # 简化样式配置，避免冲突 - 只设置必要的样式，不使用主题
        style = ttk.Style()
        
        # 只设置必要的样式，不修改背景和前景色
        style.configure("Treeview.Heading", 
                       font=("微软雅黑", 10, "bold"))
        style.configure("Treeview",
                       font=("微软雅黑", 9))
        
        # 放置表格
        self.file_listbox.pack(fill="both", expand=True)
        self.tree_scroll.config(command=self.file_listbox.yview)
        
        # 提示文字 - 将在有文件时移除
        self.empty_label = tk.Label(
            self.tree_frame, 
            text="点击'添加文件'按钮选择文件",
            font=("微软雅黑", 10),
            fg="gray",
            bg=self.colors["white"]
        )
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # 文件统计信息
        self.file_summary_label = tk.Label(
            self.file_list_frame,
            text="",
            font=("微软雅黑", 9),
            fg=self.colors["text_light"],
            bg=self.colors["background"]
        )
        self.file_summary_label.pack(anchor="w", pady=(2, 5))

        # 文件操作按钮
        self.file_ops_frame = tk.Frame(self.file_list_frame)
        self.file_ops_frame.pack(fill="x", pady=5)
        
        # 使用更美观的按钮样式 - 统一的UI设计
        btn_style = {
            "font": ("微软雅黑", 10, "bold"),
            "padx": 15,
            "pady": 8,
            "relief": "flat",
            "borderwidth": 1,
            "highlightthickness": 0,
            "cursor": "hand2",
            "width": 12,  # 固定宽度，确保文字完整显示
            "anchor": "center"  # 文字居中显示
        }
        
        self.add_btn = tk.Button(
            self.file_ops_frame, 
            text="添加文件", 
            command=self.add_files,
            bg="#4CAF50",
            fg="white",
            **btn_style
        )
        self.add_btn.pack(side="left", padx=5, expand=True, fill="x")

        self.add_folder_btn = tk.Button(
            self.file_ops_frame, 
            text="添加文件夹", 
            command=self.add_folder,
            bg="#2196F3",
            fg="white",
            **btn_style
        )
        self.add_folder_btn.pack(side="left", padx=5, expand=True, fill="x")

        self.remove_btn = tk.Button(
            self.file_ops_frame, 
            text="移除所选", 
            command=self.remove_files,
            bg="#f44336",
            fg="white",
            **btn_style
        )
        self.remove_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        self.clear_btn = tk.Button(
            self.file_ops_frame, 
            text="清空所有", 
            command=self.clear_files,
            bg="#FFC107",
            fg="black",
            **btn_style
        )
        self.clear_btn.pack(side="left", padx=5, expand=True, fill="x")

        # 输出目录 - 美化样式
        self.output_frame = tk.Frame(root)
        self.output_frame.pack(pady=8, fill="x", padx=15)
        self.output_label = tk.Label(
            self.output_frame, 
            text="输出目录:",
            font=("微软雅黑", 11, "bold"),
            fg=self.colors["text"]
        )
        self.output_label.pack(side="left", padx=(0, 10))
        self.output_path = tk.StringVar(value=os.path.join(os.getcwd(), "output"))
        self.output_entry = tk.Entry(
            self.output_frame, 
            textvariable=self.output_path, 
            font=("微软雅黑", 10),
            relief="flat",
            borderwidth=1,
            highlightthickness=2,
            highlightbackground=self.colors["background"],
            highlightcolor=self.colors["primary"],
            bg=self.colors["white"],
            fg=self.colors["text"]
        )
        self.output_entry.pack(side="left", padx=5, fill="x", expand=True, ipady=4)
        self.output_btn = tk.Button(
            self.output_frame, 
            text="修改", 
            command=self.choose_output_dir,
            bg=self.colors["secondary"],
            fg=self.colors["white"],
            font=("微软雅黑", 10, "bold"),
            padx=20,
            pady=8,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            activebackground="#1976d2",
            width=8
        )
        self.output_btn.pack(side="left", padx=5)

        # ========== 输出格式选择 ==========
        # 输出格式选择 - 美化样式
        self.format_frame = tk.Frame(root)
        self.format_frame.pack(pady=8, fill="x", padx=15)
        self.format_label = tk.Label(
            self.format_frame, 
            text="输出格式:",
            font=("微软雅黑", 11, "bold"),
            fg=self.colors["text"]
        )
        self.format_label.pack(anchor="w", pady=(0, 5))
        
        # 输出格式分类
        self.format_var = tk.StringVar(value="MP3")
        self.format_buttons = []
        
        # 格式分类定义 - 每个格式只出现在一个分类中
        format_categories = {
            "常用音频格式": ["MP3", "WAV", "FLAC", "AAC"],
            "其他音频格式": ["OGG", "OPUS", "WMA", "AIFF"],
            "移动设备格式": ["M4A", "M4R"],
            "无损格式": ["ALAC", "WV"]
        }
        
        # 创建格式选项框架
        self.format_options_frame = tk.Frame(self.format_frame)
        self.format_options_frame.pack(fill="x", pady=5)
        
        # 按类别显示格式选项
        for category, formats in format_categories.items():
            # 创建分类标签
            category_label = tk.Label(
                self.format_options_frame,
                text=f"{category}:",
                font=("微软雅黑", 10, "bold"),
                fg=self.colors["primary"],
                bg=self.colors["background"]
            )
            category_label.pack(anchor="w", pady=(10, 5), padx=5)
            
            # 创建类别按钮框架
            category_frame = tk.Frame(self.format_options_frame, bg=self.colors["background"])
            category_frame.pack(fill="x", pady=2)
            
            # 添加格式按钮
            for format_name in formats:
                format_btn = tk.Button(
                    category_frame,
                    text=format_name,
                    command=lambda f=format_name: self.format_var.set(f),
                    font=("微软雅黑", 10),
                    bg=self.colors["white"],
                    fg=self.colors["text"],
                    relief="flat",
                    borderwidth=1,
                    padx=12,
                    pady=6,
                    cursor="hand2"
                )
                format_btn.pack(side="left", padx=5, pady=3)
                self.format_buttons.append(format_btn)
        
        # 绑定选中状态更新
        self.format_var.trace_add("write", self.update_format_btn_style)
        
        # 更新初始选中状态
        self.update_format_btn_style()

        # 标签选项 - 美化样式
        self.tag_frame = tk.Frame(root)
        self.tag_frame.pack(pady=8, fill="x", padx=15)
        self.remove_id3 = tk.BooleanVar(value=True)
        self.remove_riff = tk.BooleanVar(value=True)
        self.open_dir = tk.BooleanVar(value=True)
        
        # 创建美化的复选框
        checkbox_style = {
            "font": ("微软雅黑", 10),
            "padx": 10,
            "pady": 5,
            "fg": "#333333",
            "activeforeground": "#1976d2",
            "relief": "flat",
            "cursor": "hand2"
        }
        
        tk.Checkbutton(
            self.tag_frame, 
            text="去掉ID3标签", 
            variable=self.remove_id3,
            selectcolor="#4CAF50",
            **checkbox_style
        ).pack(side="left", padx=10)
        
        tk.Checkbutton(
            self.tag_frame, 
            text="去掉RIFF标签(WAV)", 
            variable=self.remove_riff,
            selectcolor="#4CAF50",
            **checkbox_style
        ).pack(side="left", padx=10)
        
        tk.Checkbutton(
            self.tag_frame, 
            text="自动打开输出目录", 
            variable=self.open_dir,
            selectcolor="#4CAF50",
            **checkbox_style
        ).pack(side="left", padx=10)

        # 转换控制按钮 - 美化样式
        self.convert_btn_frame = tk.Frame(root)
        self.convert_btn_frame.pack(pady=15)
        
        self.convert_btn = tk.Button(
            self.convert_btn_frame, 
            text="开始批量转换", 
            command=self.start_convert_thread,
            font=("微软雅黑", 14, "bold"), 
            bg="#4CAF50", 
            fg="white",
            padx=30,
            pady=12,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            activebackground="#388E3C",  # 鼠标悬停时的颜色
            activeforeground="white",
            bd=0
        )
        self.convert_btn.pack(side="left", padx=10)
        
        # 使用原生tk.Button实现停止按钮，确保背景色正确显示
        # 统一按钮样式配置
        btn_style = {
            "font": ("微软雅黑", 14, "bold"),
            "padx": 30,
            "pady": 12,
            "relief": "flat",
            "borderwidth": 0,
            "highlightthickness": 0,
            "cursor": "hand2",
            "width": 8  # 固定宽度，确保文字完整显示
        }
        
        # 创建停止按钮 - 只使用标准支持的选项
        self.stop_btn = tk.Button(
            self.convert_btn_frame, 
            text="停止转换", 
            command=self.stop_convert,
            bg="#f44336",  # 正常状态红色背景
            fg="white",    # 白色文字
            activebackground="#b71c1c",  # 鼠标悬停/按下时深红色
            activeforeground="white",     # 鼠标悬停/按下时白色文字
            **btn_style
        )
        
        # 手动设置初始禁用状态
        self.stop_btn.config(state="disabled")
        # 手动设置禁用状态的样式
        self.stop_btn.config(bg="#bdbdbd", fg="white")
        
        self.stop_btn.pack(side="left", padx=10)
        
        # 转换控制标志
        self.is_converting = False
        self.stop_requested = False
        self.current_process = None
        
        # 进度条 - 美化样式
        self.progress = ttk.Progressbar(
            root, 
            orient="horizontal", 
            mode="determinate",
            maximum=100
        )
        self.progress["value"] = 0  # 初始状态为0%
        self.progress.pack(pady=12, padx=20, fill="x")
        
        # 进度文本
        self.progress_text = tk.StringVar(value="")
        self.progress_label = tk.Label(
            root, 
            textvariable=self.progress_text,
            font=("微软雅黑", 10),
            fg=self.colors["text"],
            bg=self.colors["background"]
        )
        self.progress_label.pack(pady=5)
        
        # 状态信息 - 美化样式
        self.status_label = tk.Label(
            root, 
            text="等待转换",
            font=("微软雅黑", 12, "italic"),
            fg=self.colors["text_light"],
            bg=self.colors["background"]
        )
        self.status_label.pack(pady=10)
        
        

    def format_file_info(self, file_path):
        """格式化文件信息，返回文件名、大小和格式的元组"""
        try:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # 格式化文件大小
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            elif file_size < 1024 * 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            else:
                size_str = f"{file_size / (1024 * 1024 * 1024):.2f} GB"
            
            # 获取文件格式
            ext = os.path.splitext(file_path)[1].upper().lstrip('.')
            if not ext:
                ext = "未知"
            
            return (filename, size_str, ext)
        except:
            filename = os.path.basename(file_path)
            return (filename, "", "未知")
    
    def update_file_summary(self):
        """更新文件统计信息显示"""
        if not self.media_files:
            self.file_summary_label.config(text="")
            return
        
        total_size = 0
        for file_path in self.media_files:
            try:
                total_size += os.path.getsize(file_path)
            except:
                pass
        
        # 格式化总大小
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        elif total_size < 1024 * 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"
        
        self.file_summary_label.config(
            text=f"共 {len(self.media_files)} 个文件，总计 {size_str}"
        )
    
    # ========== 文件操作 ==========
    def add_files(self):
        # 移除提示文字 - Treeview使用单独的标签显示提示
        if len(self.media_files) == 0 and self.empty_label.winfo_viewable():
            self.empty_label.place_forget()
                
        # 创建支持的文件类型过滤器
        supported_files = ";".join([f"*.{fmt}" for fmt in self.supported_formats])
        
        # 分离音频和视频格式
        audio_formats = [fmt for fmt in self.supported_formats if fmt not in ["mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "mpg", "mpeg", "ts", "m2ts", "3gp", "vob", "ogv", "rm", "rmvb"]]
        video_formats = [fmt for fmt in self.supported_formats if fmt in ["mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "mpg", "mpeg", "ts", "m2ts", "3gp", "vob", "ogv", "rm", "rmvb"]]
        
        audio_files = ";".join([f"*.{fmt}" for fmt in audio_formats])
        video_files = ";".join([f"*.{fmt}" for fmt in video_formats])
        
        files = filedialog.askopenfilenames(
            filetypes=[
                ("所有支持的音视频文件", supported_files),
                ("音频文件", audio_files),
                ("视频文件", video_files),
                ("MP3文件", "*.mp3"),
                ("WAV文件", "*.wav"),
                ("FLAC文件", "*.flac"),
                ("MP4文件", "*.mp4"),
                ("MKV文件", "*.mkv"),
                ("AVI文件", "*.avi"),
                ("所有文件", "*.*")
            ]
        )
        for file in files:
            if file not in self.media_files:
                self.media_files.append(file)
                # 如果是第一个文件，移除提示文字
                if len(self.media_files) == 1:
                    self.empty_label.place_forget()
                # 插入表格行 - Treeview使用空字符串作为父项
                self.file_listbox.insert('', tk.END, values=self.format_file_info(file))
                self.update_file_summary()
    
    def add_folder(self):
        """添加文件夹中的所有支持的音视频文件"""
        # 移除提示文字 - Treeview使用单独的标签显示提示
        if len(self.media_files) == 0 and self.empty_label.winfo_viewable():
            self.empty_label.place_forget()
        
        # 让用户选择文件夹
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        
        # 递归遍历文件夹，获取所有支持的音视频文件
        added_count = 0
        for root_dir, dirs, files in os.walk(folder_path):
            for file in files:
                # 获取文件扩展名
                ext = os.path.splitext(file)[1].lower().lstrip('.')
                if ext in self.supported_formats:
                    file_path = os.path.join(root_dir, file)
                    if file_path not in self.media_files:
                        self.media_files.append(file_path)
                        # 如果是第一个文件，移除提示文字
                        if len(self.media_files) == 1:
                            self.empty_label.place_forget()
                        # 插入表格行 - Treeview使用空字符串作为父项
                        self.file_listbox.insert('', tk.END, values=self.format_file_info(file_path))
                        added_count += 1
        
        if added_count > 0:
            self.update_file_summary()
            messagebox.showinfo("成功", f"已添加 {added_count} 个音视频文件")

    def remove_files(self):
        selected_items = self.file_listbox.selection()
        if not selected_items:
            return
        
        # 从后往前删除，避免索引混乱
        for item in reversed(selected_items):
            idx = self.file_listbox.index(item)
            self.file_listbox.delete(item)
            del self.media_files[idx]
        
        # 如果没有文件了，显示提示文字
        if not self.media_files:
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # 更新统计信息
        self.update_file_summary()
    
    def clear_files(self):
        """清空所有文件"""
        if len(self.media_files) > 0:
            self.file_listbox.delete(*self.file_listbox.get_children())
            self.media_files.clear()
            # 显示提示文字
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
            # 更新统计信息
            self.update_file_summary()

    # ========== 选择输出目录 ==========
    def choose_output_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_path.set(dir_path)

    # ========== 音频处理 ==========
    def resample_audio(self, samples, old_rate, new_rate):
        """重采样音频数据"""
        if old_rate == new_rate:
            return samples

        duration = len(samples) / old_rate
        new_length = int(duration * new_rate)
        new_samples = []

        for i in range(new_length):
            old_pos = i * old_rate / new_rate
            left = int(old_pos)
            right = min(left + 1, len(samples) - 1)
            alpha = old_pos - left
            
            if left == right:
                new_samples.append(samples[left])
            else:
                # 线性插值
                sample = samples[left] * (1 - alpha) + samples[right] * alpha
                new_samples.append(sample)

        return new_samples

    def convert_bit_depth(self, samples, old_depth, new_depth):
        """转换音频位深"""
        if old_depth == new_depth:
            return samples

        # 计算旧位深的取值范围
        old_min = - (2 ** (old_depth - 1))
        old_max = (2 ** (old_depth - 1)) - 1
        
        # 计算新位深的取值范围
        new_min = - (2 ** (new_depth - 1))
        new_max = (2 ** (new_depth - 1)) - 1

        new_samples = []
        for sample in samples:
            # 归一化到[-1, 1]
            normalized = (sample - old_min) / (old_max - old_min) * 2 - 1
            # 转换到新位深范围
            new_sample = normalized * new_max
            # 限制范围
            new_sample = max(new_min, min(new_max, round(new_sample)))
            new_samples.append(int(new_sample))

        return new_samples

    def update_format_btn_style(self, *args):
        """更新输出格式按钮的选中状态"""
        current_format = self.format_var.get()
        for btn in self.format_buttons:
            if btn.cget("text") == current_format:
                btn.configure(
                    bg=self.colors["primary"],
                    fg=self.colors["white"],
                    relief="flat"
                )
            else:
                btn.configure(
                    bg=self.colors["white"],
                    fg=self.colors["text"],
                    relief="flat"
                )

    def find_ffmpeg(self):
        """查找FFmpeg，优先检查系统环境变量，然后检查程序目录"""
        import sys
        import shutil
        
        # 优先检查系统环境变量
        ffmpeg_path = shutil.which("ffmpeg.exe")
        if ffmpeg_path and os.access(ffmpeg_path, os.X_OK):
            return ffmpeg_path
        
        # 处理PyInstaller打包后的情况
        if hasattr(sys, '_MEIPASS'):
            # 这是打包后的环境，_MEIPASS是临时解压目录
            current_dir = os.path.dirname(sys.executable)
        else:
            # 这是普通Python环境
            current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 检查当前目录
        ffmpeg_path = os.path.join(current_dir, "ffmpeg.exe")
        if os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
            return ffmpeg_path
        
        # 检查ffmpeg目录
        ffmpeg_dir = os.path.join(current_dir, "ffmpeg")
        if os.path.exists(ffmpeg_dir):
            ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg.exe")
            if os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                return ffmpeg_path
        
        # 检查bin目录
        bin_dir = os.path.join(current_dir, "bin")
        if os.path.exists(bin_dir):
            ffmpeg_path = os.path.join(bin_dir, "ffmpeg.exe")
            if os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                return ffmpeg_path
        
        return None

    def convert_audio(self, input_file, output_dir):
        """转换音频文件，支持多种格式"""
        try:
            # 获取输出格式
            output_format = self.format_var.get()
            output_ext = output_format.lower()
            
            # 查找FFmpeg
            ffmpeg_path = self.find_ffmpeg()
            if not ffmpeg_path:
                return False, "转换需要FFmpeg，请将ffmpeg.exe放在程序目录下"
            
            # 生成输出文件名
            filename = os.path.basename(input_file)
            name_without_ext = os.path.splitext(filename)[0]
            output_file = os.path.join(output_dir, f"{name_without_ext}.{output_ext}")
            
            # 构建FFmpeg命令 - 简化的转换命令
            cmd = [ffmpeg_path, "-i", input_file]
            
            # 添加全局参数，提高兼容性
            cmd.extend(["-y"])  # 覆盖输出文件
            
            # 确保输出格式正确 - 添加格式标志
            format_flags = {
                "mp3": ["-f", "mp3"],
                "aac": ["-f", "adts"],
                "m4a": ["-f", "mp4"],
                "m4r": ["-f", "mp4"],
                "ogg": ["-f", "ogg"],
                "opus": ["-f", "opus"],
                "wav": ["-f", "wav"],
                "flac": ["-f", "flac"],
                "aiff": ["-f", "aiff"],
                "wv": ["-f", "wv"],
                "alac": ["-f", "mp4"],
                "wma": ["-f", "asf"],
            }
            
            # 添加格式标志
            if output_ext in format_flags:
                cmd.extend(format_flags[output_ext])
            
            # 根据输出格式添加特定参数 - 所有格式都使用最高质量设置
            format_specific_params = {
                "mp3": ["-c:a", "libmp3lame", "-b:a", "320k"],
                "wav": ["-c:a", "pcm_s32le"],
                "flac": ["-c:a", "flac", "-compression_level", "12"],
                "aac": ["-c:a", "aac", "-b:a", "320k"],
                "ogg": ["-c:a", "libvorbis", "-q:a", "10"],
                "m4a": ["-c:a", "aac", "-b:a", "320k"],
                "m4r": ["-c:a", "aac", "-b:a", "320k"],
                "wma": ["-c:a", "wmav2", "-b:a", "320k"],
                "opus": ["-c:a", "libopus", "-b:a", "320k"],
                "aiff": ["-c:a", "pcm_s16be"],
                "alac": ["-c:a", "alac"],
                "wv": ["-c:a", "wavpack"],
            }
            
            # 添加格式特定参数
            if output_ext in format_specific_params:
                cmd.extend(format_specific_params[output_ext])
            else:
                # 默认参数
                cmd.extend(["-c:a", "copy"])
            
            # 确保输出文件路径正确
            cmd.append(output_file)
            
            # 执行转换，不捕获输出，避免缓冲问题
            self.current_process = subprocess.Popen(cmd, 
                                                   stdout=subprocess.DEVNULL,
                                                   stderr=subprocess.DEVNULL,
                                                   creationflags=subprocess.CREATE_NO_WINDOW)
            
            # 循环检查进程状态和停止请求，避免长时间阻塞
            import time
            while self.current_process.poll() is None:  # 进程仍在运行
                if self.stop_requested:  # 检查是否需要停止
                    # 优雅终止进程
                    self.current_process.terminate()
                    # 等待进程终止
                    try:
                        self.current_process.wait(timeout=1.0)  # 等待1秒
                    except subprocess.TimeoutExpired:
                        # 强制终止
                        self.current_process.kill()
                        self.current_process.wait(timeout=0.5)  # 等待0.5秒
                    # 删除可能生成的部分文件
                    if os.path.exists(output_file):
                        try:
                            os.remove(output_file)
                        except:
                            pass
                    return False, "转换已停止"
                # 短暂休眠，避免CPU占用过高
                time.sleep(0.1)
            
            # 检查转换结果
            if self.current_process.returncode != 0:
                # 删除失败的转换文件
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                    except:
                        pass
                return False, f"转换失败，返回码: {self.current_process.returncode}"
            
            # 检查是否在等待过程中收到停止请求
            if self.stop_requested:
                # 删除可能生成的文件
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                    except:
                        pass
                return False, "转换已停止"
            
            return True, output_file

        except Exception as e:
            # 生成输出文件路径，用于删除可能的失败文件
            output_format = self.format_var.get()
            output_ext = output_format.lower()
            filename = os.path.basename(input_file)
            name_without_ext = os.path.splitext(filename)[0]
            output_file = os.path.join(output_dir, f"{name_without_ext}.{output_ext}")
            
            # 删除可能生成的失败文件
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except:
                    pass
            return False, str(e)

    # ========== 批量转换（线程避免UI卡顿） ==========
    def start_convert_thread(self):
        if not self.media_files:
            messagebox.showwarning("提示", "请先添加音视频文件！")
            return
        output_dir = self.output_path.get()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 更新转换状态和按钮状态
        self.is_converting = True
        self.stop_requested = False
        self.convert_btn.config(state="disabled")
        # 手动设置停止按钮为可用状态并显示红色
        self.stop_btn.config(state="normal", bg="#f44336", fg="white")

        # 启动线程执行转换
        threading.Thread(
            target=self.batch_convert,
            args=(output_dir,),
            daemon=True
        ).start()

    def batch_convert(self, output_dir):
        total = len(self.media_files)
        self.progress["maximum"] = total
        self.progress["value"] = 0

        success_count = 0
        fail_count = 0

        for idx, file in enumerate(self.media_files):
            if self.stop_requested:
                break
                
            filename = os.path.basename(file)
            # 更新状态文本
            self.status_label.config(text=f"正在转换: {filename}")
            self.root.update_idletasks()

            try:
                success, result = self.convert_audio(file, output_dir)
                if success:
                    success_count += 1
                    self.progress_text.set(f"✓ 转换成功: {filename}")
                else:
                    fail_count += 1
                    self.progress_text.set(f"✗ 转换失败: {filename} - {result}")
                    if "转换已停止" not in result:
                        messagebox.showerror("转换失败", f"文件 {filename} 转换失败: {result}")
            except Exception as e:
                fail_count += 1
                self.progress_text.set(f"✗ 转换异常: {filename} - {str(e)}")
                messagebox.showerror("转换异常", f"文件 {filename} 转换异常: {str(e)}")

            self.progress["value"] = idx + 1
            self.root.update_idletasks()

        # 转换完成或停止
        if self.stop_requested:
            self.progress_text.set(f"转换已停止！已转换 {success_count} 个文件，失败 {fail_count} 个文件")
            self.status_label.config(text="转换已停止")
        else:
            self.progress_text.set(f"转换完成！成功: {success_count}, 失败: {fail_count}")
            self.status_label.config(text="转换完成")
            messagebox.showinfo("完成", f"已转换{success_count}个文件到{output_dir}")
            if self.open_dir.get() and success_count > 0:
                try:
                    os.startfile(output_dir)
                except:
                    pass
        
        # 恢复按钮状态
        self.is_converting = False
        self.convert_btn.config(state="normal")
        # 手动设置停止按钮为禁用状态并显示灰色
        self.stop_btn.config(state="disabled", bg="#bdbdbd", fg="white")
    
    def stop_convert(self):
        """停止转换，优雅终止进程，避免报错"""
        self.stop_requested = True
        self.status_label.config(text="正在停止转换...")
        self.root.update_idletasks()
        
        # 只设置停止标志，不直接终止进程
        # 让batch_convert函数自然处理停止逻辑，避免强行终止导致的报错
        # 这样可以确保进程有机会清理资源，避免报错
        pass


if __name__ == "__main__":
    # 使用普通的Tk类，不使用拖放功能
    root = tk.Tk()
    app = FixedAudioConverter(root)
    root.mainloop()