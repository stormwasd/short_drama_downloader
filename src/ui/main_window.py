"""
主窗口
"""
import logging
import sys
import re
import requests
import urllib3
from urllib.parse import urlparse, urlunparse
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path

# 禁用urllib3的SSL警告（用于下载封面时跳过证书验证）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# 使用绝对导入，兼容打包后的exe
try:
    from src.database import Database
    from src.api_clients import ShortLineTVClient, ReelShortClient
    from src.download_manager import DownloadManager
    from src.config import config
    from src.ui.new_task_widget import NewTaskWidget
    from src.ui.task_progress_widget import TaskProgressWidget
    from src.ui.message_box_helper import show_information, show_warning, show_critical, show_question
except ImportError:
    # 如果绝对导入失败，使用相对导入（开发模式）
    from ..database import Database
    from ..api_clients import ShortLineTVClient, ReelShortClient
    from ..download_manager import DownloadManager
    from ..config import config
    from .new_task_widget import NewTaskWidget
    from .task_progress_widget import TaskProgressWidget
    from .message_box_helper import show_information, show_warning, show_critical, show_question

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


def download_cover_image(cover_url: str, save_path: Path) -> bool:
    """下载封面图片
    
    Args:
        cover_url: 封面图片URL
        save_path: 保存路径（包含文件名）
        
    Returns:
        bool: 是否下载成功
    """
    if not cover_url:
        return False
    
    try:
        # 处理URL中的多余斜杠
        # 将URL解析为组件，然后重新组合以去除多余的斜杠
        parsed = urlparse(cover_url)
        # 清理path中的多余斜杠
        clean_path = re.sub(r'/+', '/', parsed.path)
        # 重新组合URL
        clean_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            clean_path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        # 使用基本的headers下载图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        
        # 下载图片（跳过SSL证书验证，与视频下载保持一致）
        response = requests.get(clean_url, headers=headers, timeout=config.API_TIMEOUT, stream=True, verify=False)
        response.raise_for_status()
        
        # 确保目录存在
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"封面图片下载成功: {save_path}")
        return True
    
    except Exception as e:
        logger.error(f"下载封面图片失败: {e}")
        return False


class TaskCreationThread(QThread):
    """任务创建线程，用于异步获取剧集信息"""
    
    finished = pyqtSignal(bool, str, list, str)  # 完成信号: (success, message, episodes, cover_url)
    
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
            
            cover_url = None
            
            if source == 'shortlinetv':
                # 获取xtoken和uid（如果提供）
                xtoken = self.task_data.get('xtoken')
                uid = self.task_data.get('uid')
                client = ShortLineTVClient(xtoken=xtoken, uid=uid)
                video_id = client.extract_video_id(drama_url)
                if not video_id:
                    self.finished.emit(False, "无法从URL中提取video_id", [], "")
                    return
                
                api_data = client.get_episodes(video_id)
                # 传递is_default_range参数
                is_default_range = self.task_data.get('is_default_range', False)
                episodes, cover_url = client.parse_episodes(api_data, start_episode, end_episode, is_default_range)
            
            elif source == 'reelshort':
                client = ReelShortClient()
                slug = client.extract_slug(drama_url)
                if not slug:
                    self.finished.emit(False, "无法从URL中提取slug", [], "")
                    return
                
                # 传递drama_url以动态获取buildId
                api_data = client.get_movie_data(slug, drama_url=drama_url)
                # 传递is_default_range参数
                is_default_range = self.task_data.get('is_default_range', False)
                episodes, cover_url = client.parse_episodes(api_data, slug, start_episode, end_episode, is_default_range)
            
            else:
                self.finished.emit(False, f"未知的来源: {source}", [], "")
                return
            
            if not episodes:
                self.finished.emit(False, "未找到可下载的剧集", [], "")
                return
            
            # 构建成功消息（只显示剧集数量，封面数量在用户确认创建任务后显示）
            message = f"成功获取 {len(episodes)} 个剧集"
            if cover_url:
                message += "，检测到1个封面"
            
            # 只传递封面URL，不下载封面（在用户确认创建任务后再下载）
            self.finished.emit(True, message, episodes, cover_url or "")
        
        except Exception as e:
            logger.error(f"创建任务时出错: {e}")
            self.finished.emit(False, f"创建任务失败: {str(e)}", [], "")


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
        self.setWindowTitle(f"Dramaseek (v{config.VERSION})")
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
        
        # 顶部按钮栏（右边距与创建任务按钮对齐，50px）
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 10, 50, 10)
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
                border-radius: 6px;
                font-size: 17px;
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
                border-radius: 6px;
                font-size: 17px;
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
        
        button_layout.addStretch()
        button_layout.addWidget(self.new_task_btn)
        button_layout.addWidget(self.progress_btn)
        
        main_layout.addLayout(button_layout)
        
        # 页面堆叠
        self.stacked_widget = QStackedWidget()
        
        # 新建任务页面
        self.new_task_widget = NewTaskWidget(db=self.db)
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
            /* QMessageBox样式由message_box_helper统一管理 */
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
            reply = show_question(
                self,
                "任务名称重复",
                f"任务名称 '{task_data['task_name']}' 已存在，是否继续创建？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 显示加载提示
        try:
            from src.ui.message_box_helper import create_message_box
        except ImportError:
            from ..ui.message_box_helper import create_message_box
        loading_msg = create_message_box(
            self, 
            "提示", 
            "正在获取剧集信息，请稍候...",
            QMessageBox.Information,
            QMessageBox.NoButton
        )
        loading_msg.show()
        QApplication.processEvents()  # 确保消息框显示
        
        # 创建任务创建线程
        self.task_creation_thread = TaskCreationThread(task_data)
        self.task_creation_thread.finished.connect(
            lambda success, msg, episodes, cover_url: self.on_task_creation_finished(
                success, msg, episodes, cover_url, task_data, loading_msg
            )
        )
        self.task_creation_thread.start()
    
    def on_task_creation_finished(self, success: bool, message: str, 
                                  episodes: list, cover_url: str, task_data: dict, loading_msg=None):
        """任务创建完成回调"""
        # 确保关闭加载提示（在所有情况下）
        try:
            if loading_msg:
                loading_msg.close()
                loading_msg.deleteLater()  # 确保完全释放
        except Exception as e:
            logger.debug(f"关闭loading_msg时出错: {e}")
        
        if not success:
            show_critical(self, "错误", message)
            return
        
        # 显示获取到的剧集信息
        reply = show_question(
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
                storage_path=task_data['storage_path'],
                xtoken=task_data.get('xtoken'),  # shortlinetv的access-token
                uid=task_data.get('uid')  # shortlinetv的uid-token
            )
            
            # 添加剧集
            self.db.add_episodes(task_id, episodes)
            
            # 下载封面图片（在用户确认创建任务后）
            cover_count = 0
            if cover_url and task_data.get('storage_path'):
                try:
                    storage_path = task_data.get('storage_path')
                    drama_name = task_data.get('drama_name', 'Unknown')
                    
                    # 构建保存路径
                    base_storage_path = Path(storage_path)
                    # 清理文件夹名中的非法字符和控制字符
                    safe_drama_name = config.sanitize_filename(drama_name)
                    
                    # 创建剧集名称文件夹
                    drama_storage_path = base_storage_path / safe_drama_name
                    drama_storage_path.mkdir(parents=True, exist_ok=True)
                    
                    # 确定封面文件扩展名
                    parsed_url = urlparse(cover_url)
                    path = parsed_url.path
                    # 尝试从URL中提取扩展名
                    if '.' in path:
                        ext = path.split('.')[-1].split('?')[0].lower()
                        # 验证扩展名是否合理（常见图片格式）
                        if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                            ext = 'jpg'  # 默认使用jpg
                    else:
                        ext = 'jpg'  # 默认使用jpg
                    
                    cover_filename = f"cover.{ext}"
                    cover_save_path = drama_storage_path / cover_filename
                    
                    # 下载封面
                    if download_cover_image(cover_url, cover_save_path):
                        cover_count = 1
                        logger.info(f"封面图片下载成功: {cover_save_path}")
                except Exception as e:
                    logger.error(f"下载封面时出错: {e}")
                    # 封面下载失败不影响任务创建
            
            # 将剧集添加到下载队列
            task_episodes = self.db.get_task_episodes(task_id)
            for episode in episodes:
                # 通过数据库查询获取episode_id
                for ep in task_episodes:
                    if (ep['episode_num'] == episode['episode_num'] and 
                        ep['episode_url'] == episode['episode_url']):
                        self.download_manager.add_episode(ep['id'])
                        break
            
            # 显示成功消息（包含封面下载结果）
            if cover_count > 0:
                show_information(self, "任务创建成功", f"已创建任务并开始下载，封面已下载")
            else:
                show_information(self, "任务创建成功", "已创建任务并开始下载")
            
            # 切换到任务进度页面
            self.switch_page(1)
        
        except Exception as e:
            logger.error(f"保存任务时出错: {e}")
            show_critical(
                self,
                "错误",
                f"保存任务失败: {str(e)}"
            )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.download_manager:
            self.download_manager.stop()
        event.accept()

