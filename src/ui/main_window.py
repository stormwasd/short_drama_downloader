"""
主窗口
"""
import logging
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
# 使用绝对导入，兼容打包后的exe
try:
    from src.database import Database
    from src.api_clients import ShortLineTVClient, ReelShortClient
    from src.download_manager import DownloadManager
    from src.config import config
    from src.ui.new_task_widget import NewTaskWidget
    from src.ui.task_progress_widget import TaskProgressWidget
except ImportError:
    # 如果绝对导入失败，使用相对导入（开发模式）
    from ..database import Database
    from ..api_clients import ShortLineTVClient, ReelShortClient
    from ..download_manager import DownloadManager
    from ..config import config
    from .new_task_widget import NewTaskWidget
    from .task_progress_widget import TaskProgressWidget

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class TaskCreationThread(QThread):
    """任务创建线程，用于异步获取剧集信息"""
    
    finished = pyqtSignal(bool, str, list)  # 完成信号: (success, message, episodes)
    
    def __init__(self, task_data: dict):
        super().__init__()
        self.task_data = task_data
    
    def run(self):
        """执行任务创建"""
        try:
            source = self.task_data['source']
            drama_url = self.task_data['drama_url']
            start_episode = self.task_data['start_episode']
            end_episode = self.task_data['end_episode']
            
            if source == 'shortlinetv':
                client = ShortLineTVClient()
                video_id = client.extract_video_id(drama_url)
                if not video_id:
                    self.finished.emit(False, "无法从URL中提取video_id", [])
                    return
                
                api_data = client.get_episodes(video_id)
                # 传递is_default_range参数
                is_default_range = self.task_data.get('is_default_range', False)
                episodes = client.parse_episodes(api_data, start_episode, end_episode, is_default_range)
            
            elif source == 'reelshort':
                client = ReelShortClient()
                slug = client.extract_slug(drama_url)
                if not slug:
                    self.finished.emit(False, "无法从URL中提取slug", [])
                    return
                
                api_data = client.get_movie_data(slug)
                # 传递is_default_range参数
                is_default_range = self.task_data.get('is_default_range', False)
                episodes = client.parse_episodes(api_data, slug, start_episode, end_episode, is_default_range)
            
            else:
                self.finished.emit(False, f"未知的来源: {source}", [])
                return
            
            if not episodes:
                self.finished.emit(False, "未找到可下载的剧集", [])
                return
            
            self.finished.emit(True, f"成功获取 {len(episodes)} 个剧集", episodes)
        
        except Exception as e:
            logger.error(f"创建任务时出错: {e}")
            self.finished.emit(False, f"创建任务失败: {str(e)}", [])


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.download_manager = None
        self.task_creation_thread = None
        self.init_ui()
        self.init_download_manager()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"短剧下载器 (v{config.VERSION})")
        self.setGeometry(
            config.WINDOW_X, 
            config.WINDOW_Y, 
            config.WINDOW_WIDTH, 
            config.WINDOW_HEIGHT
        )
        
        # 设置窗口图标（如果存在）
        try:
            from PyQt5.QtGui import QIcon
            # 尝试多个可能的路径
            # 打包后的exe，资源文件在临时目录中
            if getattr(sys, 'frozen', False):
                # 打包后的路径
                base_path = Path(sys.executable).parent
                possible_paths = [
                    base_path / "resources" / "icon.ico",  # 打包后的资源路径
                    Path(sys._MEIPASS) / "resources" / "icon.ico" if hasattr(sys, '_MEIPASS') else None,  # PyInstaller临时目录
                ]
                possible_paths = [p for p in possible_paths if p is not None]
            else:
                # 开发模式
                possible_paths = [
                    Path(__file__).parent.parent.parent / "resources" / "icon.ico",
                    Path.cwd() / "resources" / "icon.ico",
                ]
            for icon_path in possible_paths:
                if icon_path.exists():
                    self.setWindowIcon(QIcon(str(icon_path)))
                    logger.info(f"设置窗口图标: {icon_path}")
                    break
        except Exception as e:
            logger.debug(f"设置窗口图标失败: {e}")
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部按钮栏
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(10)
        
        self.new_task_btn = QPushButton("新建任务")
        self.new_task_btn.setCheckable(True)
        self.new_task_btn.setChecked(True)
        self.new_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #1976D2;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """)
        self.new_task_btn.clicked.connect(lambda: self.switch_page(0))
        
        self.progress_btn = QPushButton("任务进度")
        self.progress_btn.setCheckable(True)
        self.progress_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #1976D2;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """)
        self.progress_btn.clicked.connect(lambda: self.switch_page(1))
        
        button_layout.addWidget(self.new_task_btn)
        button_layout.addWidget(self.progress_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 页面堆叠
        self.stacked_widget = QStackedWidget()
        
        # 新建任务页面
        self.new_task_widget = NewTaskWidget()
        self.new_task_widget.task_created.connect(self.on_task_created)
        self.stacked_widget.addWidget(self.new_task_widget)
        
        # 任务进度页面
        self.progress_widget = TaskProgressWidget(self.db)
        self.stacked_widget.addWidget(self.progress_widget)
        
        main_layout.addWidget(self.stacked_widget)
        
        central_widget.setLayout(main_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                font-family: "Microsoft YaHei", "SimHei", Arial;
                font-size: 12px;
            }
            QMessageBox {
                /* 弹窗使用系统默认样式，不继承自定义样式 */
                font-family: initial;
                font-size: initial;
            }
            QMessageBox QLabel {
                font-family: initial;
                font-size: initial;
            }
            QMessageBox QPushButton {
                font-family: initial;
                font-size: initial;
            }
        """)
    
    def init_download_manager(self):
        """初始化下载管理器"""
        def progress_callback(episode_id, progress, status, error_msg=None):
            """进度回调"""
            # 进度更新会通过数据库刷新自动显示
            pass
        
        self.download_manager = DownloadManager(
            self.db,
            max_concurrent=config.MAX_CONCURRENT_DOWNLOADS,
            progress_callback=progress_callback
        )
        self.download_manager.start()
    
    def switch_page(self, index: int):
        """切换页面"""
        self.stacked_widget.setCurrentIndex(index)
        if index == 0:
            self.new_task_btn.setChecked(True)
            self.progress_btn.setChecked(False)
        else:
            self.new_task_btn.setChecked(False)
            self.progress_btn.setChecked(True)
    
    def on_task_created(self, task_data: dict):
        """处理任务创建"""
        # 检查任务名称是否重复
        if self.db.task_name_exists(task_data['task_name']):
            reply = QMessageBox.question(
                self,
                "任务名称重复",
                f"任务名称 '{task_data['task_name']}' 已存在，是否继续创建？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 显示加载提示
        loading_msg = QMessageBox(self)
        loading_msg.setWindowTitle("提示")
        loading_msg.setText("正在获取剧集信息，请稍候...")
        loading_msg.setStandardButtons(QMessageBox.NoButton)
        loading_msg.show()
        QApplication.processEvents()  # 确保消息框显示
        
        # 创建任务创建线程
        self.task_creation_thread = TaskCreationThread(task_data)
        self.task_creation_thread.finished.connect(
            lambda success, msg, episodes: self.on_task_creation_finished(
                success, msg, episodes, task_data, loading_msg
            )
        )
        self.task_creation_thread.start()
    
    def on_task_creation_finished(self, success: bool, message: str, 
                                  episodes: list, task_data: dict, loading_msg=None):
        """任务创建完成回调"""
        # 确保关闭加载提示（在所有情况下）
        try:
            if loading_msg:
                loading_msg.close()
                loading_msg.deleteLater()  # 确保完全释放
        except Exception as e:
            logger.debug(f"关闭loading_msg时出错: {e}")
        
        if not success:
            QMessageBox.critical(self, "错误", message)
            return
        
        # 显示获取到的剧集信息
        reply = QMessageBox.question(
            self,
            "获取剧集信息成功",
            f"{message}\n\n是否创建任务并开始下载？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.No:
            return
        
        try:
            # 创建任务记录
            task_id = self.db.create_task(
                task_name=task_data['task_name'],
                source=task_data['source'],
                drama_name=task_data['drama_name'],
                drama_url=task_data['drama_url'],
                start_episode=task_data['start_episode'],
                end_episode=task_data['end_episode'],
                storage_path=task_data['storage_path']
            )
            
            # 添加剧集
            self.db.add_episodes(task_id, episodes)
            
            # 将剧集添加到下载队列
            task_episodes = self.db.get_task_episodes(task_id)
            for episode in episodes:
                # 通过数据库查询获取episode_id
                for ep in task_episodes:
                    if (ep['episode_num'] == episode['episode_num'] and 
                        ep['episode_url'] == episode['episode_url']):
                        self.download_manager.add_episode(ep['id'])
                        break
            
            # 切换到任务进度页面
            self.switch_page(1)
        
        except Exception as e:
            logger.error(f"保存任务时出错: {e}")
            QMessageBox.critical(
                self,
                "错误",
                f"保存任务失败: {str(e)}"
            )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.download_manager:
            self.download_manager.stop()
        event.accept()

