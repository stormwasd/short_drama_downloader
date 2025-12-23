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


def cleanup_temp_files(storage_path: Path, episode_name: str):
    """
    清理下载过程中产生的临时文件（.part文件）
    
    yt-dlp在下载HLS视频时会创建临时片段文件，格式包括：
    - filename.part
    - filename.part-FragX.part
    - filename.extension.part
    - filename.extension.part-FragX.part
    
    Args:
        storage_path: 存储目录路径
        episode_name: 剧集名称（用于匹配临时文件，不包含扩展名）
    """
    try:
        if not storage_path.exists() or not storage_path.is_dir():
            return
        
        cleaned_count = 0
        for file_path in storage_path.iterdir():
            if not file_path.is_file():
                continue
            
            file_name = file_path.name
            
            # 检查是否是临时文件（包含.part）
            # 并且文件名以剧集名称开头（匹配当前下载的剧集）
            if '.part' in file_name and file_name.startswith(episode_name):
                try:
                    file_path.unlink()
                    cleaned_count += 1
                    logger.debug(f"已清理临时文件: {file_path}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败 {file_path}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"已清理 {cleaned_count} 个临时文件 (剧集: {episode_name})")
    
    except Exception as e:
        logger.warning(f"清理临时文件时出错: {e}")


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
        """添加剧集到下载队列
        
        对于 error 状态的剧集，会检查重试次数和时间间隔，确保不会立即重试
        """
        with self.lock:
            if episode_id in self.processing_episodes:
                return  # 已经在队列中或正在处理
        
        episode = self.db.get_episode_by_id(episode_id)
        if not episode:
            logger.warning(f"剧集 {episode_id} 不存在")
            return
        
        status = episode.get('status')
        
        # pending 状态的剧集直接添加
        if status == 'pending':
            with self.lock:
                if episode_id not in self.processing_episodes:
                    self.processing_episodes.add(episode_id)
                    self.download_queue.put(episode_id)
                    logger.info(f"剧集 {episode_id} 已添加到下载队列")
            return
        
        # error 状态的剧集需要检查重试次数和时间间隔
        if status == 'error':
            from datetime import datetime, timedelta
            
            episode_num = episode.get('episode_num', 'Unknown')
            retry_count = episode.get('retry_count', 0) or 0
            max_retry_count = config.MAX_RETRY_COUNT
            retry_delay_seconds = config.RETRY_DELAY_SECONDS
            
            # 检查重试次数是否超过限制
            if retry_count >= max_retry_count:
                logger.debug(
                    f"剧集 {episode_id} (Episode {episode_num}) 已达到最大重试次数 "
                    f"({retry_count}/{max_retry_count})，不再添加到队列"
                )
                return
            
            # 检查时间间隔
            updated_at = episode.get('updated_at')
            if updated_at:
                try:
                    # 解析更新时间
                    if isinstance(updated_at, str):
                        try:
                            updated_time = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                updated_time = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S.%f')
                            except ValueError:
                                logger.warning(f"无法解析剧集 {episode_id} 的更新时间格式: {updated_at}")
                                # 时间解析失败，不重试（避免立即重试）
                                return
                    else:
                        updated_time = updated_at
                    
                    # 计算时间差
                    time_diff = datetime.now() - updated_time
                    if time_diff.total_seconds() < retry_delay_seconds:
                        logger.debug(
                            f"剧集 {episode_id} (Episode {episode_num}) 失败时间过短 "
                            f"({time_diff.total_seconds():.1f} 秒 < {retry_delay_seconds} 秒)，暂不重试"
                        )
                        return
                except Exception as e:
                    logger.warning(f"检查剧集 {episode_id} 的重试时间间隔时出错: {e}，暂不重试")
                    return
            else:
                # 如果没有更新时间，不重试（避免立即重试）
                logger.debug(f"剧集 {episode_id} (Episode {episode_num}) 没有更新时间，暂不重试")
                return
            
            # 通过所有检查，可以重试
            with self.lock:
                if episode_id not in self.processing_episodes:
                    self.processing_episodes.add(episode_id)
                    self.download_queue.put(episode_id)
                    logger.info(
                        f"重试下载失败的剧集 {episode_id} (Episode {episode_num}), "
                        f"重试次数: {retry_count + 1}/{max_retry_count}"
                    )
    
    def _process_queue(self):
        """处理下载队列（定期检查新的待下载剧集）"""
        import time
        from datetime import datetime, timedelta
        
        while self.running:
            try:
                # 获取待下载的剧集（pending状态）
                pending_episodes = self.db.get_episodes_by_status('pending')
                
                for episode in pending_episodes:
                    if episode['status'] != 'deleted':
                        self.add_episode(episode['id'])
                
                # 获取失败状态的剧集（error状态），尝试添加到队列
                # 注意：add_episode 方法内部已经检查了重试次数和时间间隔，这里只需要调用即可
                error_episodes = self.db.get_episodes_by_status('error')
                
                for episode in error_episodes:
                    if episode['status'] != 'deleted':
                        # add_episode 内部会检查重试次数和时间间隔
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
            # 清理文件夹名中的非法字符和控制字符
            safe_drama_name = config.sanitize_filename(drama_name)
            # 创建剧集名称文件夹
            storage_path = base_storage_path / safe_drama_name
            storage_path.mkdir(parents=True, exist_ok=True)
            
            # 构建输出文件名
            episode_name = episode.get('episode_name', f"Episode_{episode['episode_num']}")
            # 清理文件名中的非法字符和控制字符
            safe_name = config.sanitize_filename(episode_name)
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
                        # 下载成功，重置重试次数
                        self.db.reset_episode_retry_count(ep_id)
                        self.db.update_episode_status(
                            ep_id, 'completed', 100.0, 
                            storage_path=str(actual_file)
                        )
                    else:
                        # 如果找不到文件，仍然标记为完成，但记录警告
                        # 重置重试次数（因为下载过程已完成）
                        self.db.reset_episode_retry_count(ep_id)
                        self.db.update_episode_status(
                            ep_id, 'completed', 100.0,
                            storage_path=str(storage_path / f"{safe_name}.mp4")
                        )
                elif status == 'error':
                    # 下载失败，增加重试次数
                    retry_count = self.db.increment_episode_retry_count(ep_id)
                    self.db.update_episode_status(
                        ep_id, 'error', 0.0, error_msg
                    )
                    logger.warning(
                        f"剧集 {ep_id} 下载失败，重试次数: {retry_count}/{config.MAX_RETRY_COUNT}"
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
                # 下载成功，确保重试次数已重置（progress_hook中已处理，这里作为双重保险）
                self.db.reset_episode_retry_count(episode_id)
                logger.info(f"剧集 {episode_id} 下载完成: {actual_file}")
            else:
                # 即使找不到文件，也重置重试次数（因为下载过程已完成）
                self.db.reset_episode_retry_count(episode_id)
                logger.warning(f"剧集 {episode_id} 下载完成，但无法找到文件")
            
            # 清理下载过程中产生的临时文件
            cleanup_temp_files(storage_path, safe_name)
            
            with self.lock:
                self.processing_episodes.discard(episode_id)
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"下载剧集 {episode_id} 失败: {error_msg}")
            
            # 增加重试次数
            retry_count = self.db.increment_episode_retry_count(episode_id)
            self.db.update_episode_status(episode_id, 'error', 0.0, error_msg)
            
            # 检查是否达到最大重试次数
            if retry_count >= config.MAX_RETRY_COUNT:
                logger.error(
                    f"剧集 {episode_id} (Episode {episode.get('episode_num', 'Unknown')}) "
                    f"已达到最大重试次数 ({retry_count}/{config.MAX_RETRY_COUNT})，将不再自动重试"
                )
            
            # 清理下载过程中产生的临时文件（即使下载失败也要清理）
            try:
                # 获取存储路径和文件名用于清理
                task_episodes = self.db.get_task_episodes(episode.get('task_id', 0))
                task_info = None
                for ep in task_episodes:
                    if ep['id'] == episode_id:
                        tasks = self.db.get_all_tasks()
                        for task in tasks:
                            if task['id'] == episode.get('task_id', 0):
                                task_info = task
                                break
                        break
                
                if task_info:
                    base_storage_path = Path(task_info['storage_path'])
                    drama_name = task_info.get('drama_name', 'Unknown')
                    safe_drama_name = config.sanitize_filename(drama_name)
                    storage_path = base_storage_path / safe_drama_name
                    
                    episode_name = episode.get('episode_name', f"Episode_{episode.get('episode_num', 'Unknown')}")
                    safe_name = config.sanitize_filename(episode_name)
                    
                    cleanup_temp_files(storage_path, safe_name)
            except Exception as cleanup_error:
                logger.warning(f"清理临时文件时出错: {cleanup_error}")
            
            if self.progress_callback:
                self.progress_callback(episode_id, 0.0, 'error', error_msg)
            
            with self.lock:
                self.processing_episodes.discard(episode_id)

