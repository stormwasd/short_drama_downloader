"""
主程序入口
"""
import sys
import os
from pathlib import Path

# 确保src目录在Python路径中（用于打包后的exe和开发模式）
# 这个设置必须在导入src模块之前完成
if getattr(sys, 'frozen', False):
    # 打包后的exe模式
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller临时目录（_MEIPASS包含所有打包的文件）
        meipass = Path(sys._MEIPASS)
        # PyInstaller会将所有文件（包括src目录）解压到_MEIPASS
        # 所以需要将_MEIPASS添加到sys.path，这样from src.xxx才能工作
        if str(meipass) not in sys.path:
            sys.path.insert(0, str(meipass))
        
        # 验证src目录是否存在
        if not (meipass / 'src').exists():
            # 如果src不在_MEIPASS中，尝试在exe目录中查找（onedir模式）
            exe_dir = Path(sys.executable).parent
            if (exe_dir / 'src').exists() and str(exe_dir) not in sys.path:
                sys.path.insert(0, str(exe_dir))
else:
    # 开发模式：确保项目根目录在路径中
    # 这样from src.xxx可以正常工作
    src_path = Path(__file__).parent.absolute()
    project_root = src_path.parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# 导入模块 - 只使用绝对导入（入口点不能使用相对导入）
# 注意：作为程序入口点，必须使用绝对导入，相对导入在打包后会失败
try:
    from src.ui.main_window import MainWindow
    from src.config import config
except ImportError as e:
    # 如果绝对导入失败，打印详细的错误信息帮助调试
    print("=" * 60)
    print("导入错误：无法导入必要的模块")
    print("=" * 60)
    print(f"错误详情: {e}")
    print(f"\n当前工作目录: {os.getcwd()}")
    print(f"Python可执行文件: {sys.executable}")
    print(f"是否为打包模式: {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        print(f"PyInstaller临时目录: {sys._MEIPASS}")
        meipass = Path(sys._MEIPASS)
        print(f"  - src目录存在: {(meipass / 'src').exists()}")
        if (meipass / 'src').exists():
            print(f"  - src目录内容: {list((meipass / 'src').iterdir())[:10]}")
    print(f"\nsys.path (前10项):")
    for i, path in enumerate(sys.path[:10], 1):
        print(f"  {i}. {path}")
    print("=" * 60)
    raise


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

