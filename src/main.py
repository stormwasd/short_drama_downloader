"""
主程序入口
"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from .ui.main_window import MainWindow
from .config import config


def main():
    """主函数"""
    # 验证配置
    try:
        config.validate()
    except ValueError as e:
        print(f"配置错误: {e}")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

