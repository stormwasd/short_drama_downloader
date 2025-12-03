"""
配置文件 - 统一管理所有配置项
"""
from typing import Dict, Any


class Config:
    """配置类"""
    
    # ========== 下载配置 ==========
    # 最大并发下载数
    MAX_CONCURRENT_DOWNLOADS: int = 5
    
    # 队列检查间隔（秒）
    QUEUE_CHECK_INTERVAL: int = 5
    
    # 工作线程超时（秒）
    WORKER_TIMEOUT: int = 1
    
    # ========== API配置 ==========
    # API请求超时时间（秒）
    API_TIMEOUT: int = 30
    
    # ========== UI配置 ==========
    # 界面刷新间隔（毫秒）
    UI_REFRESH_INTERVAL: int = 2000
    
    # 窗口配置
    WINDOW_X: int = 100
    WINDOW_Y: int = 100
    WINDOW_WIDTH: int = 1200
    WINDOW_HEIGHT: int = 800
    
    # 字体配置（调整为舒适的大小）
    FONT_SIZE: int = 22  # 基础字体大小
    LABEL_FONT_SIZE: int = 22  # 标签字体大小
    INPUT_FONT_SIZE: int = 20  # 输入框字体大小
    TABLE_FONT_SIZE: int = 18  # 表格字体大小
    
    # ========== 剧集配置 ==========
    # 剧集最大数量
    EPISODE_MAX: int = 200
    
    # 文件名最大长度
    FILENAME_MAX_LENGTH: int = 200
    
    # ========== 文件扩展名配置 ==========
    # 支持的视频文件扩展名
    VIDEO_EXTENSIONS: list = ['mp4', 'mkv', 'webm', 'flv', 'm4a', 'mp3']
    
    # ========== 数据库配置 ==========
    # 数据库文件名
    DATABASE_NAME: str = "short_drama.db"
    
    # ========== 日志配置 ==========
    # 日志级别
    LOG_LEVEL: str = "INFO"
    
    # 日志格式
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # ========== 版本配置 ==========
    # 版本号
    VERSION: str = "1.0"
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有配置项"""
        return {
            'MAX_CONCURRENT_DOWNLOADS': cls.MAX_CONCURRENT_DOWNLOADS,
            'QUEUE_CHECK_INTERVAL': cls.QUEUE_CHECK_INTERVAL,
            'WORKER_TIMEOUT': cls.WORKER_TIMEOUT,
            'API_TIMEOUT': cls.API_TIMEOUT,
            'UI_REFRESH_INTERVAL': cls.UI_REFRESH_INTERVAL,
            'WINDOW_X': cls.WINDOW_X,
            'WINDOW_Y': cls.WINDOW_Y,
            'WINDOW_WIDTH': cls.WINDOW_WIDTH,
            'WINDOW_HEIGHT': cls.WINDOW_HEIGHT,
            'EPISODE_MAX': cls.EPISODE_MAX,
            'FILENAME_MAX_LENGTH': cls.FILENAME_MAX_LENGTH,
            'VIDEO_EXTENSIONS': cls.VIDEO_EXTENSIONS,
            'DATABASE_NAME': cls.DATABASE_NAME,
            'LOG_LEVEL': cls.LOG_LEVEL,
            'LOG_FORMAT': cls.LOG_FORMAT,
            'FONT_SIZE': cls.FONT_SIZE,
            'LABEL_FONT_SIZE': cls.LABEL_FONT_SIZE,
            'INPUT_FONT_SIZE': cls.INPUT_FONT_SIZE,
            'TABLE_FONT_SIZE': cls.TABLE_FONT_SIZE,
            'VERSION': cls.VERSION,
        }
    
    @classmethod
    def validate(cls) -> bool:
        """验证配置项的有效性"""
        if cls.MAX_CONCURRENT_DOWNLOADS < 1:
            raise ValueError("MAX_CONCURRENT_DOWNLOADS 必须大于0")
        if cls.API_TIMEOUT < 1:
            raise ValueError("API_TIMEOUT 必须大于0")
        if cls.UI_REFRESH_INTERVAL < 100:
            raise ValueError("UI_REFRESH_INTERVAL 必须大于等于100毫秒")
        if cls.EPISODE_MAX < 1:
            raise ValueError("EPISODE_MAX 必须大于0")
        if cls.FILENAME_MAX_LENGTH < 1:
            raise ValueError("FILENAME_MAX_LENGTH 必须大于0")
        return True


# 创建全局配置实例
config = Config()

