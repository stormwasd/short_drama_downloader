"""
任务进度界面
"""
import os
import logging
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QCheckBox, QHeaderView, QMessageBox, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from ..database import Database
from ..config import config

logger = logging.getLogger(__name__)


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
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 设置整体样式
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
            QMessageBox {
                /* 弹窗使用默认样式，不继承自定义样式 */
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                gridline-color: #e0e0e0;
                font-size: 17px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 17px;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #666;
                padding: 15px 30px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
            }
            QPushButton {
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 17px;
            }
            /* 美化滚动条 */
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 16px;
                border-radius: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #bdbdbd;
                border-radius: 8px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #9e9e9e;
            }
            QScrollBar::handle:vertical:pressed {
                background-color: #757575;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #f0f0f0;
                height: 16px;
                border-radius: 8px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background-color: #bdbdbd;
                border-radius: 8px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #9e9e9e;
            }
            QScrollBar::handle:horizontal:pressed {
                background-color: #757575;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        # 设置字体
        font = QFont()
        font.setPointSize(config.TABLE_FONT_SIZE)
        self.setFont(font)
        
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
        # 设置列宽：选择列较窄，其他列自适应
        header = self.downloading_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 选择列固定宽度
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        self.downloading_table.setColumnWidth(0, 60)  # 选择列宽度设为60
        self.downloading_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.downloading_table.setFont(font)
        downloading_layout.addWidget(self.downloading_table)
        
        # 按钮区域
        delete_btn_layout = QHBoxLayout()
        delete_btn_layout.setSpacing(10)
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setFont(font)
        self.select_all_btn.setFixedWidth(100)
        self.select_all_btn.setFixedHeight(40)
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.select_all_btn.clicked.connect(lambda: self.select_all_downloading(True))
        self.select_none_btn = QPushButton("全不选")
        self.select_none_btn.setFont(font)
        self.select_none_btn.setFixedWidth(100)
        self.select_none_btn.setFixedHeight(40)
        self.select_none_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.select_none_btn.clicked.connect(lambda: self.select_all_downloading(False))
        delete_btn_layout.addWidget(self.select_all_btn)
        delete_btn_layout.addWidget(self.select_none_btn)
        delete_btn_layout.addStretch()
        self.delete_btn = QPushButton("删除选中")
        self.delete_btn.setFont(font)
        self.delete_btn.setFixedHeight(40)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
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
        self.completed_table.setColumnCount(6)
        self.completed_table.setHorizontalHeaderLabels([
            "选择", "任务名称", "剧集网址", "剧集名称", "存储路径", "完成时间"
        ])
        # 设置列宽：选择列较窄，其他列自适应
        completed_header = self.completed_table.horizontalHeader()
        completed_header.setSectionResizeMode(0, QHeaderView.Fixed)  # 选择列固定宽度
        completed_header.setSectionResizeMode(1, QHeaderView.Stretch)
        completed_header.setSectionResizeMode(2, QHeaderView.Stretch)
        completed_header.setSectionResizeMode(3, QHeaderView.Stretch)
        completed_header.setSectionResizeMode(4, QHeaderView.Stretch)
        completed_header.setSectionResizeMode(5, QHeaderView.Stretch)
        self.completed_table.setColumnWidth(0, 60)  # 选择列宽度设为60
        self.completed_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.completed_table.setFont(font)
        completed_layout.addWidget(self.completed_table)
        
        # 已完成按钮区域
        completed_btn_layout = QHBoxLayout()
        completed_btn_layout.setSpacing(10)
        self.completed_select_all_btn = QPushButton("全选")
        self.completed_select_all_btn.setFont(font)
        self.completed_select_all_btn.setFixedWidth(100)
        self.completed_select_all_btn.setFixedHeight(40)
        self.completed_select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.completed_select_all_btn.clicked.connect(lambda: self.select_all_completed(True))
        self.completed_select_none_btn = QPushButton("全不选")
        self.completed_select_none_btn.setFont(font)
        self.completed_select_none_btn.setFixedWidth(100)
        self.completed_select_none_btn.setFixedHeight(40)
        self.completed_select_none_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.completed_select_none_btn.clicked.connect(lambda: self.select_all_completed(False))
        completed_btn_layout.addWidget(self.completed_select_all_btn)
        completed_btn_layout.addWidget(self.completed_select_none_btn)
        completed_btn_layout.addStretch()
        self.completed_delete_btn = QPushButton("删除选中")
        self.completed_delete_btn.setFont(font)
        self.completed_delete_btn.setFixedHeight(40)
        self.completed_delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """)
        self.completed_delete_btn.clicked.connect(self.delete_selected_completed)
        completed_btn_layout.addWidget(self.completed_delete_btn)
        completed_layout.addLayout(completed_btn_layout)
        
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
        # 保存当前选中的episode_id
        selected_ids = set()
        for row in range(self.downloading_table.rowCount()):
            checkbox = self.downloading_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                episode_id = checkbox.property("episode_id")
                if episode_id:
                    selected_ids.add(episode_id)
        
        episodes = self.db.get_downloading_episodes()
        
        self.downloading_table.setRowCount(len(episodes))
        
        for row, episode in enumerate(episodes):
            # 选择框
            checkbox = QCheckBox()
            episode_id = episode['id']
            checkbox.setProperty("episode_id", episode_id)
            # 恢复之前选中的状态
            if episode_id in selected_ids:
                checkbox.setChecked(True)
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
        # 保存当前选中的episode_id
        selected_ids = set()
        for row in range(self.completed_table.rowCount()):
            checkbox = self.completed_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                episode_id = checkbox.property("episode_id")
                if episode_id:
                    selected_ids.add(episode_id)
        
        episodes = self.db.get_completed_episodes()
        
        self.completed_table.setRowCount(len(episodes))
        
        for row, episode in enumerate(episodes):
            # 选择框
            checkbox = QCheckBox()
            episode_id = episode['id']
            checkbox.setProperty("episode_id", episode_id)
            checkbox.setProperty("storage_path", episode.get('storage_path', '') or episode.get('task_storage_path', ''))
            # 恢复之前选中的状态
            if episode_id in selected_ids:
                checkbox.setChecked(True)
            checkbox.setEnabled(True)
            self.completed_table.setCellWidget(row, 0, checkbox)
            
            # 任务名称
            self.completed_table.setItem(row, 1, QTableWidgetItem(episode.get('task_name', '')))
            
            # 剧集网址
            self.completed_table.setItem(row, 2, QTableWidgetItem(episode.get('episode_url', '')))
            
            # 剧集名称
            self.completed_table.setItem(row, 3, QTableWidgetItem(episode.get('episode_name', '')))
            
            # 存储路径
            storage_path = episode.get('storage_path', '') or episode.get('task_storage_path', '')
            self.completed_table.setItem(row, 4, QTableWidgetItem(storage_path))
            
            # 完成时间
            updated_at = episode.get('updated_at', '')
            self.completed_table.setItem(row, 5, QTableWidgetItem(updated_at))
    
    def select_all_downloading(self, checked: bool):
        """全选/全不选下载中的剧集"""
        for row in range(self.downloading_table.rowCount()):
            checkbox = self.downloading_table.cellWidget(row, 0)
            if checkbox and checkbox.isEnabled():
                checkbox.setChecked(checked)
    
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
    
    def select_all_completed(self, checked: bool):
        """全选/全不选已完成的剧集"""
        for row in range(self.completed_table.rowCount()):
            checkbox = self.completed_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(checked)
    
    def delete_selected_completed(self):
        """删除选中的已完成剧集"""
        selected_items = []
        
        for row in range(self.completed_table.rowCount()):
            checkbox = self.completed_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                episode_id = checkbox.property("episode_id")
                storage_path = checkbox.property("storage_path")
                if episode_id:
                    selected_items.append({
                        'episode_id': episode_id,
                        'storage_path': storage_path
                    })
        
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要删除的剧集！")
            return
        
        # 询问是否删除文件
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(selected_items)} 个剧集吗？\n\n是否同时删除对应的视频文件？",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Cancel:
            return
        
        delete_files = (reply == QMessageBox.Yes)
        
        # 删除文件和记录
        episode_ids = [item['episode_id'] for item in selected_items]
        deleted_count = 0
        file_deleted_count = 0
        
        # 删除文件
        if delete_files:
            for item in selected_items:
                storage_path = item['storage_path']
                if storage_path:
                    try:
                        file_path = Path(storage_path)
                        if file_path.exists() and file_path.is_file():
                            file_path.unlink()
                            file_deleted_count += 1
                    except Exception as e:
                        logger.error(f"删除文件失败 {storage_path}: {e}")
        
        # 批量删除数据库记录
        try:
            self.db.delete_completed_episodes(episode_ids)
            deleted_count = len(episode_ids)
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            QMessageBox.critical(self, "错误", f"删除记录失败: {str(e)}")
            return
        
        self.refresh_completed()
        
        msg = f"已删除 {deleted_count} 条记录"
        if delete_files:
            msg += f"，已删除 {file_deleted_count} 个文件"
        QMessageBox.information(self, "成功", msg)

