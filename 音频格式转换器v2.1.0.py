import sys
import os
import threading
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QProgressBar, QTableWidget,
    QTableWidgetItem, QLineEdit, QGroupBox,
    QMessageBox, QHeaderView, QAbstractItemView, QStyledItemDelegate,
    QSplitter, QComboBox, QCheckBox, QSizePolicy
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QSettings
)
from PyQt5.QtGui import (
    QDragEnterEvent, QDropEvent, QFont, QColor, QPixmap, QIcon
)

# 获取资源文件路径
def resource_path(relative_path):
    """获取资源文件的绝对路径，支持PyInstaller打包"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

import resources


class StyledItemDelegate(QStyledItemDelegate):
    """自定义表格项代理，提供更好的视觉反馈"""
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter, option, index):
        # 高亮正在转换的文件
        if hasattr(self.parent(), 'current_converting_file'):
            if index.row() == getattr(self.parent(), 'current_row', -1):
                painter.fillRect(option.rect, QColor(255, 248, 225))  # 浅黄色背景
        
        super().paint(painter, option, index)


class ConvertWorker(QThread):
    """优化的转换工作线程"""
    
    # 信号定义
    progress_update = pyqtSignal(int, str, str, bool)  # 进度, 状态, 文件名, 是否成功
    conversion_complete = pyqtSignal(int, int, int)     # 成功数, 失败数, 跳过数
    file_processing = pyqtSignal(int, str)              # 当前处理文件索引, 文件名
    
    # FFmpeg预设配置
    FORMAT_PRESETS = {
        "mp3": {
            "flags": ["-f", "mp3"],
            "params": ["-c:a", "libmp3lame", "-b:a", "320k", "-q:a", "0"]
        },
        "wav": {
            "flags": ["-f", "wav"],
            "params": ["-c:a", "pcm_s32le"]
        },
        "flac": {
            "flags": ["-f", "flac"],
            "params": ["-c:a", "flac", "-compression_level", "12"]
        },
        "aac": {
            "flags": ["-f", "adts"],
            "params": ["-c:a", "aac", "-b:a", "320k"]
        },
        "ogg": {
            "flags": ["-f", "ogg"],
            "params": ["-c:a", "libvorbis", "-q:a", "10"]
        },
        "m4a": {
            "flags": ["-f", "mp4"],
            "params": ["-c:a", "aac", "-b:a", "320k"]
        },
        "opus": {
            "flags": ["-f", "opus"],
            "params": ["-c:a", "libopus", "-b:a", "192k"]
        }
    }
    
    def __init__(self, files: List[str], output_dir: str, output_format: str):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.output_format = output_format.lower()
        self.stop_flag = threading.Event()
        self.pause_flag = threading.Event()
        self._ffmpeg_path = None  # 缓存FFmpeg路径
        
    @property
    def ffmpeg_path(self):
        """获取FFmpeg路径（带缓存）"""
        if self._ffmpeg_path is None:
            self._ffmpeg_path = self._find_ffmpeg()
        return self._ffmpeg_path
    
    def _find_ffmpeg(self) -> Optional[str]:
        """优化FFmpeg查找逻辑"""
        import shutil
        
        # 检查环境变量
        for cmd in ["ffmpeg", "ffmpeg.exe"]:
            path = shutil.which(cmd)
            if path and os.access(path, os.X_OK):
                return path
        
        # 检查常见目录
        search_paths = [
            os.path.dirname(os.path.abspath(__file__)),
            os.getcwd(),
            os.path.join(os.getcwd(), "ffmpeg"),
            os.path.join(os.path.dirname(sys.executable), "ffmpeg") if hasattr(sys, '_MEIPASS') else None
        ]
        
        for base_path in search_paths:
            if base_path and os.path.exists(base_path):
                # 检查常见文件名
                for filename in ["ffmpeg", "ffmpeg.exe"]:
                    path = os.path.join(base_path, filename)
                    if os.path.exists(path) and os.access(path, os.X_OK):
                        return path
        
        return None
    
    def _get_format_params(self) -> Tuple[List[str], List[str]]:
        """获取格式特定参数"""
        if self.output_format in self.FORMAT_PRESETS:
            preset = self.FORMAT_PRESETS[self.output_format]
            return preset.get("flags", []), preset.get("params", [])
        return [], ["-c:a", "copy"]
    
    def _get_unique_filename(self, filepath: str) -> str:
        """生成唯一的输出文件名"""
        base_path = Path(filepath)
        counter = 1
        
        while base_path.exists():
            new_name = f"{base_path.stem}_{counter}{base_path.suffix}"
            base_path = base_path.parent / new_name
            counter += 1
        
        return str(base_path)
    
    def convert_single_file(self, file_path: str, idx: int) -> Tuple[bool, str]:
        """转换单个文件"""
        if not self.ffmpeg_path:
            return False, "FFmpeg未找到"
        
        try:
            # 准备文件路径
            src_path = Path(file_path)
            output_name = f"{src_path.stem}.{self.output_format}"
            output_path = Path(self.output_dir) / output_name
            
            # 检查并处理重复文件
            if output_path.exists():
                output_path = Path(self._get_unique_filename(str(output_path)))
            
            # 获取格式参数
            format_flags, format_params = self._get_format_params()
            
            # 构建命令
            cmd = [
                self.ffmpeg_path,
                "-i", str(src_path),
                "-y",  # 覆盖输出文件
                "-loglevel", "error",  # 只显示错误信息
                "-stats"  # 显示进度统计
            ]
            
            # 添加格式特定参数
            cmd.extend(format_flags)
            cmd.extend(format_params)
            cmd.append(str(output_path))
            
            # 执行转换
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            # 处理输出并更新进度
            last_progress = 0
            for line in process.stderr:
                if self.stop_flag.is_set():
                    process.terminate()
                    return False, "用户停止"
                
                if self.pause_flag.is_set():
                    while self.pause_flag.is_set() and not self.stop_flag.is_set():
                        self.msleep(100)
                
                # 解析进度信息（如果可用）
                if "time=" in line:
                    try:
                        # 简化进度计算
                        parts = line.split()
                        for part in parts:
                            if part.startswith("time="):
                                time_str = part.split('=')[1]
                                # 将时间转换为秒
                                h, m, s = map(float, time_str.split(':'))
                                current_seconds = h * 3600 + m * 60 + s
                                
                                # 估算文件时长（这里简化处理）
                                estimated_duration = 180  # 假设3分钟
                                progress = min(int((current_seconds / estimated_duration) * 100), 99)
                                
                                if progress > last_progress:
                                    self.progress_update.emit(
                                        progress,
                                        "转换中",
                                        src_path.name,
                                        True
                                    )
                                    last_progress = progress
                    except:
                        pass
            
            process.wait()
            
            if process.returncode == 0:
                return True, str(output_path)
            else:
                return False, f"FFmpeg错误: {process.returncode}"
                
        except Exception as e:
            return False, f"转换异常: {str(e)}"
    
    def run(self):
        """主运行方法"""
        success_count = 0
        fail_count = 0
        skip_count = 0
        total_files = len(self.files)
        
        for idx, file_path in enumerate(self.files):
            if self.stop_flag.is_set():
                break
            
            # 发送文件处理信号
            self.file_processing.emit(idx, Path(file_path).name)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.progress_update.emit(
                    0, f"文件不存在: {file_path}", Path(file_path).name, False
                )
                fail_count += 1
                continue
            
            # 执行转换
            success, message = self.convert_single_file(file_path, idx)
            
            # 更新进度
            progress = int(((idx + 1) / total_files) * 100)
            
            if success:
                success_count += 1
                self.progress_update.emit(
                    progress,
                    f"✓ 转换成功",
                    Path(file_path).name,
                    True
                )
            else:
                fail_count += 1
                self.progress_update.emit(
                    progress,
                    f"✗ 转换失败: {message}",
                    Path(file_path).name,
                    False
                )
            
            # 短暂暂停，让UI有机会更新
            self.msleep(50)
        
        # 发送完成信号
        self.conversion_complete.emit(success_count, fail_count, skip_count)
    
    def pause(self):
        """暂停转换"""
        self.pause_flag.set()
    
    def resume(self):
        """恢复转换"""
        self.pause_flag.clear()
    
    def stop(self):
        """停止转换"""
        self.stop_flag.set()


class AudioConverter(QMainWindow):
    """优化的音频转换器主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化设置
        self.settings = QSettings("AudioConverter", "AudioConverter")
        
        # 初始化变量
        self.media_files = []
        self.convert_thread = None
        self.is_converting = False
        self.current_row = -1
        
        # 颜色方案
        self.colors = {
            "primary": "#4361ee",
            "secondary": "#4cc9f0",
            "accent": "#f72585",
            "text": "#2d3748",
            "text_light": "#718096",
            "background": "#f7fafc",
            "white": "#ffffff",
            "success": "#48bb78",
            "warning": "#ed8936",
            "error": "#f56565",
            "disabled": "#a0aec0",
            "table_header": "#edf2f7",
            "table_row_even": "#f7fafc",
            "table_row_odd": "#ffffff"
        }
        
        # 支持的文件格式
        self.supported_formats = {
            "audio": ["wav", "mp3", "flac", "aac", "ogg", "wma", "m4a", 
                     "aiff", "alac", "ape", "opus", "wv", "dsf", "dff"],
            "video": ["mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", 
                     "mpg", "mpeg", "ts", "m2ts", "3gp", "vob", "ogv"]
        }
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("音频格式转换器 v2.1.0")
        self.setAcceptDrops(True)
        # 移除固定大小，允许调整窗口大小
        # 添加最小大小限制，确保窗口不会变得太小
        self.setMinimumSize(695, 820)
        # 添加最大大小限制，防止窗口过大
        self.setMaximumSize(695, 820)
        
        # 设置窗口图标
        self.setWindowIcon(QIcon(":/logo.ico"))
        
        self.setStyleSheet(self.get_stylesheet())
        self.statusBar().hide()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(15, 15, 15, 15)
       # 标题区域
        title_label = QLabel("音频格式转换器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)
        
        info_layout = QHBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)
        info_layout.setSpacing(5)
        
        info_text = QLabel("作者：凯拓 | 禁止商用 | <a href='https://github.com/Kaituo1/AudioTranscoder' style='color: #4361ee; text-decoration: none; font-size: 12px;'>GitHub</a> | <a href='https://space.bilibili.com/209568678?spm_id_from=333.1007.0.0' style='color: #4361ee; text-decoration: none; font-size: 12px;'>bilibili</a>")
        info_text.setStyleSheet(f"color: {self.colors['text_light']}; font-size: 12px; padding: 0px; margin: 0px;")
        info_text.setTextFormat(Qt.RichText)
        info_text.setOpenExternalLinks(True)
        info_layout.addWidget(info_text)
        
        separator = QLabel("|")
        separator.setStyleSheet(f"color: {self.colors['text_light']}; font-size: 12px; padding: 0px; margin: 0px;")
        info_layout.addWidget(separator)
        
        support_btn = QPushButton("支持作者")
        support_btn.setStyleSheet("""QPushButton {
            background-color: transparent;
            border: none;
            color: #f72585;
            font-size: 12px;
            padding: 0px;
            margin: 0px;
        }
        QPushButton:hover {
            text-decoration: underline;
        }""")
        support_btn.setToolTip("支持作者，打赏一杯咖啡")
        support_btn.clicked.connect(self.show_support_window)
        info_layout.addWidget(support_btn)
        
        info_container = QWidget()
        info_container.setLayout(info_layout)
        main_layout.addWidget(info_container)
        
        splitter = QSplitter(Qt.Vertical)
        
        file_widget = self.create_file_widget()
        splitter.addWidget(file_widget)
        
        control_widget = self.create_control_widget()
        splitter.addWidget(control_widget)
        
        splitter.setSizes([400, 300])
        main_layout.addWidget(splitter, 1)
    
    def create_file_widget(self) -> QWidget:
        """创建文件列表区域"""
        widget = QWidget()
        widget.setContentsMargins(0, 0, 0, 0)
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 文件表格 - 宽度与软件一致，高度固定222
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["文件名", "大小", "格式", "状态"])
        
        # 设置表格高度固定222
        self.file_table.setFixedHeight(222)
        
        # 设置表格属性
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 设置列宽
        header = self.file_table.horizontalHeader()
        # 文件名列占主要宽度，可拉伸
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        # 大小列设置最小宽度，避免内容拥挤
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.resizeSection(1, 100)  # 为大小列设置最小宽度
        # 格式列固定宽度
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.resizeSection(2, 80)   # 为格式列设置固定宽度
        # 状态列固定宽度
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(3, 120)  # 为状态列设置固定宽度
        
        # 设置自定义代理
        self.file_table.setItemDelegate(StyledItemDelegate(self.file_table))
        
        # 创建表格容器，使用层叠布局让提示显示在表格中间
        table_container = QWidget()
        # 使用QVBoxLayout作为基础布局
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        
        # 创建一个相对布局容器来放置表格和提示
        relative_container = QWidget()
        relative_container.setLayout(QVBoxLayout())
        relative_container.layout().setContentsMargins(0, 0, 0, 0)
        
        # 添加表格到相对布局
        relative_container.layout().addWidget(self.file_table)
        
        # 创建拖拽提示标签
        self.drag_hint_label = QLabel("📁 拖拽文件到此处添加")
        self.drag_hint_label.setAlignment(Qt.AlignCenter)
        self.drag_hint_label.setFont(QFont("微软雅黑", 16, QFont.Bold))
        self.drag_hint_label.setStyleSheet(
            f"color: {self.colors['text_light']};")
        # 使用绝对定位将提示标签放在表格中间
        self.drag_hint_label.setParent(relative_container)
        self.drag_hint_label.setGeometry(0, 0, 0, 0)
        self.drag_hint_label.setFixedSize(relative_container.size())
        self.drag_hint_label.setAlignment(Qt.AlignCenter)
        
        # 监听相对容器的大小变化，调整提示标签大小
        relative_container.resizeEvent = lambda event: self.drag_hint_label.setFixedSize(event.size())
        
        # 将相对布局容器添加到主布局
        table_layout.addWidget(relative_container)
        
        # 初始时表格为空，显示提示
        self.update_drag_hint_visibility()
        
        layout.addWidget(table_container, 1)
        
        # 文件操作按钮 - 横向排列在一行，与窗口齐平
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)  # 设置按钮间距
        
        self.add_files_btn = self.create_button("添加文件", self.colors["primary"], self.add_files)
        self.add_folder_btn = self.create_button("添加文件夹", self.colors["secondary"], self.add_folder)
        self.remove_btn = self.create_button("移除所选", self.colors["warning"], self.remove_selected_files)
        self.clear_btn = self.create_button("清空所有", self.colors["error"], self.clear_all_files)
        
        # 设置按钮宽度平均分配，填满窗口
        self.add_files_btn.setMinimumWidth(220)
        self.add_folder_btn.setMinimumWidth(220)
        self.remove_btn.setMinimumWidth(220)
        self.clear_btn.setMinimumWidth(220)
        
        button_layout.addWidget(self.add_files_btn, 1)  # 使用拉伸因子平均分配宽度
        button_layout.addWidget(self.add_folder_btn, 1)
        button_layout.addWidget(self.remove_btn, 1)
        button_layout.addWidget(self.clear_btn, 1)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def create_control_widget(self) -> QWidget:
        """创建控制区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()
        
        # 输出目录
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("输出目录:"))
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(str(Path.home() / "AudioOutput"))
        self.output_dir_edit.setReadOnly(True)
        
        browse_btn = self.create_button("浏览", self.colors["secondary"], 
                                       self.browse_output_dir)
        
        dir_layout.addWidget(self.output_dir_edit, 1)
        dir_layout.addWidget(browse_btn)
        output_layout.addLayout(dir_layout)
        
        # 输出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        
        self.format_combo = QComboBox()
        for format in ["MP3", "WAV", "FLAC", "AAC", "OGG", "M4A", "OPUS"]:
            self.format_combo.addItem(format)
        format_layout.addWidget(self.format_combo, 1)
        
        output_layout.addLayout(format_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # 转换控制
        control_group = QGroupBox("转换控制")
        
        # 使用网格布局帮助居中
        from PyQt5.QtWidgets import QGridLayout
        layout_grid = QGridLayout(control_group)
        layout_grid.setContentsMargins(15, 15, 15, 15)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                background: #f0f0f0;
                min-width: 320px;
                text-align: center;  /* 确保百分比数字居中 */
            }
            QProgressBar::chunk {
                background: #4CAF50;
                border-radius: 2px;
            }
        """)
        
        # 将进度条放在网格中间
        layout_grid.addWidget(self.progress_bar, 0, 0, 1, 3)  # 跨3列
        
        # 进度标签
        self.progress_label = QLabel("等待开始...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout_grid.addWidget(self.progress_label, 1, 0, 1, 3)  # 跨3列
        
        # 控制按钮
        self.start_btn = self.create_button("开始转换", self.colors["primary"], 
                                           self.start_conversion)
        self.pause_btn = self.create_button("暂停", self.colors["warning"], 
                                           self.pause_conversion)
        self.stop_btn = self.create_button("停止", self.colors["error"], 
                                          self.stop_conversion)
        
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        # 添加按钮到网格
        layout_grid.addWidget(self.start_btn, 2, 0)
        layout_grid.addWidget(self.pause_btn, 2, 1)
        layout_grid.addWidget(self.stop_btn, 2, 2)
        
        # 设置列的拉伸比例，让中间列固定，两边列拉伸
        layout_grid.setColumnStretch(0, 1)  # 左列拉伸
        layout_grid.setColumnStretch(1, 1)  # 中列拉伸
        layout_grid.setColumnStretch(2, 1)  # 右列拉伸
        
        layout.addWidget(control_group)
        
        # 选项
        options_group = QGroupBox("选项")
        options_layout = QVBoxLayout()
        
        self.open_folder_check = QCheckBox("转换完成后打开输出文件夹")
        self.open_folder_check.setChecked(True)  # 默认勾选
        
        # 添加窗口置顶选项
        self.always_on_top_check = QCheckBox("窗口置顶")
        self.always_on_top_check.stateChanged.connect(self.toggle_always_on_top)
        
        options_layout.addWidget(self.open_folder_check)
        options_layout.addWidget(self.always_on_top_check)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        return widget
    
    def create_button(self, text: str, color: str, callback) -> QPushButton:
        """创建样式化按钮"""
        btn = QPushButton(text)
        # 构建样式表，使用f-string和双花括号转义CSS选择器
        style = f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color, 20)};
            }}
            QPushButton:disabled {{
                background-color: {self.colors['disabled']};
            }}
        """
        btn.setStyleSheet(style)
        btn.clicked.connect(callback)
        return btn
    
    def get_stylesheet(self) -> str:
        """获取应用样式表"""
        return f"""
            /* 全局样式 */
            * {{
                font-weight: bold;
                font-size: 14px;
                font-family: '微软雅黑', Arial, sans-serif;
            }}
            QMainWindow {{
                background-color: {self.colors['background']};
            }}
            QLabel#titleLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {self.colors['primary']};
                padding: 10px;
            }}
            QTableWidget {{
                background-color: {self.colors['white']};
                alternate-background-color: {self.colors['table_row_even']};
                selection-background-color: {self.colors['primary']}40;
            }}
            QHeaderView::section {{
                background-color: {self.colors['table_header']};
                padding: 5px;
                border: 1px solid {self.colors['background']};
                font-weight: bold;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {self.colors['text_light']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
            QLineEdit {{
                background-color: {self.colors['white']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['text_light']};
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:read-only {{
                background-color: {self.colors['table_row_even']};
                color: {self.colors['text_light']};
            }}
            QLineEdit:focus {{
                border-color: {self.colors['primary']};
                outline: none;
            }}
            QComboBox {{
                background-color: {self.colors['white']};
                color: {self.colors['text']};
                border: 1px solid {self.colors['text_light']};
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                min-width: 150px;
            }}
            QComboBox:focus {{
                border-color: {self.colors['primary']};
                outline: none;
            }}
            QCheckBox {{
                color: {self.colors['text']};
                font-size: 14px;
                padding: 5px;
            }}
        """
    
    def darken_color(self, color: str, percent: int) -> str:
        """颜色变暗"""
        color = QColor(color)
        return color.darker(100 + percent).name()
    
    def load_settings(self):
        """加载设置"""
        # 加载窗口位置和大小
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # 加载输出目录
        output_dir = self.settings.value("output_dir")
        if output_dir:
            self.output_dir_edit.setText(output_dir)
        
        # 加载选项 - 只保留"转换完成后打开输出文件夹"
        self.open_folder_check.setChecked(
            self.settings.value("open_folder", True, type=bool)
        )
    
    def save_settings(self):
        """保存设置"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("output_dir", self.output_dir_edit.text())
        self.settings.setValue("open_folder", self.open_folder_check.isChecked())
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """处理拖拽释放事件"""
        urls = event.mimeData().urls()
        added_files = []
        
        for url in urls:
            file_path = url.toLocalFile()
            if self.is_supported_file(file_path) and file_path not in self.media_files:
                self.media_files.append(file_path)
                added_files.append(file_path)
        
        if added_files:
            self.update_file_table()
            self.statusBar().showMessage(f"已添加 {len(added_files)} 个文件")
    
    def is_supported_file(self, file_path: str) -> bool:
        """检查文件是否支持"""
        ext = Path(file_path).suffix.lower().lstrip('.')
        return (ext in self.supported_formats["audio"] or 
                ext in self.supported_formats["video"])
    
    def update_file_table(self):
        """更新文件表格"""
        self.file_table.setRowCount(0)
        
        for idx, file_path in enumerate(self.media_files):
            path = Path(file_path)
            
            # 获取文件大小
            try:
                size = path.stat().st_size
                size_str = self.format_file_size(size)
            except:
                size_str = "未知"
            
            # 获取文件格式
            ext = path.suffix.lower().lstrip('.')
            
            # 添加行
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)
            
            # 设置单元格
            self.file_table.setItem(row, 0, QTableWidgetItem(path.name))
            self.file_table.setItem(row, 1, QTableWidgetItem(size_str))
            self.file_table.setItem(row, 2, QTableWidgetItem(ext.upper()))
            self.file_table.setItem(row, 3, QTableWidgetItem("等待"))
            
            # 设置文本对齐
            self.file_table.item(row, 1).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.file_table.item(row, 2).setTextAlignment(Qt.AlignCenter)
            self.file_table.item(row, 3).setTextAlignment(Qt.AlignCenter)
        
        self.update_drag_hint_visibility()
    
    def update_drag_hint_visibility(self):
        """更新拖拽提示的可见性"""
        if hasattr(self, 'drag_hint_label'):
            if self.media_files:
                self.drag_hint_label.hide()
            else:
                self.drag_hint_label.show()
    
    def format_file_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def add_files(self):
        """添加文件"""
        formats = " ".join(f"*.{fmt}" for fmt in 
                          self.supported_formats["audio"] + self.supported_formats["video"])
        
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "", 
            f"支持的文件 ({formats});;所有文件 (*.*)"
        )
        
        if files:
            new_files = [f for f in files if f not in self.media_files]
            self.media_files.extend(new_files)
            self.update_file_table()
            
            if new_files:
                self.statusBar().showMessage(f"已添加 {len(new_files)} 个文件")
    
    def add_folder(self):
        """添加文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            new_files = []
            for ext in self.supported_formats["audio"] + self.supported_formats["video"]:
                pattern = f"**/*.{ext}"
                for file in Path(folder).glob(pattern):
                    file_str = str(file)
                    if file_str not in self.media_files:
                        self.media_files.append(file_str)
                        new_files.append(file_str)
            
            if new_files:
                self.update_file_table()
                self.statusBar().showMessage(f"已添加 {len(new_files)} 个文件")
    
    def remove_selected_files(self):
        """移除选中的文件"""
        rows = set(item.row() for item in self.file_table.selectedItems())
        if not rows:
            return
        
        # 从后往前删除
        for row in sorted(rows, reverse=True):
            if row < len(self.media_files):
                self.media_files.pop(row)
        
        self.update_file_table()
    
    def clear_all_files(self):
        """清空所有文件"""
        if self.media_files:
            reply = QMessageBox.question(
                self, "确认", "确定要清空所有文件吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.media_files.clear()
                self.update_file_table()
    
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.output_dir_edit.text()
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def start_conversion(self):
        """开始转换"""
        if not self.media_files:
            QMessageBox.warning(self, "提示", "请先添加要转换的文件")
            return
        
        # 创建输出目录
        output_dir = Path(self.output_dir_edit.text())
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 更新UI状态
        self.is_converting = True
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        # 重置表格状态
        for row in range(self.file_table.rowCount()):
            if item := self.file_table.item(row, 3):
                item.setText("等待")
        
        # 创建并启动工作线程
        self.convert_thread = ConvertWorker(
            self.media_files,
            str(output_dir),
            self.format_combo.currentText()
        )
        
        # 连接信号
        self.convert_thread.progress_update.connect(self.update_progress)
        self.convert_thread.file_processing.connect(self.update_current_file)
        self.convert_thread.conversion_complete.connect(self.conversion_finished)
        
        self.convert_thread.start()
        
        self.statusBar().showMessage("转换开始...")
    
    def pause_conversion(self):
        """暂停转换"""
        if self.convert_thread and self.is_converting:
            if not self.convert_thread.pause_flag.is_set():
                self.convert_thread.pause()
                self.pause_btn.setText("继续")
                self.statusBar().showMessage("转换暂停")
            else:
                self.convert_thread.resume()
                self.pause_btn.setText("暂停")
                self.statusBar().showMessage("转换继续")
    
    def stop_conversion(self):
        """停止转换"""
        if self.convert_thread and self.is_converting:
            reply = QMessageBox.question(
                self, "确认", "确定要停止转换吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.convert_thread.stop()
                self.statusBar().showMessage("正在停止转换...")
    
    def update_progress(self, progress: int, status: str, filename: str, success: bool):
        """更新进度"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"{status}: {filename}")
        
        # 更新表格状态
        for row in range(self.file_table.rowCount()):
            if self.file_table.item(row, 0).text() == filename:
                if item := self.file_table.item(row, 3):
                    item.setText("成功" if success else "失败")
                    item.setForeground(
                        QColor(self.colors["success"] if success else self.colors["error"])
                    )
                break
    
    def update_current_file(self, idx: int, filename: str):
        """更新当前处理文件"""
        self.current_row = idx
        self.file_table.viewport().update()
    
    def conversion_finished(self, success: int, fail: int, skip: int):
        """转换完成"""
        self.is_converting = False
        self.current_row = -1
        
        # 更新UI状态
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("暂停")
        self.stop_btn.setEnabled(False)
        
        # 显示完成消息
        message = f"转换完成！成功: {success}, 失败: {fail}"
        if skip > 0:
            message += f", 跳过: {skip}"
        
        self.statusBar().showMessage(message)
        QMessageBox.information(self, "完成", message)
        
        # 自动打开输出文件夹
        if self.open_folder_check.isChecked() and success > 0:
            self.open_output_folder()
    
    def open_output_folder(self):
        """打开输出文件夹"""
        output_dir = self.output_dir_edit.text()
        if os.path.exists(output_dir):
            if sys.platform == "win32":
                os.startfile(output_dir)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", output_dir])
            else:  # Linux
                subprocess.run(["xdg-open", output_dir])
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.is_converting:
            reply = QMessageBox.question(
                self, "确认", "转换正在进行中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        # 停止工作线程
        if self.convert_thread and self.convert_thread.isRunning():
            self.convert_thread.stop()
            self.convert_thread.wait(2000)  # 等待2秒
        
        # 保存设置
        self.save_settings()
        
        event.accept()
    
    def toggle_always_on_top(self, state):
        """切换窗口置顶状态"""
        if state == Qt.Checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        # 重新显示窗口以应用新的窗口标志
        self.show()
    
    def show_support_window(self):
        """显示支持作者窗口，包含付款码"""
        from PyQt5.QtWidgets import QDialog
        
        # 创建支持窗口（使用QDialog以便使用exec_()方法实现模态窗口）
        support_window = QDialog(self)
        support_window.setWindowTitle("支持作者")
        support_window.setFixedSize(750, 530)
        
        support_window.setWindowFlags(support_window.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 设置窗口图标
        support_window.setWindowIcon(QIcon(":/logo.ico"))
        
        # 主布局
        main_layout = QVBoxLayout(support_window)
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("支持作者，打赏一杯咖啡")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4361ee;")
        main_layout.addWidget(title_label)
        
        # 创建水平图片容器
        image_layout = QHBoxLayout()
        image_layout.setAlignment(Qt.AlignCenter)
        image_layout.setSpacing(20)
        
        # 支付宝图片
        alipay_widget = QWidget()
        alipay_layout = QVBoxLayout(alipay_widget)
        alipay_layout.setAlignment(Qt.AlignCenter)
        alipay_layout.setSpacing(10)
        
        alipay_label = QLabel("支付宝")
        alipay_label.setAlignment(Qt.AlignCenter)
        alipay_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1677ff;")
        alipay_layout.addWidget(alipay_label)
        
        alipay_pixmap = QPixmap(":/支付宝.jpg")
        if not alipay_pixmap.isNull():
            alipay_image = QLabel()
            alipay_image.setPixmap(alipay_pixmap.scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            alipay_layout.addWidget(alipay_image)
        else:
            alipay_error = QLabel("无法加载支付宝图片")
            alipay_error.setAlignment(Qt.AlignCenter)
            alipay_error.setStyleSheet("color: #f56565;")
            alipay_layout.addWidget(alipay_error)
        
        image_layout.addWidget(alipay_widget)
        
        # 微信图片
        wechat_widget = QWidget()
        wechat_layout = QVBoxLayout(wechat_widget)
        wechat_layout.setAlignment(Qt.AlignCenter)
        wechat_layout.setSpacing(10)
        
        wechat_label = QLabel("微信")
        wechat_label.setAlignment(Qt.AlignCenter)
        wechat_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #07c160;")
        wechat_layout.addWidget(wechat_label)
        
        wechat_pixmap = QPixmap(":/微信.png")
        if not wechat_pixmap.isNull():
            wechat_image = QLabel()
            wechat_image.setPixmap(wechat_pixmap.scaled(350, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            wechat_layout.addWidget(wechat_image)
        else:
            wechat_error = QLabel("无法加载微信图片")
            wechat_error.setAlignment(Qt.AlignCenter)
            wechat_error.setStyleSheet("color: #f56565;")
            wechat_layout.addWidget(wechat_error)
        
        image_layout.addWidget(wechat_widget)
        
        main_layout.addLayout(image_layout)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""QPushButton {
            background-color: #4361ee;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
            min-width: 100px;
        }
        QPushButton:hover {
            background-color: #3a50d9;
        }""")
        close_btn.clicked.connect(support_window.close)
        main_layout.addWidget(close_btn)
        
        # 显示模态窗口
        support_window.exec_()


if __name__ == "__main__":
    # 设置高DPI支持
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("音频格式转换器")
    app.setApplicationVersion("2.1.0")
    app.setOrganizationName("AudioTools")
    
    # 设置应用图标
    app.setWindowIcon(QIcon(":/logo.ico"))
    
    converter = AudioConverter()
    converter.show()
    
    sys.exit(app.exec_())