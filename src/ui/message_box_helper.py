"""
消息框辅助模块 - 统一管理所有QMessageBox的样式和按钮文字
"""
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QFont


def create_message_box(parent, title: str, text: str, icon=QMessageBox.Information, 
                       buttons=QMessageBox.Ok, default_button=QMessageBox.Ok):
    """
    创建统一样式的消息框
    
    Args:
        parent: 父窗口
        title: 标题
        text: 消息内容
        icon: 图标类型（QMessageBox.Information, QMessageBox.Warning, QMessageBox.Critical, QMessageBox.Question）
        buttons: 按钮组合（QMessageBox.Yes | QMessageBox.No 等）
        default_button: 默认按钮
    
    Returns:
        QMessageBox实例
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setIcon(icon)
    msg_box.setStandardButtons(buttons)
    msg_box.setDefaultButton(default_button)
    
    # 设置统一字体样式：17px，不粗体，与创建任务界面的标签保持一致
    font = QFont()
    font.setPointSize(17)
    font.setBold(False)
    msg_box.setFont(font)
    
    # 先设置样式表，确保所有文本都使用统一字体
    msg_box.setStyleSheet("""
        QMessageBox {
            font-size: 17px;
            font-weight: normal;
        }
        QMessageBox QLabel {
            font-size: 17px;
            font-weight: normal;
        }
        QMessageBox QPushButton {
            font-size: 17px !important;
            font-weight: bold !important;
            min-width: 80px;
            min-height: 35px;
            border: none !important;
            border-radius: 6px;
            padding: 8px 16px;
            background-color: #f0f0f0;
        }
        QMessageBox QPushButton:hover {
            background-color: #e0e0e0;
        }
        QMessageBox QPushButton:pressed {
            background-color: #d0d0d0;
        }
    """)
    
    # 创建按钮字体对象，确保所有按钮字体大小一致，按钮文字加粗
    button_font = QFont()
    button_font.setPointSize(17)
    button_font.setBold(True)  # 按钮文字加粗
    
    # 中文化按钮文字并设置字体 - 在样式表之后设置，确保字体生效
    # 使用button()方法获取按钮对象，然后设置文字和字体
    if buttons & QMessageBox.Yes:
        yes_button = msg_box.button(QMessageBox.Yes)
        if yes_button:
            yes_button.setText("是")
            yes_button.setFont(button_font)  # 单独设置按钮字体，确保生效
    if buttons & QMessageBox.No:
        no_button = msg_box.button(QMessageBox.No)
        if no_button:
            no_button.setText("否")
            no_button.setFont(button_font)  # 单独设置按钮字体，确保生效
    if buttons & QMessageBox.Cancel:
        cancel_button = msg_box.button(QMessageBox.Cancel)
        if cancel_button:
            cancel_button.setText("取消")
            cancel_button.setFont(button_font)  # 单独设置按钮字体，确保生效
    if buttons & QMessageBox.Ok:
        ok_button = msg_box.button(QMessageBox.Ok)
        if ok_button:
            ok_button.setText("确定")
            ok_button.setFont(button_font)  # 单独设置按钮字体，确保生效
    
    # 再次强制设置所有按钮的字体，确保一致性
    # 遍历所有按钮并设置字体
    for button_type in [QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel, QMessageBox.Ok]:
        if buttons & button_type:
            button = msg_box.button(button_type)
            if button:
                button.setFont(button_font)
    
    return msg_box


def _ensure_button_fonts(msg_box, buttons):
    """确保所有按钮字体正确设置 - 在显示前调用"""
    button_font = QFont()
    button_font.setPointSize(17)
    button_font.setBold(True)  # 按钮文字加粗
    
    # 按钮样式表 - 强制设置字体大小、加粗和边框
    button_style = """
        QPushButton {
            font-size: 17px;
            font-weight: bold;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            background-color: #f0f0f0;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
    """
    
    # 遍历所有可能的按钮类型并设置字体和样式
    for button_type in [QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel, QMessageBox.Ok]:
        if buttons & button_type:
            button = msg_box.button(button_type)
            if button:
                # 方法1：直接设置字体对象
                button.setFont(button_font)
                # 方法2：设置样式表（更强制）
                button.setStyleSheet(button_style)
                # 方法3：强制更新
                button.update()


def show_information(parent, title: str, text: str):
    """显示信息消息框"""
    msg_box = create_message_box(parent, title, text, QMessageBox.Information, QMessageBox.Ok)
    # 在显示前再次确保按钮字体正确
    _ensure_button_fonts(msg_box, QMessageBox.Ok)
    return msg_box.exec_()


def show_warning(parent, title: str, text: str):
    """显示警告消息框"""
    msg_box = create_message_box(parent, title, text, QMessageBox.Warning, QMessageBox.Ok)
    # 在显示前再次确保按钮字体正确
    _ensure_button_fonts(msg_box, QMessageBox.Ok)
    return msg_box.exec_()


def show_critical(parent, title: str, text: str):
    """显示错误消息框"""
    msg_box = create_message_box(parent, title, text, QMessageBox.Critical, QMessageBox.Ok)
    # 在显示前再次确保按钮字体正确
    _ensure_button_fonts(msg_box, QMessageBox.Ok)
    return msg_box.exec_()


def show_question(parent, title: str, text: str, 
                 buttons=QMessageBox.Yes | QMessageBox.No, 
                 default_button=QMessageBox.Yes):
    """
    显示询问消息框
    
    Args:
        parent: 父窗口
        title: 标题
        text: 消息内容
        buttons: 按钮组合（默认 Yes | No）
        default_button: 默认按钮（默认 Yes）
    
    Returns:
        用户点击的按钮（QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel 等）
    """
    msg_box = create_message_box(parent, title, text, QMessageBox.Question, buttons, default_button)
    # 在显示前再次确保按钮字体正确
    _ensure_button_fonts(msg_box, buttons)
    return msg_box.exec_()

