"""
新建任务界面
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QFileDialog,
                             QMessageBox, QSpinBox, QProxyStyle, QStyleOption, QStyle, QApplication,
                             QStyleOptionComboBox, QStyleOptionSpinBox, QStylePainter, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize, QPoint
from PyQt5.QtGui import QFont, QPainter, QPolygon, QPen, QBrush, QColor
from pathlib import Path
# 使用绝对导入，兼容打包后的exe
try:
    from src.config import config
    from src.ui.message_box_helper import show_warning, show_critical
except ImportError:
    from ..config import config
    from ..ui.message_box_helper import show_warning, show_critical


class CustomComboBox(QComboBox):
    """自定义ComboBox，绘制美观的箭头"""
    
    def paintEvent(self, event):
        """重写绘制事件"""
        super().paintEvent(event)
        
        # 绘制自定义箭头
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取下拉箭头区域
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        style = self.style()
        arrow_rect = style.subControlRect(QStyle.CC_ComboBox, opt, QStyle.SC_ComboBoxArrow, self)
        
        if arrow_rect.isValid():
            # 绘制向下箭头
            center_x = arrow_rect.center().x()
            center_y = arrow_rect.center().y()
            arrow_size = 7
            
            arrow = QPolygon()
            arrow.append(QPoint(int(center_x - arrow_size), int(center_y - 3)))
            arrow.append(QPoint(int(center_x + arrow_size), int(center_y - 3)))
            arrow.append(QPoint(int(center_x), int(center_y + 4)))
            
            painter.setPen(QPen(QColor(85, 85, 85), 1.5))
            painter.setBrush(QBrush(QColor(85, 85, 85)))
            painter.drawPolygon(arrow)


class CustomSpinBox(QSpinBox):
    """自定义SpinBox，绘制美观的箭头"""
    
    def paintEvent(self, event):
        """重写绘制事件"""
        super().paintEvent(event)
        
        # 绘制自定义箭头
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取上下箭头区域
        opt = QStyleOptionSpinBox()
        self.initStyleOption(opt)
        style = self.style()
        
        up_rect = style.subControlRect(QStyle.CC_SpinBox, opt, QStyle.SC_SpinBoxUp, self)
        down_rect = style.subControlRect(QStyle.CC_SpinBox, opt, QStyle.SC_SpinBoxDown, self)
        
        arrow_size = 6
        
        # 绘制向上箭头
        if up_rect.isValid():
            center_x = up_rect.center().x()
            center_y = up_rect.center().y()
            
            arrow = QPolygon()
            arrow.append(QPoint(int(center_x - arrow_size), int(center_y + 3)))
            arrow.append(QPoint(int(center_x + arrow_size), int(center_y + 3)))
            arrow.append(QPoint(int(center_x), int(center_y - 3)))
            
            painter.setPen(QPen(QColor(85, 85, 85), 1.5))
            painter.setBrush(QBrush(QColor(85, 85, 85)))
            painter.drawPolygon(arrow)
        
        # 绘制向下箭头
        if down_rect.isValid():
            center_x = down_rect.center().x()
            center_y = down_rect.center().y()
            
            arrow = QPolygon()
            arrow.append(QPoint(int(center_x - arrow_size), int(center_y - 3)))
            arrow.append(QPoint(int(center_x + arrow_size), int(center_y - 3)))
            arrow.append(QPoint(int(center_x), int(center_y + 3)))
            
            painter.setPen(QPen(QColor(85, 85, 85), 1.5))
            painter.setBrush(QBrush(QColor(85, 85, 85)))
            painter.drawPolygon(arrow)




class NewTaskWidget(QWidget):
    """新建任务界面"""
    
    task_created = pyqtSignal(dict)  # 任务创建信号
    
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db  # 数据库实例，用于保存和读取设置
        self.start_episode_default = 1  # 记录默认值
        self.end_episode_default = 1   # 记录默认值
        self.user_modified_range = False  # 标记用户是否手动修改过剧集区间
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)  # 均分布局间距
        layout.setContentsMargins(50, 20, 50, 40)  # 减小顶部间距，均分布局
        
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
                font-size: 17px;
                text-align: left;
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
                font-size: 17px;
                min-height: 25px;
                text-align: left;
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
                width: 0px;
                height: 0px;
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
                width: 0px;
                height: 0px;
            }
            QComboBox {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 10px 30px 10px 10px;
                font-size: 17px;
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
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 2px solid #4CAF50;
                border-radius: 6px;
                selection-background-color: #E3F2FD;
                selection-color: #333;
                padding: 5px;
                font-size: 17px;
            }
            QLabel {
                color: #333;
                font-weight: normal;
                font-size: 17px;
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
        
        # 统一的标签宽度和字体（与创建任务按钮一致，17px，不粗体）
        label_width = 100
        # 统一的输入框和下拉框宽度（除了SpinBox）
        input_width = 550
        name_font = QFont()
        name_font.setPointSize(17)
        name_font.setBold(False)
        input_font = QFont()
        input_font.setPointSize(17)
        
        # "从"和"到"标签使用相同的字体大小
        range_label_font = QFont()
        range_label_font.setPointSize(17)
        range_label_font.setBold(False)
        
        # 辅助函数：创建带红色星号的必填项标签文字
        def create_required_label_text(text: str, show_asterisk: bool = True) -> str:
            """创建带红色星号的必填项标签文字"""
            if show_asterisk:
                return f"{text}<span style='color: red;'>*</span>"
            else:
                return text
        
        # 保存标签引用，用于动态更新红色星号
        self.name_label = None
        self.source_label = None
        self.drama_name_label = None
        self.url_label = None
        self.xtoken_label = None
        self.uid_label = None
        self.episode_range_label = None
        self.storage_label = None
        
        # 任务名称
        name_layout = QHBoxLayout()
        name_layout.setSpacing(10)  # 缩小间距
        name_layout.setContentsMargins(0, 0, 0, 0)  # 确保没有额外边距
        self.name_label = QLabel(create_required_label_text("任务名称:", True))
        self.name_label.setFixedWidth(label_width)
        self.name_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.name_label.setFont(name_font)
        self.name_label.setTextFormat(Qt.RichText)  # 启用富文本格式以显示HTML
        self.name_input = QLineEdit()
        self.name_input.setFont(input_font)
        self.name_input.setPlaceholderText("例如: shortlinetv的下载任务")
        # 监听文本变化，动态更新红色星号
        self.name_input.textChanged.connect(lambda: self.update_required_indicator(self.name_label, "任务名称:", self.name_input.text().strip()))
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.name_input, 1)  # 添加拉伸因子，确保对齐
        layout.addLayout(name_layout)
        
        # 来源
        source_layout = QHBoxLayout()
        source_layout.setSpacing(10)  # 缩小间距
        source_layout.setContentsMargins(0, 0, 0, 0)  # 确保没有额外边距
        self.source_label = QLabel(create_required_label_text("来源:", False))  # 有默认值，初始不显示星号
        self.source_label.setFixedWidth(label_width)
        self.source_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.source_label.setFont(name_font)
        self.source_label.setTextFormat(Qt.RichText)  # 启用富文本格式以显示HTML
        self.source_combo = CustomComboBox()
        self.source_combo.setFont(input_font)
        self.source_combo.addItems(["shortlinetv", "reelshort"])
        self.source_combo.currentTextChanged.connect(self.on_source_changed)
        # 监听选择变化，动态更新红色星号（来源有默认值，所以不需要星号）
        # source_combo 有默认值，所以不需要显示星号
        source_layout.addWidget(self.source_label)
        source_layout.addWidget(self.source_combo, 1)  # 添加拉伸因子，确保对齐
        layout.addLayout(source_layout)
        
        # 剧集名称
        drama_name_layout = QHBoxLayout()
        drama_name_layout.setSpacing(10)  # 缩小间距
        drama_name_layout.setContentsMargins(0, 0, 0, 0)  # 确保没有额外边距
        self.drama_name_label = QLabel(create_required_label_text("剧集名称:", True))
        self.drama_name_label.setFixedWidth(label_width)
        self.drama_name_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.drama_name_label.setFont(name_font)
        self.drama_name_label.setTextFormat(Qt.RichText)  # 启用富文本格式以显示HTML
        self.drama_name_input = QLineEdit()
        self.drama_name_input.setFont(input_font)
        self.drama_name_input.setPlaceholderText("例如: You Fired a Fashion Icon Full Movie")
        # 监听文本变化，动态更新红色星号
        self.drama_name_input.textChanged.connect(lambda: self.update_required_indicator(self.drama_name_label, "剧集名称:", self.drama_name_input.text().strip()))
        drama_name_layout.addWidget(self.drama_name_label)
        drama_name_layout.addWidget(self.drama_name_input, 1)  # 添加拉伸因子，确保对齐
        layout.addLayout(drama_name_layout)
        
        # 剧集网址
        url_layout = QHBoxLayout()
        url_layout.setSpacing(10)  # 缩小间距
        url_layout.setContentsMargins(0, 0, 0, 0)  # 确保没有额外边距
        self.url_label = QLabel(create_required_label_text("剧集网址:", True))
        self.url_label.setFixedWidth(label_width)
        self.url_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.url_label.setFont(name_font)
        self.url_label.setTextFormat(Qt.RichText)  # 启用富文本格式以显示HTML
        self.url_input = QLineEdit()
        self.url_input.setFont(input_font)
        self.url_input.setPlaceholderText("请输入剧集网址")
        # 监听文本变化，动态更新红色星号
        self.url_input.textChanged.connect(lambda: self.update_required_indicator(self.url_label, "剧集网址:", self.url_input.text().strip()))
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.url_input, 1)  # 添加拉伸因子，确保对齐
        layout.addLayout(url_layout)
        
        # xtoken (仅shortlinetv时显示)
        # 关键：由于xtoken_layout被包装在QWidget中，QWidget添加到主布局时会继承主布局的50px左边距
        # 所以xtoken_layout的左边距应该设置为0，让它与其他layout保持一致，确保标签列对齐
        # 同时需要确保QWidget能够水平拉伸，与其他输入框保持一致的长度
        self.xtoken_layout = QHBoxLayout()
        self.xtoken_layout.setSpacing(10)  # 缩小间距
        # 左边距设置为0，继承主布局的50px左边距，确保标签列对齐
        self.xtoken_layout.setContentsMargins(0, 0, 0, 0)
        self.xtoken_label = QLabel(create_required_label_text("xtoken:", True))
        self.xtoken_label.setFixedWidth(label_width)
        self.xtoken_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.xtoken_label.setFont(name_font)
        self.xtoken_label.setTextFormat(Qt.RichText)  # 启用富文本格式以显示HTML
        self.xtoken_input = QLineEdit()
        self.xtoken_input.setFont(input_font)
        self.xtoken_input.setPlaceholderText("例如: 5b8f1e7d3a9c02a446d7e12f891a34bc")
        # 监听文本变化，动态更新红色星号
        self.xtoken_input.textChanged.connect(lambda: self.update_required_indicator(self.xtoken_label, "xtoken:", self.xtoken_input.text().strip()))
        self.xtoken_layout.addWidget(self.xtoken_label)
        self.xtoken_layout.addWidget(self.xtoken_input, 1)  # 添加拉伸因子，确保对齐
        self.xtoken_widget = QWidget()
        self.xtoken_widget.setLayout(self.xtoken_layout)
        # 关键：设置QWidget的大小策略，允许水平拉伸，确保与其他输入框长度一致
        self.xtoken_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.xtoken_widget.setVisible(False)  # 默认隐藏
        layout.addWidget(self.xtoken_widget, 0)  # 添加拉伸因子0，与其他layout保持一致
        
        # uid (仅shortlinetv时显示)
        # 关键：由于uid_layout被包装在QWidget中，QWidget添加到主布局时会继承主布局的50px左边距
        # 所以uid_layout的左边距应该设置为0，让它与其他layout保持一致，确保标签列对齐
        # 同时需要确保QWidget能够水平拉伸，与其他输入框保持一致的长度
        self.uid_layout = QHBoxLayout()
        self.uid_layout.setSpacing(10)  # 缩小间距
        # 左边距设置为0，继承主布局的50px左边距，确保标签列对齐
        self.uid_layout.setContentsMargins(0, 0, 0, 0)
        self.uid_label = QLabel(create_required_label_text("uid:", True))
        self.uid_label.setFixedWidth(label_width)
        self.uid_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.uid_label.setFont(name_font)
        self.uid_label.setTextFormat(Qt.RichText)  # 启用富文本格式以显示HTML
        self.uid_input = QLineEdit()
        self.uid_input.setFont(input_font)
        self.uid_input.setPlaceholderText("例如: 720934815067")
        # 监听文本变化，动态更新红色星号
        self.uid_input.textChanged.connect(lambda: self.update_required_indicator(self.uid_label, "uid:", self.uid_input.text().strip()))
        self.uid_layout.addWidget(self.uid_label)
        self.uid_layout.addWidget(self.uid_input, 1)  # 添加拉伸因子，确保对齐
        self.uid_widget = QWidget()
        self.uid_widget.setLayout(self.uid_layout)
        # 关键：设置QWidget的大小策略，允许水平拉伸，确保与其他输入框长度一致
        self.uid_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.uid_widget.setVisible(False)  # 默认隐藏
        layout.addWidget(self.uid_widget, 0)  # 添加拉伸因子0，与其他layout保持一致
        
        # 剧集区间（改为一行布局，间距均匀）
        episode_range_layout = QHBoxLayout()
        episode_range_layout.setSpacing(10)  # 缩小间距
        episode_range_layout.setContentsMargins(0, 0, 0, 0)  # 确保没有额外边距
        self.episode_range_label = QLabel(create_required_label_text("剧集区间:", False))  # 有默认值，初始不显示星号
        self.episode_range_label.setFixedWidth(label_width)
        self.episode_range_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.episode_range_label.setFont(name_font)
        self.episode_range_label.setTextFormat(Qt.RichText)  # 启用富文本格式以显示HTML
        episode_range_layout.addWidget(self.episode_range_label)
        
        from_label = QLabel("从:")
        from_label.setFont(range_label_font)
        episode_range_layout.addWidget(from_label)
        self.start_episode_spin = CustomSpinBox()
        self.start_episode_spin.setFont(input_font)
        self.start_episode_spin.setMinimum(0)
        self.start_episode_spin.setMaximum(config.EPISODE_MAX)
        self.start_episode_spin.setValue(1)
        self.start_episode_spin.setFixedWidth(100)
        # 标记用户开始修改，并更新红色星号
        def on_start_episode_changed():
            setattr(self, 'user_modified_range', True)
            self.update_episode_range_indicator()
        self.start_episode_spin.valueChanged.connect(on_start_episode_changed)
        # 移除自动同步逻辑，让左右独立
        episode_range_layout.addWidget(self.start_episode_spin)
        
        to_label = QLabel("到:")
        to_label.setFont(range_label_font)
        episode_range_layout.addWidget(to_label)
        self.end_episode_spin = CustomSpinBox()
        self.end_episode_spin.setFont(input_font)
        self.end_episode_spin.setMinimum(0)
        self.end_episode_spin.setMaximum(config.EPISODE_MAX)
        self.end_episode_spin.setValue(1)
        self.end_episode_spin.setFixedWidth(100)
        # 标记用户开始修改，并更新红色星号
        def on_end_episode_changed():
            setattr(self, 'user_modified_range', True)
            self.update_episode_range_indicator()
        self.end_episode_spin.valueChanged.connect(on_end_episode_changed)
        # 移除自动同步逻辑，让左右独立
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
        storage_layout.setSpacing(10)  # 缩小间距
        storage_layout.setContentsMargins(0, 0, 0, 0)  # 确保没有额外边距
        self.storage_label = QLabel(create_required_label_text("存储地址:", True))
        self.storage_label.setFixedWidth(label_width)
        self.storage_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐
        self.storage_label.setFont(name_font)
        self.storage_label.setTextFormat(Qt.RichText)  # 启用富文本格式以显示HTML
        self.storage_input = QLineEdit()
        self.storage_input.setFont(input_font)
        self.storage_input.setPlaceholderText("请选择存储文件夹")
        # 加载最后使用的存储路径
        if self.db:
            last_storage_path = self.db.get_setting('last_storage_path')
            if last_storage_path:
                self.storage_input.setText(last_storage_path)
                # 如果有默认值，更新红色星号
                self.update_required_indicator(self.storage_label, "存储地址:", self.storage_input.text().strip())
        # 监听文本变化，动态更新红色星号
        self.storage_input.textChanged.connect(lambda: self.update_required_indicator(self.storage_label, "存储地址:", self.storage_input.text().strip()))
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
                font-size: 17px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        storage_btn.clicked.connect(self.select_storage_path)
        storage_layout.addWidget(self.storage_label)
        storage_layout.addWidget(self.storage_input, 1)  # 添加拉伸因子，确保对齐
        storage_layout.addWidget(storage_btn)
        layout.addLayout(storage_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.create_btn = QPushButton("创建任务")
        self.create_btn.setFont(input_font)
        # 不设置固定宽度，让按钮根据内容自动调整，与其他按钮一致
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
        
        # 初始化时更新所有必填项的红色星号状态
        # 检查存储地址是否有默认值
        if self.storage_input.text().strip():
            self.update_required_indicator(self.storage_label, "存储地址:", self.storage_input.text().strip())
        # 更新剧集区间的星号（有默认值1，所以不显示星号）
        self.update_episode_range_indicator()
    
    def update_required_indicator(self, label: QLabel, base_text: str, value: str):
        """
        更新必填项标签的红色星号显示
        
        Args:
            label: 标签对象
            base_text: 基础文本（如"任务名称:"）
            value: 输入框的值
        """
        if not label:
            return
        # 如果值为空，显示红色星号；如果有值，隐藏红色星号
        if value:
            label.setText(base_text)  # 无星号
        else:
            label.setText(f"{base_text}<span style='color: red;'>*</span>")  # 有星号
    
    def update_episode_range_indicator(self):
        """更新剧集区间标签的红色星号显示"""
        if not self.episode_range_label:
            return
        # 检查两个SpinBox的值是否都是默认值1
        start_val = self.start_episode_spin.value()
        end_val = self.end_episode_spin.value()
        # 如果都是1且用户没有修改过，认为已填写（有默认值）
        if start_val == 1 and end_val == 1 and not self.user_modified_range:
            self.episode_range_label.setText("剧集区间:")  # 无星号
        else:
            # 如果用户修改过，检查是否有效（至少有一个值大于0）
            if start_val > 0 or end_val > 0:
                self.episode_range_label.setText("剧集区间:")  # 无星号
            else:
                self.episode_range_label.setText("剧集区间:<span style='color: red;'>*</span>")  # 有星号
    
    def on_source_changed(self, source: str):
        """来源变化时的处理"""
        # 重置用户修改标记
        self.user_modified_range = False
        # 更新剧集区间的红色星号（因为重置了默认值）
        self.update_episode_range_indicator()
        if source == "shortlinetv":
            self.url_input.setPlaceholderText("例如: https://shortlinetv.com/videos/xxx")
            self.start_episode_spin.setValue(1)
            self.end_episode_spin.setValue(1)
            self.start_episode_default = 1
            self.end_episode_default = 1
            # 显示xtoken和uid输入框
            self.xtoken_widget.setVisible(True)
            self.uid_widget.setVisible(True)
        elif source == "reelshort":
            self.url_input.setPlaceholderText("例如: https://www.reelshort.com/episodes/trailer-you-fired-a-fashion-icon-687f2a41314aed63020928f9-dr1wo1epdw?play_time=1")
            self.start_episode_spin.setValue(1)
            self.end_episode_spin.setValue(1)
            self.start_episode_default = 1
            self.end_episode_default = 1
            # 隐藏xtoken和uid输入框
            self.xtoken_widget.setVisible(False)
            self.uid_widget.setVisible(False)
    
    # 已移除自动同步逻辑，让左右数字独立调整
    
    def select_storage_path(self):
        """选择存储路径"""
        # 如果有上次的路径，默认打开上次的路径
        default_path = self.storage_input.text().strip() or str(Path.home())
        if self.db:
            last_storage_path = self.db.get_setting('last_storage_path')
            if last_storage_path:
                default_path = last_storage_path
        
        path = QFileDialog.getExistingDirectory(
            self, 
            "选择存储文件夹",
            default_path
        )
        if path:
            self.storage_input.setText(path)
            # 更新红色星号（因为已填写）
            self.update_required_indicator(self.storage_label, "存储地址:", path)
            # 保存到数据库
            if self.db:
                self.db.set_setting('last_storage_path', path)
    
    def create_task(self):
        """创建任务"""
        # 验证输入
        if not self.name_input.text().strip():
            show_warning(self, "输入错误", "请输入任务名称！")
            return
        
        if not self.drama_name_input.text().strip():
            show_warning(self, "输入错误", "请输入剧集名称！")
            return
        
        if not self.url_input.text().strip():
            show_warning(self, "输入错误", "请输入剧集网址！")
            return
        
        if not self.storage_input.text().strip():
            show_warning(self, "输入错误", "请选择存储地址！")
            return
        
        # 验证shortlinetv的xtoken和uid
        source = self.source_combo.currentText()
        xtoken = ""
        uid = ""
        if source == "shortlinetv":
            xtoken = self.xtoken_input.text().strip()
            uid = self.uid_input.text().strip()
            if not xtoken:
                show_warning(self, "输入错误", "请输入xtoken！")
                return
            if not uid:
                show_warning(self, "输入错误", "请输入uid！")
                return
        
        # 验证剧集区间
        start_ep = self.start_episode_spin.value()
        end_ep = self.end_episode_spin.value()
        if end_ep > 0 and end_ep < start_ep:
            show_warning(
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
                show_critical(
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
        
        # 保存存储路径到数据库（用于下次默认填充）
        if self.db:
            self.db.set_setting('last_storage_path', str(storage_path.absolute()))
        
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

