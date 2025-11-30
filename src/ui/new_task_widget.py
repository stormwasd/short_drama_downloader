"""
新建任务界面
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QFileDialog,
                             QMessageBox, QSpinBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path
from ..config import config


class NewTaskWidget(QWidget):
    """新建任务界面"""
    
    task_created = pyqtSignal(dict)  # 任务创建信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 任务名称
        name_layout = QHBoxLayout()
        name_label = QLabel("任务名称:")
        name_label.setFixedWidth(100)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如: shortlinetv的下载任务")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # 来源
        source_layout = QHBoxLayout()
        source_label = QLabel("来源:")
        source_label.setFixedWidth(100)
        self.source_combo = QComboBox()
        self.source_combo.addItems(["shortlinetv", "reelshort"])
        self.source_combo.currentTextChanged.connect(self.on_source_changed)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_combo)
        layout.addLayout(source_layout)
        
        # 剧集名称
        drama_name_layout = QHBoxLayout()
        drama_name_label = QLabel("剧集名称:")
        drama_name_label.setFixedWidth(100)
        self.drama_name_input = QLineEdit()
        self.drama_name_input.setPlaceholderText("例如: You Fired a Fashion Icon Full Movie")
        drama_name_layout.addWidget(drama_name_label)
        drama_name_layout.addWidget(self.drama_name_input)
        layout.addLayout(drama_name_layout)
        
        # 剧集网址
        url_layout = QHBoxLayout()
        url_label = QLabel("剧集网址:")
        url_label.setFixedWidth(100)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入剧集网址")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # 剧集区间
        episode_range_group = QGroupBox("剧集区间")
        episode_range_layout = QHBoxLayout()
        episode_range_layout.addWidget(QLabel("从:"))
        self.start_episode_spin = QSpinBox()
        self.start_episode_spin.setMinimum(0)
        self.start_episode_spin.setMaximum(config.EPISODE_MAX)
        self.start_episode_spin.setValue(0)
        self.start_episode_spin.valueChanged.connect(self.on_start_episode_changed)
        episode_range_layout.addWidget(self.start_episode_spin)
        
        episode_range_layout.addWidget(QLabel("到:"))
        self.end_episode_spin = QSpinBox()
        self.end_episode_spin.setMinimum(0)
        self.end_episode_spin.setMaximum(config.EPISODE_MAX)
        self.end_episode_spin.setValue(0)
        self.end_episode_spin.valueChanged.connect(self.on_end_episode_changed)
        episode_range_layout.addWidget(self.end_episode_spin)
        
        episode_range_layout.addStretch()
        episode_range_group.setLayout(episode_range_layout)
        layout.addWidget(episode_range_group)
        
        # 存储地址
        storage_layout = QHBoxLayout()
        storage_label = QLabel("存储地址:")
        storage_label.setFixedWidth(100)
        self.storage_input = QLineEdit()
        self.storage_input.setPlaceholderText("请选择存储文件夹")
        storage_btn = QPushButton("选择文件夹")
        storage_btn.clicked.connect(self.select_storage_path)
        storage_layout.addWidget(storage_label)
        storage_layout.addWidget(self.storage_input)
        storage_layout.addWidget(storage_btn)
        layout.addLayout(storage_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.create_btn = QPushButton("创建任务")
        self.create_btn.setFixedWidth(120)
        self.create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-size: 14px;
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
        
        layout.addStretch()
        self.setLayout(layout)
        
        # 初始化来源变化
        self.on_source_changed(self.source_combo.currentText())
    
    def on_source_changed(self, source: str):
        """来源变化时的处理"""
        if source == "shortlinetv":
            self.url_input.setPlaceholderText("https://shortlinetv.com/videos/xxx")
            self.start_episode_spin.setValue(1)
        elif source == "reelshort":
            self.url_input.setPlaceholderText("https://www.reelshort.com/episodes/trailer-you-fired-a-fashion-icon-687f2a41314aed63020928f9-dr1wo1epdw?play_time=1")
            self.start_episode_spin.setValue(0)
    
    def on_start_episode_changed(self, value: int):
        """开始剧集变化时的处理"""
        if self.end_episode_spin.value() < value and self.end_episode_spin.value() > 0:
            QMessageBox.warning(
                self, 
                "输入错误", 
                "结束剧集号必须大于等于开始剧集号！"
            )
            self.start_episode_spin.setValue(self.end_episode_spin.value())
    
    def on_end_episode_changed(self, value: int):
        """结束剧集变化时的处理"""
        if value > 0 and value < self.start_episode_spin.value():
            QMessageBox.warning(
                self, 
                "输入错误", 
                "结束剧集号必须大于等于开始剧集号！"
            )
            self.end_episode_spin.setValue(self.start_episode_spin.value())
    
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
        
        # 构建任务数据
        task_data = {
            "task_name": self.name_input.text().strip(),
            "source": self.source_combo.currentText(),
            "drama_name": self.drama_name_input.text().strip(),
            "drama_url": self.url_input.text().strip(),
            "start_episode": start_ep,
            "end_episode": end_ep,
            "storage_path": str(storage_path.absolute())
        }
        
        # 发送信号
        self.task_created.emit(task_data)
        
        # 清空输入（可选）
        # self.name_input.clear()
        # self.drama_name_input.clear()
        # self.url_input.clear()
        # self.storage_input.clear()
        
        QMessageBox.information(self, "成功", "任务创建成功！")

