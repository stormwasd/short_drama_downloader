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
    
    # 检查必要的资源文件
    icon_file = project_root / "resources" / "icon.ico"
    if not icon_file.exists():
        print("警告: 未找到图标文件 resources/icon.ico")
        print("将使用默认图标")
    
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
        print("注意: 确保已安装所有依赖: pip install -r requirements.txt")
        # 注意：使用spec文件时，不能使用--collect-all等命令行选项
        # 这些选项需要在spec文件中配置
        cmd = [
            "pyinstaller",
            "--clean",
            "--noconfirm",  # 不询问确认，直接覆盖
            str(spec_file)
        ]
    else:
        # 如果没有spec文件，使用命令行参数
        print("使用命令行参数打包...")
        icon_arg = []
        if icon_file.exists():
            icon_arg = [f"--icon={icon_file}"]
        
        cmd = [
            "pyinstaller",
            "--name=Dramaseek",
            "--onefile",  # 打包成单个exe文件
            "--windowed",  # 不显示控制台窗口
            "--clean",
            "--noconfirm",
            *icon_arg,
            "--hidden-import=PyQt5",
            "--hidden-import=PyQt5.QtCore",
            "--hidden-import=PyQt5.QtWidgets",
            "--hidden-import=PyQt5.QtGui",
            "--hidden-import=PyQt5.QtCore.Qt",
            "--hidden-import=yt_dlp",
            "--hidden-import=yt_dlp.extractor",
            "--hidden-import=yt_dlp.postprocessor",
            "--hidden-import=requests",
            "--hidden-import=aiohttp",
            "--hidden-import=sqlite3",
            "--collect-all=yt_dlp",  # 收集yt-dlp的所有数据文件
            "--collect-all=PyQt5",  # 收集PyQt5的所有数据文件
            "--add-data", f"{icon_file};resources" if icon_file.exists() else "",
            f"--distpath={project_root / 'dist'}",
            f"--workpath={project_root / 'build'}",
            str(project_root / "src" / "main.py")
        ]
        # 移除空字符串
        cmd = [c for c in cmd if c]
    
    print("开始打包...")
    print(f"命令: {' '.join(cmd)}")
    print("\n注意: 打包过程可能需要几分钟，请耐心等待...")
    
    try:
        subprocess.check_call(cmd, cwd=str(project_root))
        print("\n" + "="*50)
        print("打包完成！")
        print("="*50)
        
        exe_path = project_root / 'dist' / 'Dramaseek_1.0.1_x86_64.exe'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n✓ exe文件位置: {exe_path}")
            print(f"✓ 文件大小: {size_mb:.2f} MB")
            print(f"\n提示: 可以将exe文件复制到任何Windows电脑上运行")
        else:
            print("\n✗ 警告: 未找到生成的exe文件")
            print("请检查打包过程中的错误信息")
            
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 打包失败: {e}")
        print("\n常见问题排查:")
        print("1. 确保所有依赖已安装: pip install -r requirements.txt")
        print("2. 检查是否有Python语法错误")
        print("3. 查看上方的错误信息")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n打包被用户中断")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()

