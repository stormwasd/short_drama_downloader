# 短剧下载器

一个功能强大的短剧下载工具，支持 shortlinetv 和 reelshort 两个平台。

## 项目结构

```
short_drama_downloader/
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── main.py            # 主程序入口
│   ├── database.py        # 数据库模型
│   ├── api_clients.py     # API客户端
│   ├── download_manager.py # 下载管理器
│   └── ui/                # UI模块
│       ├── __init__.py
│       ├── main_window.py
│       ├── new_task_widget.py
│       └── task_progress_widget.py
├── build/                  # 构建输出（自动生成）
├── dist/                   # 分发文件（自动生成）
├── requirements.txt        # 依赖列表
├── build_exe.py           # 打包脚本
├── short_drama.spec       # PyInstaller配置文件
├── README.md
└── USAGE.md
```

## 功能特性

- 支持 shortlinetv 和 reelshort 平台
- 可选择性下载指定剧集区间
- 实时显示下载进度
- 任务管理（下载中/已完成）
- 数据持久化存储
- 高并发下载支持
- 支持打包成独立的exe文件
- 统一的配置文件管理（`src/config.py`）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

### 开发模式

```bash
python main.py
```

或者：

```bash
python -m src.main
```

## 打包成exe

### 方法1：使用打包脚本（推荐）

```bash
python build_exe.py
```

### 方法2：使用PyInstaller直接打包

```bash
pyinstaller short_drama.spec
```

打包完成后，exe文件位于 `dist/短剧下载器.exe`

### 打包说明

- 打包后的exe文件是独立的，不需要安装Python环境
- 首次打包可能需要较长时间（5-10分钟）
- 生成的exe文件大小约为100-200MB（包含所有依赖）
- 可以将exe文件单独分发给客户使用

## 使用说明

1. 在"新建任务"界面填写任务信息
2. 选择来源平台（shortlinetv 或 reelshort）
3. 输入剧集网址
4. 选择要下载的剧集区间
5. 选择存储路径
6. 点击开始下载
7. 在"任务进度"界面查看下载状态

详细使用说明请参考 [USAGE.md](USAGE.md)

## 配置说明

所有配置项统一在 `src/config.py` 中管理，包括：

- **下载配置**：最大并发数、队列检查间隔等
- **API配置**：请求超时时间
- **UI配置**：刷新间隔、窗口大小等
- **剧集配置**：最大剧集数、文件名长度限制等
- **数据库配置**：数据库文件名
- **日志配置**：日志级别和格式

修改配置只需编辑 `src/config.py` 文件即可，无需修改其他代码。

