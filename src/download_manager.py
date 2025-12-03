"""
下载管理器，使用yt-dlp进行视频下载，支持进度跟踪和并发下载
"""
import os
import threading
import queue
import logging
from typing import Callable, Optional
from pathlib import Path
import yt_dlp
# 使用绝对导入，兼容打包后的exe
try:
    from src.database import Database
    from src.config import config
except ImportError:
    from .database import Database
    from .config import config

logger = logging.getLogger(__name__)


class DownloadProgressHook:
    """yt-dlp进度钩子"""
    
    def __init__(self, episode_id: int, progress_callback: Callable):
        self.episode_id = episode_id
        self.progress_callback = progress_callback
        self.last_progress = 0.0
    
    def __call__(self, d: dict):
        """进度回调函数"""
        if d['status'] == 'downloading':
            # 计算下载进度
            if 'total_bytes' in d:
                progress = (d.get('downloaded_bytes', 0) / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d:
                progress = (d.get('downloaded_bytes', 0) / d['total_bytes_estimate']) * 100
            else:
                progress = self.last_progress
            
            self.last_progress = progress
            if self.progress_callback:
                self.progress_callback(self.episode_id, progress, 'downloading')
        
        elif d['status'] == 'finished':
            if self.progress_callback:
                self.progress_callback(self.episode_id, 100.0, 'completed')
        
        elif d['status'] == 'error':
            error_msg = d.get('error', '未知错误')
            if self.progress_callback:
                self.progress_callback(self.episode_id, 0.0, 'error', error_msg)


class DownloadManager:
    """下载管理器"""
    
    def __init__(self, db: Database, max_concurrent: int = None, progress_callback: Optional[Callable] = None):
        self.db = db
        self.max_concurrent = max_concurrent or config.MAX_CONCURRENT_DOWNLOADS
        self.progress_callback = progress_callback
        self.download_queue = queue.Queue()
        self.workers = []
        self.running = False
        self.lock = threading.Lock()
        self.processing_episodes = set()  # 正在处理或已加入队列的episode_id
    
    def start(self):
        """启动下载管理器"""
        if self.running:
            return
        
        self.running = True
        # 启动工作线程
        for i in range(self.max_concurrent):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
        
        # 启动队列处理线程
        queue_thread = threading.Thread(target=self._process_queue, daemon=True)
        queue_thread.start()
        
        logger.info("下载管理器已启动")
    
    def stop(self):
        """停止下载管理器"""
        self.running = False
        logger.info("下载管理器已停止")
    
    def add_episode(self, episode_id: int):
        """添加剧集到下载队列"""
        with self.lock:
            if episode_id in self.processing_episodes:
                return  # 已经在队列中或正在处理
        
        episode = self.db.get_episode_by_id(episode_id)
        if not episode:
            logger.warning(f"剧集 {episode_id} 不存在")
            return
        
        if episode['status'] in ['pending', 'error']:
            with self.lock:
                if episode_id not in self.processing_episodes:
                    self.processing_episodes.add(episode_id)
                    self.download_queue.put(episode_id)
                    logger.info(f"剧集 {episode_id} 已添加到下载队列")
    
    def _process_queue(self):
        """处理下载队列（定期检查新的待下载剧集）"""
        import time
        while self.running:
            try:
                # 获取待下载的剧集
                pending_episodes = self.db.get_episodes_by_status('pending')
                
                for episode in pending_episodes:
                    if episode['status'] != 'deleted':
                        self.add_episode(episode['id'])
                
                # 等待一段时间后再次检查
                time.sleep(config.QUEUE_CHECK_INTERVAL)
            
            except Exception as e:
                logger.error(f"处理队列时出错: {e}")
                time.sleep(config.QUEUE_CHECK_INTERVAL * 2)
    
    def _worker(self):
        """工作线程，执行下载任务"""
        while self.running:
            try:
                episode_id = self.download_queue.get(timeout=config.WORKER_TIMEOUT)
                self._download_episode(episode_id)
                self.download_queue.task_done()
            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"工作线程出错: {e}")
    
    def _download_episode(self, episode_id: int):
        """下载单个剧集"""
        episode = self.db.get_episode_by_id(episode_id)
        if not episode:
            return
        
        # 检查是否已删除
        if episode['status'] == 'deleted':
            with self.lock:
                self.processing_episodes.discard(episode_id)
            return
        
        # 更新状态为下载中
        self.db.update_episode_status(episode_id, 'downloading', 0.0)
        
        try:
            # 获取任务信息以确定存储路径
            task_episodes = self.db.get_task_episodes(episode['task_id'])
            task_info = None
            for ep in task_episodes:
                if ep['id'] == episode_id:
                    # 从任务中获取存储路径
                    tasks = self.db.get_all_tasks()
                    for task in tasks:
                        if task['id'] == episode['task_id']:
                            task_info = task
                            break
                    break
            
            if not task_info:
                raise Exception("无法找到任务信息")
            
            # 在存储地址下创建以剧集名称为名的文件夹
            base_storage_path = Path(task_info['storage_path'])
            drama_name = task_info.get('drama_name', 'Unknown')
            # 清理文件夹名中的非法字符（Windows文件名不允许的字符）
            import re
            safe_drama_name = re.sub(r'[<>:"/\\|?*]', '', drama_name).strip()
            # 限制文件夹名长度
            if len(safe_drama_name) > config.FILENAME_MAX_LENGTH:
                safe_drama_name = safe_drama_name[:config.FILENAME_MAX_LENGTH]
            # 创建剧集名称文件夹
            storage_path = base_storage_path / safe_drama_name
            storage_path.mkdir(parents=True, exist_ok=True)
            
            # 构建输出文件名
            episode_name = episode.get('episode_name', f"Episode_{episode['episode_num']}")
            # 清理文件名中的非法字符（Windows文件名不允许的字符）
            safe_name = re.sub(r'[<>:"/\\|?*]', '', episode_name).strip()
            # 限制文件名长度
            if len(safe_name) > config.FILENAME_MAX_LENGTH:
                safe_name = safe_name[:config.FILENAME_MAX_LENGTH]
            # yt-dlp输出模板，使用%(ext)s让yt-dlp自动选择扩展名
            output_template = str(storage_path / f"{safe_name}.%(ext)s")
            
            # 获取下载URL
            download_url = episode.get('download_url') or episode.get('episode_url')
            if not download_url:
                raise Exception("缺少下载URL")
            
            # 创建进度钩子
            def progress_hook(ep_id, progress, status, error_msg=None):
                if status == 'completed':
                    # 获取实际下载的文件路径
                    actual_file = None
                    for ext in config.VIDEO_EXTENSIONS:
                        test_file = storage_path / f"{safe_name}.{ext}"
                        if test_file.exists():
                            actual_file = test_file
                            break
                    
                    if actual_file:
                        self.db.update_episode_status(
                            ep_id, 'completed', 100.0, 
                            storage_path=str(actual_file)
                        )
                    else:
                        # 如果找不到文件，仍然标记为完成，但记录警告
                        self.db.update_episode_status(
                            ep_id, 'completed', 100.0,
                            storage_path=str(storage_path / f"{safe_name}.mp4")
                        )
                elif status == 'error':
                    self.db.update_episode_status(
                        ep_id, 'error', 0.0, error_msg
                    )
                else:
                    self.db.update_episode_status(ep_id, 'downloading', progress)
                
                if self.progress_callback:
                    self.progress_callback(ep_id, progress, status, error_msg)
            
            hook = DownloadProgressHook(episode_id, progress_hook)
            
            # 配置yt-dlp选项
            ydl_opts = {
                'format': 'best',
                'outtmpl': output_template,
                'nocheckcertificate': True,
                'progress_hooks': [hook],
                'quiet': False,
                'no_warnings': False,
            }
            
            # 执行下载
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([download_url])
            
            # 获取实际下载的文件路径
            actual_file = None
            for ext in config.VIDEO_EXTENSIONS:
                test_file = storage_path / f"{safe_name}.{ext}"
                if test_file.exists():
                    actual_file = test_file
                    break
            
            if actual_file:
                logger.info(f"剧集 {episode_id} 下载完成: {actual_file}")
            else:
                logger.warning(f"剧集 {episode_id} 下载完成，但无法找到文件")
            
            with self.lock:
                self.processing_episodes.discard(episode_id)
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"下载剧集 {episode_id} 失败: {error_msg}")
            self.db.update_episode_status(episode_id, 'error', 0.0, error_msg)
            
            if self.progress_callback:
                self.progress_callback(episode_id, 0.0, 'error', error_msg)
            
            with self.lock:
                self.processing_episodes.discard(episode_id)

