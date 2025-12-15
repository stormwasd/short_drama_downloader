"""
单实例管理器 - 确保应用程序只有一个实例运行
"""
import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SingleInstance:
    """单实例管理器
    
    使用命名互斥锁（Windows）或文件锁（Unix）来确保应用程序只有一个实例运行。
    如果检测到已有实例运行，会尝试激活已存在的窗口。
    """
    
    def __init__(self, app_id: str = None):
        """
        初始化单实例管理器
        
        Args:
            app_id: 应用程序唯一标识符，用于创建互斥锁/文件锁
                   如果为None，则使用应用程序名称
        """
        if app_id is None:
            # 使用应用程序名称作为默认ID
            app_id = "ShortDramaDownloader_SingleInstance"
        
        self.app_id = app_id
        self.mutex = None
        self.is_running = False
        
        # 根据平台选择实现
        if sys.platform == 'win32':
            self._init_windows()
        else:
            self._init_unix()
    
    def _init_windows(self):
        """Windows平台初始化 - 使用命名互斥锁"""
        try:
            import win32event
            import win32api
            import winerror
            
            # 创建命名互斥锁（初始拥有，这样我们才能正确释放）
            self.mutex = win32event.CreateMutex(
                None,  # 默认安全属性
                True,  # 初始拥有互斥锁
                self.app_id  # 互斥锁名称
            )
            
            # 检查是否已有实例运行
            last_error = win32api.GetLastError()
            if last_error == winerror.ERROR_ALREADY_EXISTS:
                # 互斥锁已存在，说明已有实例运行
                # 注意：即使互斥锁已存在，CreateMutex仍然会返回句柄，但我们不是拥有者
                self.is_running = True
                logger.info("检测到已有实例运行")
                # 释放当前互斥锁句柄（因为我们不是拥有者）
                win32api.CloseHandle(self.mutex)
                self.mutex = None
            else:
                # 成功创建互斥锁，这是第一个实例
                # 我们拥有互斥锁，可以在退出时释放
                self.is_running = False
                logger.info("这是第一个实例")
                
        except ImportError:
            # 如果没有安装pywin32，使用备用方案
            logger.warning("未安装pywin32，使用备用单实例检测方案")
            self._init_windows_fallback()
        except Exception as e:
            logger.error(f"初始化Windows单实例管理器失败: {e}")
            # 失败时允许运行（降级处理）
            self.is_running = False
            self.mutex = None
    
    def _init_windows_fallback(self):
        """Windows平台备用方案 - 使用文件锁"""
        try:
            import tempfile
            import os
            from pathlib import Path
            
            # 创建临时文件路径
            temp_dir = Path(tempfile.gettempdir())
            lock_file = temp_dir / f"{self.app_id}.lock"
            
            # 尝试创建锁文件（独占模式）
            try:
                # 在Windows上，使用独占模式打开文件
                self.lock_file_handle = open(lock_file, 'x')
                self.is_running = False
                logger.info("这是第一个实例（文件锁方式）")
            except FileExistsError:
                # 文件已存在，说明已有实例运行
                self.is_running = True
                logger.info("检测到已有实例运行（文件锁方式）")
                self.lock_file_handle = None
            except Exception as e:
                logger.error(f"创建文件锁失败: {e}")
                self.is_running = False
                self.lock_file_handle = None
                
        except Exception as e:
            logger.error(f"初始化Windows备用方案失败: {e}")
            self.is_running = False
            self.lock_file_handle = None
    
    def _init_unix(self):
        """Unix平台初始化 - 使用文件锁"""
        try:
            import fcntl
            import tempfile
            from pathlib import Path
            
            # 创建临时文件路径
            temp_dir = Path(tempfile.gettempdir())
            lock_file = temp_dir / f"{self.app_id}.lock"
            
            # 尝试创建并锁定文件
            try:
                self.lock_file_handle = open(lock_file, 'w')
                # 尝试获取独占锁（非阻塞）
                fcntl.flock(self.lock_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.is_running = False
                logger.info("这是第一个实例（Unix文件锁）")
            except (IOError, OSError):
                # 无法获取锁，说明已有实例运行
                self.is_running = True
                logger.info("检测到已有实例运行（Unix文件锁）")
                if hasattr(self, 'lock_file_handle'):
                    self.lock_file_handle.close()
                self.lock_file_handle = None
                
        except Exception as e:
            logger.error(f"初始化Unix单实例管理器失败: {e}")
            self.is_running = False
            self.lock_file_handle = None
    
    def activate_existing_window(self, window_title: str = None, max_retries: int = 5, retry_delay: float = 0.2) -> bool:
        """
        激活已存在的窗口
        
        Args:
            window_title: 窗口标题（部分匹配即可）
                         如果为None，则使用默认标题
            max_retries: 最大重试次数（窗口可能还未创建完成）
            retry_delay: 重试延迟（秒）
            
        Returns:
            是否成功激活窗口
        """
        if not self.is_running:
            return False
        
        if sys.platform != 'win32':
            # Unix平台暂不支持窗口激活
            logger.warning("Unix平台不支持窗口激活")
            return False
        
        try:
            import win32gui
            import win32con
            import time
            
            if window_title is None:
                window_title = "Dramaseek"
            
            # 查找窗口（带重试机制，因为窗口可能还未创建完成）
            for attempt in range(max_retries):
                def enum_windows_callback(hwnd, windows):
                    """枚举窗口回调"""
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if window_title in title:
                            windows.append((hwnd, title))
                    return True
                
                windows = []
                win32gui.EnumWindows(enum_windows_callback, windows)
                
                if windows:
                    # 找到窗口，激活它
                    hwnd, title = windows[0]
                    logger.info(f"找到已存在的窗口: {title}")
                    
                    # 如果窗口最小化，先恢复
                    if win32gui.IsIconic(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    
                    # 激活窗口（置顶）
                    try:
                        win32gui.SetForegroundWindow(hwnd)
                        win32gui.BringWindowToTop(hwnd)
                        logger.info("成功激活已存在的窗口")
                        return True
                    except Exception as e:
                        # SetForegroundWindow可能失败（Windows安全限制）
                        # 尝试使用其他方法
                        logger.debug(f"SetForegroundWindow失败: {e}，尝试其他方法")
                        try:
                            # 使用ShowWindow和BringWindowToTop的组合
                            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                            win32gui.BringWindowToTop(hwnd)
                            logger.info("使用备用方法激活窗口")
                            return True
                        except Exception as e2:
                            logger.warning(f"激活窗口失败: {e2}")
                            return False
                
                # 如果未找到窗口且还有重试机会，等待后重试
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            
            logger.warning(f"未找到已存在的窗口（已重试{max_retries}次）")
            return False
                
        except ImportError:
            logger.warning("未安装pywin32，无法激活已存在的窗口")
            return False
        except Exception as e:
            logger.error(f"激活已存在窗口失败: {e}")
            return False
    
    def release(self):
        """释放资源"""
        if sys.platform == 'win32':
            if self.mutex:
                try:
                    import win32api
                    win32api.CloseHandle(self.mutex)
                    logger.info("释放Windows互斥锁")
                except Exception as e:
                    logger.error(f"释放互斥锁失败: {e}")
            elif hasattr(self, 'lock_file_handle') and self.lock_file_handle:
                # Windows文件锁方式
                try:
                    self.lock_file_handle.close()
                    # 尝试删除锁文件
                    try:
                        import tempfile
                        from pathlib import Path
                        temp_dir = Path(tempfile.gettempdir())
                        lock_file = temp_dir / f"{self.app_id}.lock"
                        if lock_file.exists():
                            lock_file.unlink()
                    except Exception:
                        pass  # 忽略删除失败
                    logger.info("释放Windows文件锁")
                except Exception as e:
                    logger.error(f"释放文件锁失败: {e}")
        else:
            if hasattr(self, 'lock_file_handle') and self.lock_file_handle:
                try:
                    import fcntl
                    fcntl.flock(self.lock_file_handle.fileno(), fcntl.LOCK_UN)
                    self.lock_file_handle.close()
                    logger.info("释放文件锁")
                except Exception as e:
                    logger.error(f"释放文件锁失败: {e}")

