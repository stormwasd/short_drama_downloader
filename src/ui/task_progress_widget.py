"""
任务进度界面
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QCheckBox, QHeaderView, QMessageBox, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor
from ..database import Database
from ..config import config


class TaskProgressWidget(QWidget):
    """任务进度界面"""
    
    refresh_requested = pyqtSignal()  # 刷新请求信号
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.setup_refresh_timer()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标签页
        self.tab_widget = QTabWidget()
        
        # 下载中标签页
        self.downloading_tab = QWidget()
        downloading_layout = QVBoxLayout()
        downloading_layout.setContentsMargins(0, 0, 0, 0)
        
        # 下载中表格
        self.downloading_table = QTableWidget()
        self.downloading_table.setColumnCount(7)
        self.downloading_table.setHorizontalHeaderLabels([
            "选择", "任务名称", "剧集网址", "剧集名称", "下载进度", "存储路径", "操作"
        ])
        self.downloading_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.downloading_table.setSelectionBehavior(QTableWidget.SelectRows)
        downloading_layout.addWidget(self.downloading_table)
        
        # 删除按钮
        delete_btn_layout = QHBoxLayout()
        delete_btn_layout.addStretch()
        self.delete_btn = QPushButton("删除选中")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_selected_episodes)
        delete_btn_layout.addWidget(self.delete_btn)
        downloading_layout.addLayout(delete_btn_layout)
        
        self.downloading_tab.setLayout(downloading_layout)
        self.tab_widget.addTab(self.downloading_tab, "下载中")
        
        # 已完成标签页
        self.completed_tab = QWidget()
        completed_layout = QVBoxLayout()
        completed_layout.setContentsMargins(0, 0, 0, 0)
        
        # 已完成表格
        self.completed_table = QTableWidget()
        self.completed_table.setColumnCount(5)
        self.completed_table.setHorizontalHeaderLabels([
            "任务名称", "剧集网址", "剧集名称", "存储路径", "完成时间"
        ])
        self.completed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.completed_table.setSelectionBehavior(QTableWidget.SelectRows)
        completed_layout.addWidget(self.completed_table)
        
        self.completed_tab.setLayout(completed_layout)
        self.tab_widget.addTab(self.completed_tab, "已完成")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def setup_refresh_timer(self):
        """设置刷新定时器"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(config.UI_REFRESH_INTERVAL)
    
    def refresh_data(self):
        """刷新数据"""
        self.refresh_downloading()
        self.refresh_completed()
    
    def refresh_downloading(self):
        """刷新下载中列表"""
        episodes = self.db.get_downloading_episodes()
        
        self.downloading_table.setRowCount(len(episodes))
        
        for row, episode in enumerate(episodes):
            # 选择框
            checkbox = QCheckBox()
            checkbox.setProperty("episode_id", episode['id'])
            # 只有pending状态的可以删除
            if episode['status'] == 'pending':
                checkbox.setEnabled(True)
            else:
                checkbox.setEnabled(False)
            self.downloading_table.setCellWidget(row, 0, checkbox)
            
            # 任务名称
            self.downloading_table.setItem(row, 1, QTableWidgetItem(episode.get('task_name', '')))
            
            # 剧集网址
            self.downloading_table.setItem(row, 2, QTableWidgetItem(episode.get('episode_url', '')))
            
            # 剧集名称
            self.downloading_table.setItem(row, 3, QTableWidgetItem(episode.get('episode_name', '')))
            
            # 下载进度
            progress = episode.get('progress', 0.0)
            status = episode.get('status', 'pending')
            if status == 'downloading':
                progress_text = f"{progress:.1f}%"
                progress_item = QTableWidgetItem(progress_text)
                # 根据进度设置颜色
                if progress < 30:
                    progress_item.setForeground(QColor(255, 0, 0))
                elif progress < 70:
                    progress_item.setForeground(QColor(255, 165, 0))
                else:
                    progress_item.setForeground(QColor(0, 128, 0))
            elif status == 'error':
                progress_item = QTableWidgetItem("错误")
                progress_item.setForeground(QColor(255, 0, 0))
            else:
                progress_item = QTableWidgetItem("等待中")
                progress_item.setForeground(QColor(128, 128, 128))
            self.downloading_table.setItem(row, 4, progress_item)
            
            # 存储路径
            storage_path = episode.get('task_storage_path', '') or episode.get('storage_path', '')
            self.downloading_table.setItem(row, 5, QTableWidgetItem(storage_path))
            
            # 操作
            status_text = {
                'pending': '等待中',
                'downloading': '下载中',
                'error': '错误',
                'deleted': '已删除'
            }.get(status, status)
            self.downloading_table.setItem(row, 6, QTableWidgetItem(status_text))
    
    def refresh_completed(self):
        """刷新已完成列表"""
        episodes = self.db.get_completed_episodes()
        
        self.completed_table.setRowCount(len(episodes))
        
        for row, episode in enumerate(episodes):
            # 任务名称
            self.completed_table.setItem(row, 0, QTableWidgetItem(episode.get('task_name', '')))
            
            # 剧集网址
            self.completed_table.setItem(row, 1, QTableWidgetItem(episode.get('episode_url', '')))
            
            # 剧集名称
            self.completed_table.setItem(row, 2, QTableWidgetItem(episode.get('episode_name', '')))
            
            # 存储路径
            storage_path = episode.get('storage_path', '') or episode.get('task_storage_path', '')
            self.completed_table.setItem(row, 3, QTableWidgetItem(storage_path))
            
            # 完成时间
            updated_at = episode.get('updated_at', '')
            self.completed_table.setItem(row, 4, QTableWidgetItem(updated_at))
    
    def delete_selected_episodes(self):
        """删除选中的剧集"""
        selected_ids = []
        
        for row in range(self.downloading_table.rowCount()):
            checkbox = self.downloading_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked() and checkbox.isEnabled():
                episode_id = checkbox.property("episode_id")
                if episode_id:
                    selected_ids.append(episode_id)
        
        if not selected_ids:
            QMessageBox.information(self, "提示", "请先选择要删除的剧集！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(selected_ids)} 个剧集吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_episodes(selected_ids)
            self.refresh_downloading()
            QMessageBox.information(self, "成功", "已删除选中的剧集！")

