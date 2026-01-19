import os
from logger import get_logger
import threading
from multi_source_file_copy import on_backup
from typing import Dict, List, Any
from database import Database
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QFileDialog, QMessageBox, QLineEdit
)

# 初始化日志
logger = get_logger(__name__)


class BackupManager:
    """备份业务逻辑管理器（处理数据库、备份核心操作）"""

    def __init__(self):
        # 初始化数据库
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "backup.db")
        logger.info(f"数据库路径: {db_path}")
        self.db = Database(db_path)

    def add_backup_path(self, file_path: str):
        """新增备份路径到数据库"""
        if not file_path or not file_path.strip():
            logger.error("未选择有效文件/文件夹路径")
            return False
        clean_path = file_path.strip()
        self.db.insert('backup_items', {'file_path': clean_path})
        logger.info(f"新增备份路径: {clean_path}")
        return True

    def delete_backup_path(self, selected_path: str):
        """删除指定的备份路径"""
        if not selected_path:
            logger.error("未选择要删除的路径")
            return False
        self.db.delete('backup_items', 'file_path=?', (selected_path,))
        logger.info(f"删除备份路径: {selected_path}")
        return True

    def edit_backup_path(self, old_path: str, new_path: str):
        """编辑备份路径"""
        if not old_path or not new_path:
            logger.error("原路径或新路径为空")
            return False
        self.db.update(
            'backup_items',
            data={'file_path': new_path.strip()},
            where_clause='file_path=?',
            where_params=(old_path,)
        )
        logger.info(f"备份路径修改: {old_path} -> {new_path.strip()}")
        return True

    def save_output_path(self, output_path: str):
        """保存备份输出路径到配置"""
        if not output_path or not output_path.strip():
            logger.error("输出路径为空")
            return False
        clean_path = output_path.strip().replace('\\', '/').replace('//', '/')
        sql = "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)"
        self.db.execute(sql, ("output_path", clean_path))
        logger.info(f"保存备份输出路径: {clean_path}")
        return True

    def get_output_path(self):
        """获取当前备份输出路径"""
        result = self.db.select_one('settings', 'value', 'key="output_path"')
        output_value = result['value'] if result else None
        # 转为字符串类型
        return str(Path(output_value)) if output_value else "未设置"

    def get_all_backup_items(self):
        """获取所有备份路径列表"""
        items = self.db.select('backup_items', 'file_path')
        backup_list = []
        if items:
            for item in items:
                # 同样使用键名索引或数字索引获取 file_path
                file_path = item['file_path']  # 推荐：键名索引
                # file_path = item[0]  # 备选：数字索引
                if file_path:
                    backup_list.append(str(Path(file_path)))

        return backup_list


class BackupWidget(QWidget):
    """备份功能UI组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.backup_status = {}
        self.backup_manager = BackupManager()
        self.backup_output_label = QLineEdit()
        self.backup_output_label.setPlaceholderText("未选择输出路径，点击右侧按钮选择")
        self.backup_output_label.setReadOnly(True)
        self.backup_list_widget = QListWidget()
        self.init_ui()
        self.refresh_ui()  # 初始化UI数据

    def init_ui(self):
        """构建备份UI布局"""
        fl = QFormLayout(self)
        fl.addRow(QLabel("备份文件管理"))

        # 按钮布局
        h_layout = QHBoxLayout()
        self.add_btn = QPushButton("新增备份路径")
        self.del_btn = QPushButton("删除备份路径")
        self.edit_btn = QPushButton("编辑备份路径")
        self.backup_btn = QPushButton("备份")
        self.select_output_btn = QPushButton("选择输出路径")

        # 绑定按钮事件
        self.add_btn.clicked.connect(self.on_add_backup_path)
        self.del_btn.clicked.connect(self.on_del_backup_path)
        self.edit_btn.clicked.connect(self.on_edit_backup_path)
        self.backup_btn.clicked.connect(self.on_backup)
        self.select_output_btn.clicked.connect(self.on_select_output_path)

        # 添加按钮到布局
        h_layout.addWidget(self.add_btn)
        h_layout.addWidget(self.del_btn)
        h_layout.addWidget(self.edit_btn)
        h_layout.addWidget(self.backup_btn)
        # h_layout.addWidget(self.select_output_btn)

        # 组装UI
        fl.addRow(h_layout)
        output_file_operate_layout = QHBoxLayout()
        output_file_operate_layout.addWidget(self.backup_output_label)  # 路径框占主要宽度
        output_file_operate_layout.addWidget(self.select_output_btn)  # 按钮紧跟右侧
        # 可选：设置布局间距，优化美观度
        output_file_operate_layout.setSpacing(10)
        fl.addRow("当前输出路径:", output_file_operate_layout)
        fl.addRow("备份文件列表:",self.backup_list_widget)

    def refresh_ui(self):
        """刷新备份列表和输出路径显示"""
        # 刷新输出路径
        output_path = self.backup_manager.get_output_path()
        self.backup_output_label.setPlaceholderText(f"{output_path}")
        # 刷新备份列表
        self.backup_list_widget.clear()
        backup_items = self.backup_manager.get_all_backup_items()
        self.backup_list_widget.addItems(backup_items)

    def on_add_backup_path(self):
        """新增备份路径按钮事件"""
        path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if self.backup_manager.add_backup_path(path):
            self.refresh_ui()

    def on_del_backup_path(self):
        """删除备份路径按钮事件"""
        selected_items = self.backup_list_widget.selectedItems()
        if not selected_items:
            logger.error("未选中要删除的备份路径")
            return
        selected_path = selected_items[0].text()
        if self.backup_manager.delete_backup_path(selected_path):
            self.refresh_ui()

    def on_edit_backup_path(self):
        """编辑备份路径按钮事件"""
        selected_items = self.backup_list_widget.selectedItems()
        if not selected_items:
            logger.error("未选中要编辑的备份路径")
            return
        old_path = selected_items[0].text()
        new_path, _ = QFileDialog.getOpenFileName(self, "选择新的文件/文件夹", old_path)
        if self.backup_manager.edit_backup_path(old_path, new_path):
            self.refresh_ui()

    def on_select_output_path(self):
        """选择备份输出路径按钮事件"""
        path = QFileDialog.getExistingDirectory(self, "选择备份输出文件夹")
        if self.backup_manager.save_output_path(path):
            self.refresh_ui()

    def on_backup(self):
        """执行备份操作（可扩展具体备份逻辑）"""
        backup_items = self.backup_manager.get_all_backup_items()
        output_path = self.backup_manager.get_output_path()
        self.start_backup_async(backup_items, output_path)

    def start_backup_async(self, backup_items: List[str], output_path: str) -> Dict[str, Any]:
        """异步开始备份操作"""
        try:
            # 验证数据
            validation = self.validate_backup_data(backup_items, output_path)
            if not validation["valid"]:
                self.show_backup_result_popup({"success": False, "message": validation["error"]})

            # 检查是否已有备份任务在运行
            if self.backup_status["running"]:
                self.show_backup_result_popup({"success": False, "message": "已有备份任务正在执行"})

            # 设置备份状态为运行中
            self.backup_status["running"] = True
            self.backup_status["result"] = None

            # 创建并启动后台线程执行备份
            def backup_worker():
                try:
                    logger.info("开始异步备份操作...")
                    on_backup(backup_items, output_path)
                    self.backup_status["result"] = {"success": True, "message": "备份操作完成"}
                    logger.info("异步备份操作完成")
                except Exception as e:
                    self.backup_status["result"] = {"success": False, "message": str(e)}
                    logger.error(f"异步备份失败: {e}")
                finally:
                    self.backup_status["running"] = False

            # 启动后台线程
            backup_thread = threading.Thread(target=backup_worker, daemon=True)
            backup_thread.start()
            logger.info("异步备份任务已启动，正在后台执行...")
            # return {"success": True, "message": "备份任务已启动，正在后台执行..."}
        except Exception as e:
            self.backup_status["running"] = False
            logger.error(f"异步备份失败: {e}")
            # return {"success": False, "error": str(e)}

    def show_backup_result_popup(self, backup_result):
        """弹窗展示备份结果"""
        # 创建弹窗
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("备份结果")

        # 根据备份状态设置弹窗图标和内容
        if backup_result["success"]:
            msg_box.setIcon(QMessageBox.Information)  # 信息图标（成功）
            msg_box.setText(backup_result["message"])
        else:
            msg_box.setIcon(QMessageBox.Warning)  # 警告图标（失败/部分失败）
            # 拼接详细信息（包含失败列表）
            detail_msg = backup_result["message"]
            msg_box.setText(detail_msg)

        # 显示弹窗
        msg_box.exec()

    def validate_backup_data(self, backup_items: List[str], output_path: str) -> Dict[str, Any]:
        """验证备份数据"""
        if not backup_items:
            return {"valid": False, "error": "没有可备份的目录"}

        if not output_path or output_path == "未设置":
            return {"valid": False, "error": "请先选择输出目录"}

        # 检查路径是否存在
        for item in backup_items:
            if not os.path.exists(item):
                return {"valid": False, "error": f"备份目录不存在: {item}"}

        # 检查输出目录是否存在，不存在则创建
        if not os.path.exists(output_path):
            try:
                os.makedirs(output_path, exist_ok=True)
            except Exception as e:
                return {"valid": False, "error": f"无法创建输出目录: {str(e)}"}

        return {"valid": True}