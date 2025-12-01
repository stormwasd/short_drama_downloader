"""
PyInstaller运行时hook：修复src包的导入路径
这个hook会在主程序执行之前运行，确保sys.path正确设置
"""
import sys
from pathlib import Path

# 在打包后的exe中，确保src目录在sys.path中
# 这个hook会在main.py之前执行，所以可以提前设置好路径
if getattr(sys, 'frozen', False):
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

