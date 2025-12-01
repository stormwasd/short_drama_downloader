"""
数据库模型和持久化层
"""
import sqlite3
import json
import sys
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
# 使用绝对导入，兼容打包后的exe
try:
    from src.config import config
except ImportError:
    from .config import config


def get_app_data_dir():
    """获取应用程序数据目录"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe，使用exe所在目录
        return Path(sys.executable).parent
    else:
        # 开发模式，使用项目根目录
        return Path(__file__).parent.parent


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 使用应用程序数据目录
            app_dir = get_app_data_dir()
            self.db_path = str(app_dir / config.DATABASE_NAME)
        else:
            self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                source TEXT NOT NULL,
                drama_name TEXT NOT NULL,
                drama_url TEXT NOT NULL,
                start_episode INTEGER DEFAULT 0,
                end_episode INTEGER DEFAULT 0,
                storage_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 剧集表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                episode_num INTEGER NOT NULL,
                episode_name TEXT,
                episode_url TEXT NOT NULL,
                download_url TEXT,
                storage_path TEXT,
                status TEXT DEFAULT 'pending',
                progress REAL DEFAULT 0.0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (id),
                UNIQUE(task_id, episode_num)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def task_name_exists(self, task_name: str) -> bool:
        """检查任务名称是否已存在"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE task_name = ?", (task_name,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def create_task(self, task_name: str, source: str, drama_name: str, 
                   drama_url: str, start_episode: int, end_episode: int, 
                   storage_path: str) -> int:
        """创建新任务"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks (task_name, source, drama_name, drama_url, 
                             start_episode, end_episode, storage_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (task_name, source, drama_name, drama_url, 
              start_episode, end_episode, storage_path))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def add_episodes(self, task_id: int, episodes: List[Dict]):
        """批量添加剧集"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for episode in episodes:
            cursor.execute("""
                INSERT OR REPLACE INTO episodes 
                (task_id, episode_num, episode_name, episode_url, download_url, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (task_id, episode['episode_num'], episode.get('episode_name', ''),
                  episode['episode_url'], episode.get('download_url', '')))
        
        conn.commit()
        conn.close()
    
    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tasks
    
    def get_task_episodes(self, task_id: int, status: Optional[str] = None) -> List[Dict]:
        """获取任务的剧集列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM episodes 
                WHERE task_id = ? AND status = ?
                ORDER BY episode_num
            """, (task_id, status))
        else:
            cursor.execute("""
                SELECT * FROM episodes 
                WHERE task_id = ?
                ORDER BY episode_num
            """, (task_id,))
        
        episodes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return episodes
    
    def get_downloading_episodes(self) -> List[Dict]:
        """获取所有下载中的剧集"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.*, t.task_name, t.storage_path as task_storage_path
            FROM episodes e
            JOIN tasks t ON e.task_id = t.id
            WHERE e.status IN ('pending', 'downloading')
            ORDER BY e.created_at
        """)
        
        episodes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return episodes
    
    def get_completed_episodes(self) -> List[Dict]:
        """获取所有已完成的剧集"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.*, t.task_name, t.storage_path as task_storage_path
            FROM episodes e
            JOIN tasks t ON e.task_id = t.id
            WHERE e.status = 'completed'
            ORDER BY e.updated_at DESC
        """)
        
        episodes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return episodes
    
    def update_episode_status(self, episode_id: int, status: str, 
                             progress: float = 0.0, error_message: str = None,
                             storage_path: str = None):
        """更新剧集状态"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE episodes 
            SET status = ?, progress = ?, error_message = ?, 
                storage_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, progress, error_message, storage_path, episode_id))
        
        conn.commit()
        conn.close()
    
    def delete_episodes(self, episode_ids: List[int]):
        """删除剧集（标记为删除，不实际删除记录）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(episode_ids))
        cursor.execute(f"""
            UPDATE episodes 
            SET status = 'deleted', updated_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
        """, episode_ids)
        
        conn.commit()
        conn.close()
    
    def delete_completed_episodes(self, episode_ids: List[int]):
        """删除已完成的剧集记录（从数据库中物理删除）"""
        if not episode_ids:
            return
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(episode_ids))
        cursor.execute(f"""
            DELETE FROM episodes 
            WHERE id IN ({placeholders}) AND status = 'completed'
        """, episode_ids)
        
        conn.commit()
        conn.close()
    
    def get_episode_by_id(self, episode_id: int) -> Optional[Dict]:
        """根据ID获取剧集"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_episodes_by_status(self, status: str) -> List[Dict]:
        """根据状态获取剧集"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM episodes 
            WHERE status = ?
            ORDER BY created_at
        """, (status,))
        
        episodes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return episodes

