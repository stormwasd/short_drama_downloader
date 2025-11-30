"""
打包脚本 - 使用PyInstaller将Python程序打包成exe
"""
import os
import sys
import subprocess
from pathlib import Path


def build_exe():
    """构建exe文件"""
    # 获取项目根目录
    project_root = Path(__file__).parent.absolute()
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 使用spec文件打包
    spec_file = project_root / "short_drama.spec"
    
    if spec_file.exists():
        print("使用spec文件打包...")
        cmd = [
            "pyinstaller",
            "--clean",
            str(spec_file)
        ]
    else:
        # 如果没有spec文件，使用命令行参数
        print("使用命令行参数打包...")
        cmd = [
            "pyinstaller",
            "--name=短剧下载器",
            "--onefile",  # 打包成单个exe文件
            "--windowed",  # 不显示控制台窗口
            "--hidden-import=PyQt5",
            "--hidden-import=PyQt5.QtCore",
            "--hidden-import=PyQt5.QtWidgets",
            "--hidden-import=PyQt5.QtGui",
            "--hidden-import=yt_dlp",
            "--hidden-import=requests",
            "--hidden-import=aiohttp",
            "--collect-all=yt_dlp",  # 收集yt-dlp的所有数据文件
            "--collect-all=PyQt5",  # 收集PyQt5的所有数据文件
            f"--distpath={project_root / 'dist'}",
            f"--workpath={project_root / 'build'}",
            str(project_root / "src" / "main.py")
        ]
    
    print("开始打包...")
    print(f"命令: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\n打包完成！")
        exe_path = project_root / 'dist' / '短剧下载器.exe'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"exe文件位置: {exe_path}")
            print(f"文件大小: {size_mb:.2f} MB")
        else:
            print("警告: 未找到生成的exe文件")
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()

