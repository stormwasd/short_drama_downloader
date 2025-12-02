"""
新建任务界面
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QFileDialog,
                             QMessageBox, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from pathlib import Path
# 使用绝对导入，兼容打包后的exe
try:
    from src.config import config
except ImportError:
    from ..config import config


class NewTaskWidget(QWidget):
    """新建任务界面"""
    
    task_created = pyqtSignal(dict)  # 任务创建信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_episode_default = 0  # 记录默认值
        self.end_episode_default = 0   # 记录默认值
        self.user_modified_range = False  # 标记用户是否手动修改过剧集区间
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(18)  # 统一间距，让布局更均匀
        layout.setContentsMargins(50, 40, 50, 40)
        
        # 设置整体样式
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
            QMessageBox {
                /* 弹窗使用默认样式，不继承自定义样式 */
            }
            QLineEdit {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 10px;
                font-size: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
            QSpinBox {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 10px;
                padding-right: 30px;
                font-size: 20px;
                min-height: 25px;
            }
            QSpinBox:focus {
                border: 2px solid #4CAF50;
            }
            QSpinBox::up-button {
                background-color: #f5f5f5;
                border: none;
                border-top-right-radius: 6px;
                border-bottom: 1px solid #ddd;
                width: 28px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                right: 1px;
                top: 1px;
            }
            QSpinBox::up-button:hover {
                background-color: #e0e0e0;
            }
            QSpinBox::up-button:pressed {
                background-color: #d0d0d0;
            }
            QSpinBox::up-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 6px solid #666;
                width: 0;
                height: 0;
                margin-left: 4px;
                margin-right: 4px;
            }
            QSpinBox::up-button:hover QSpinBox::up-arrow {
                border-bottom-color: #4CAF50;
            }
            QSpinBox::down-button {
                background-color: #f5f5f5;
                border: none;
                border-bottom-right-radius: 6px;
                width: 28px;
                subcontrol-origin: padding;
                subcontrol-position: bottom right;
                right: 1px;
                bottom: 1px;
            }
            QSpinBox::down-button:hover {
                background-color: #e0e0e0;
            }
            QSpinBox::down-button:pressed {
                background-color: #d0d0d0;
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #666;
                width: 0;
                height: 0;
                margin-left: 4px;
                margin-right: 4px;
            }
            QSpinBox::down-button:hover QSpinBox::down-arrow {
                border-top-color: #4CAF50;
            }
            QComboBox {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 10px 30px 10px 10px;
                font-size: 18px;
                min-height: 20px;
            }
            QComboBox:focus {
                border: 2px solid #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #666;
                width: 0;
                height: 0;
                margin-right: 10px;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #4CAF50;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 2px solid #4CAF50;
                border-radius: 6px;
                selection-background-color: #E3F2FD;
                selection-color: #333;
                padding: 5px;
                font-size: 18px;
            }
            QLabel {
                color: #333;
                font-weight: 600;
                font-size: 22px;
            }
            QPushButton {
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
        """)
        
        # 设置字体
        font = QFont()
        font.setPointSize(config.FONT_SIZE)
        self.setFont(font)
        
        # 统一的标签宽度和字体
        label_width = 100
        name_font = QFont()
        name_font.setPointSize(config.LABEL_FONT_SIZE)
        name_font.setBold(True)
        input_font = QFont()
        input_font.setPointSize(config.INPUT_FONT_SIZE)
        
        # "从"和"到"标签使用相同的字体大小
        range_label_font = QFont()
        range_label_font.setPointSize(config.LABEL_FONT_SIZE)
        range_label_font.setBold(True)
        
        # 任务名称
        name_layout = QHBoxLayout()
        name_layout.setSpacing(15)
        name_label = QLabel("任务名称:")
        name_label.setFixedWidth(label_width)
        name_label.setFont(name_font)
        self.name_input = QLineEdit()
        self.name_input.setFont(input_font)
        self.name_input.setPlaceholderText("例如: shortlinetv的下载任务")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # 来源
        source_layout = QHBoxLayout()
        source_layout.setSpacing(15)
        source_label = QLabel("来源:")
        source_label.setFixedWidth(label_width)
        source_label.setFont(name_font)
        self.source_combo = QComboBox()
        self.source_combo.setFont(input_font)
        self.source_combo.addItems(["shortlinetv", "reelshort"])
        self.source_combo.currentTextChanged.connect(self.on_source_changed)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_combo)
        layout.addLayout(source_layout)
        
        # 剧集名称
        drama_name_layout = QHBoxLayout()
        drama_name_layout.setSpacing(15)
        drama_name_label = QLabel("剧集名称:")
        drama_name_label.setFixedWidth(label_width)
        drama_name_label.setFont(name_font)
        self.drama_name_input = QLineEdit()
        self.drama_name_input.setFont(input_font)
        self.drama_name_input.setPlaceholderText("例如: You Fired a Fashion Icon Full Movie")
        drama_name_layout.addWidget(drama_name_label)
        drama_name_layout.addWidget(self.drama_name_input)
        layout.addLayout(drama_name_layout)
        
        # 剧集网址
        url_layout = QHBoxLayout()
        url_layout.setSpacing(15)
        url_label = QLabel("剧集网址:")
        url_label.setFixedWidth(label_width)
        url_label.setFont(name_font)
        self.url_input = QLineEdit()
        self.url_input.setFont(input_font)
        self.url_input.setPlaceholderText("请输入剧集网址")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # xtoken (仅shortlinetv时显示)
        self.xtoken_layout = QHBoxLayout()
        self.xtoken_layout.setSpacing(15)
        xtoken_label = QLabel("xtoken:")
        xtoken_label.setFixedWidth(label_width)
        xtoken_label.setFont(name_font)
        self.xtoken_input = QLineEdit()
        self.xtoken_input.setFont(input_font)
        self.xtoken_input.setPlaceholderText("例如: 5b8f1e7d3a9c02a446d7e12f891a34bc")
        self.xtoken_layout.addWidget(xtoken_label)
        self.xtoken_layout.addWidget(self.xtoken_input)
        self.xtoken_widget = QWidget()
        self.xtoken_widget.setLayout(self.xtoken_layout)
        self.xtoken_widget.setVisible(False)  # 默认隐藏
        layout.addWidget(self.xtoken_widget)
        
        # uid (仅shortlinetv时显示)
        self.uid_layout = QHBoxLayout()
        self.uid_layout.setSpacing(15)
        uid_label = QLabel("uid:")
        uid_label.setFixedWidth(label_width)
        uid_label.setFont(name_font)
        self.uid_input = QLineEdit()
        self.uid_input.setFont(input_font)
        self.uid_input.setPlaceholderText("例如: 720934815067")
        self.uid_layout.addWidget(uid_label)
        self.uid_layout.addWidget(self.uid_input)
        self.uid_widget = QWidget()
        self.uid_widget.setLayout(self.uid_layout)
        self.uid_widget.setVisible(False)  # 默认隐藏
        layout.addWidget(self.uid_widget)
        
        # 剧集区间（改为一行布局，间距均匀）
        episode_range_layout = QHBoxLayout()
        episode_range_layout.setSpacing(15)
        episode_range_label = QLabel("剧集区间:")
        episode_range_label.setFixedWidth(label_width)
        episode_range_label.setFont(name_font)
        episode_range_layout.addWidget(episode_range_label)
        
        from_label = QLabel("从:")
        from_label.setFont(range_label_font)
        episode_range_layout.addWidget(from_label)
        self.start_episode_spin = QSpinBox()
        self.start_episode_spin.setFont(input_font)
        self.start_episode_spin.setMinimum(0)
        self.start_episode_spin.setMaximum(config.EPISODE_MAX)
        self.start_episode_spin.setValue(0)
        self.start_episode_spin.setFixedWidth(100)
        # 标记用户开始修改
        self.start_episode_spin.valueChanged.connect(lambda: setattr(self, 'user_modified_range', True))
        self.start_episode_spin.valueChanged.connect(self.on_start_episode_changed)
        episode_range_layout.addWidget(self.start_episode_spin)
        
        to_label = QLabel("到:")
        to_label.setFont(range_label_font)
        episode_range_layout.addWidget(to_label)
        self.end_episode_spin = QSpinBox()
        self.end_episode_spin.setFont(input_font)
        self.end_episode_spin.setMinimum(0)
        self.end_episode_spin.setMaximum(config.EPISODE_MAX)
        self.end_episode_spin.setValue(0)
        self.end_episode_spin.setFixedWidth(100)
        # 标记用户开始修改
        self.end_episode_spin.valueChanged.connect(lambda: setattr(self, 'user_modified_range', True))
        self.end_episode_spin.valueChanged.connect(self.on_end_episode_changed)
        episode_range_layout.addWidget(self.end_episode_spin)
        
        # 提示语已注释掉，不再显示
        # tip_label = QLabel("(0-0表示下载所有剧集，手动选择0-0表示只下载第0集)")
        # tip_font = QFont()
        # tip_font.setPointSize(config.LABEL_FONT_SIZE - 2)
        # tip_label.setFont(tip_font)
        # tip_label.setStyleSheet("color: #888;")
        # episode_range_layout.addWidget(tip_label)
        episode_range_layout.addStretch()
        layout.addLayout(episode_range_layout)
        
        # 存储地址
        storage_layout = QHBoxLayout()
        storage_layout.setSpacing(15)
        storage_label = QLabel("存储地址:")
        storage_label.setFixedWidth(label_width)
        storage_label.setFont(name_font)
        self.storage_input = QLineEdit()
        self.storage_input.setFont(input_font)
        self.storage_input.setPlaceholderText("请选择存储文件夹")
        storage_btn = QPushButton("选择文件夹")
        storage_btn.setFont(input_font)
        storage_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        storage_btn.clicked.connect(self.select_storage_path)
        storage_layout.addWidget(storage_label)
        storage_layout.addWidget(self.storage_input)
        storage_layout.addWidget(storage_btn)
        layout.addLayout(storage_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.create_btn = QPushButton("创建任务")
        self.create_btn.setFont(input_font)
        self.create_btn.setFixedWidth(180)
        self.create_btn.setFixedHeight(50)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 17px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.create_btn.clicked.connect(self.create_task)
        button_layout.addWidget(self.create_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 初始化来源变化
        self.on_source_changed(self.source_combo.currentText())
    
    def on_source_changed(self, source: str):
        """来源变化时的处理"""
        # 重置用户修改标记
        self.user_modified_range = False
        if source == "shortlinetv":
            self.url_input.setPlaceholderText("例如: https://shortlinetv.com/videos/xxx")
            self.start_episode_spin.setValue(1)
            self.end_episode_spin.setValue(0)
            self.start_episode_default = 1
            self.end_episode_default = 0
            # 显示xtoken和uid输入框
            self.xtoken_widget.setVisible(True)
            self.uid_widget.setVisible(True)
        elif source == "reelshort":
            self.url_input.setPlaceholderText("例如: https://www.reelshort.com/episodes/trailer-you-fired-a-fashion-icon-687f2a41314aed63020928f9-dr1wo1epdw?play_time=1")
            self.start_episode_spin.setValue(0)
            self.end_episode_spin.setValue(0)
            self.start_episode_default = 0
            self.end_episode_default = 0
            # 隐藏xtoken和uid输入框
            self.xtoken_widget.setVisible(False)
            self.uid_widget.setVisible(False)
    
    def on_start_episode_changed(self, value: int):
        """开始剧集变化时的处理"""
        end_value = self.end_episode_spin.value()
        # 如果结束值大于0且小于开始值，则自动调整（不弹窗）
        if end_value > 0 and end_value < value:
            self.end_episode_spin.setValue(value)
    
    def on_end_episode_changed(self, value: int):
        """结束剧集变化时的处理"""
        start_value = self.start_episode_spin.value()
        # 如果结束值大于0且小于开始值，则自动调整（不弹窗）
        if value > 0 and value < start_value:
            self.end_episode_spin.setValue(start_value)
    
    def select_storage_path(self):
        """选择存储路径"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "选择存储文件夹",
            str(Path.home())
        )
        if path:
            self.storage_input.setText(path)
    
    def create_task(self):
        """创建任务"""
        # 验证输入
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "输入错误", "请输入任务名称！")
            return
        
        if not self.drama_name_input.text().strip():
            QMessageBox.warning(self, "输入错误", "请输入剧集名称！")
            return
        
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "输入错误", "请输入剧集网址！")
            return
        
        if not self.storage_input.text().strip():
            QMessageBox.warning(self, "输入错误", "请选择存储地址！")
            return
        
        # 验证shortlinetv的xtoken和uid
        source = self.source_combo.currentText()
        xtoken = ""
        uid = ""
        if source == "shortlinetv":
            xtoken = self.xtoken_input.text().strip()
            uid = self.uid_input.text().strip()
            if not xtoken:
                QMessageBox.warning(self, "输入错误", "请输入xtoken！")
                return
            if not uid:
                QMessageBox.warning(self, "输入错误", "请输入uid！")
                return
        
        # 验证剧集区间
        start_ep = self.start_episode_spin.value()
        end_ep = self.end_episode_spin.value()
        if end_ep > 0 and end_ep < start_ep:
            QMessageBox.warning(
                self, 
                "输入错误", 
                "结束剧集号必须大于等于开始剧集号！"
            )
            return
        
        # 验证存储路径
        storage_path = Path(self.storage_input.text().strip())
        if not storage_path.exists():
            try:
                storage_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "错误", 
                    f"无法创建存储目录: {str(e)}"
                )
                return
        
        # 判断是否是默认值（用于区分"下载所有"和"只下载第0集"）
        # 只有当值等于默认值且用户没有手动修改过时，才认为是默认值
        is_default_range = (not self.user_modified_range and 
                           start_ep == self.start_episode_default and 
                           end_ep == self.end_episode_default)
        
        # 构建任务数据
        task_data = {
            "task_name": self.name_input.text().strip(),
            "source": self.source_combo.currentText(),
            "drama_name": self.drama_name_input.text().strip(),
            "drama_url": self.url_input.text().strip(),
            "start_episode": start_ep,
            "end_episode": end_ep,
            "storage_path": str(storage_path.absolute()),
            "is_default_range": is_default_range,  # 传递是否是默认值
            "xtoken": xtoken,  # shortlinetv的access-token
            "uid": uid  # shortlinetv的uid-token
        }
        
        # 发送信号（不再在这里显示成功消息，由主窗口统一处理）
        self.task_created.emit(task_data)

