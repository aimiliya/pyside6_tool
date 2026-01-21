import os

from pathlib import Path
from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QPushButton, QComboBox, QLineEdit, QHBoxLayout, QFileDialog, \
    QMessageBox
from database import Database
from logger import get_logger
from excel_to_entity import excel_to_entity_main

# 初始化日志
logger = get_logger(__name__)

class ExcelToEntityWidget(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("未选择文件，点击右侧按钮选择")
        self.input_edit.setReadOnly(True)  # 推荐设置为只读，仅通过按钮更新

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("未选择文件，点击右侧按钮选择")
        self.output_edit.setReadOnly(True)  # 推荐设置为只读，仅通过按钮更新
        self.chunk_size_edit = QLineEdit()

        self.index_edit = QLineEdit()

        self.init_ui()
        self.refresh_ui()
        
    def init_ui(self):
        fl = QFormLayout(self)
        fl.addRow(QLabel("Excel转实体工具"))
        select_file = QPushButton("选择文件")
        select_dir = QPushButton("选择目录")

        # 绑定方法
        select_file.clicked.connect(self.on_select_file)
        select_dir.clicked.connect(self.on_select_dir)

        # 封装「路径框 + 选择按钮」为水平布局（核心：将两个控件横向排列）
        input_file_operate_layout = QHBoxLayout()
        input_file_operate_layout.addWidget(self.input_edit)  # 路径框占主要宽度
        input_file_operate_layout.addWidget(select_file)  # 按钮紧跟右侧
        # 可选：设置布局间距，优化美观度
        input_file_operate_layout.setSpacing(10)

        output_file_operate_layout = QHBoxLayout()
        output_file_operate_layout.addWidget(self.output_edit)  # 路径框占主要宽度
        output_file_operate_layout.addWidget(select_dir)  # 按钮紧跟右侧
        # 可选：设置布局间距，优化美观度
        output_file_operate_layout.setSpacing(10)

        fl.addRow("请选择要转换的文件",input_file_operate_layout)
        fl.addRow("请选择输出路径",output_file_operate_layout)
        fl.addRow("起始工作表序号",self.index_edit)

        start_but = QPushButton("开始转换")
        start_but.clicked.connect(self.on_start)


    def refresh_ui(self):
        self.input_edit.setPlaceholderText(self.get_path("excel_input"))
        self.output_edit.setPlaceholderText(self.get_path("excel_output"))

    def on_select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if self.add_path(path, "excel_input"):
            self.refresh_ui()

    def on_select_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择备份输出文件夹")
        if self.add_path(path, "excel_output"):
            self.refresh_ui()

    # 用于保存路径
    def add_path(self, file_path: str, path_type):
        """新增备份路径到数据库"""
        if not file_path or not file_path.strip():
            logger.error("未选择有效文件/文件夹路径")
            return False
        clean_path = file_path.strip()
        sql = "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)"
        self.db.execute(sql, (f"split_{path_type}", clean_path))
        logger.info(f"新增备份路径: {clean_path}")
        return True

    # 应用获取路径
    def get_path(self, path_type: str):
        where_clause = f"key='split_{path_type}'"
        result = self.db.select_one('settings', 'value', where_clause)
        output_value = result['value'] if result else None
        # 转为字符串类型
        return str(Path(output_value)) if output_value else "未选择文件，点击右侧按钮选择"

    def on_start(self):
        excel_path = self.get_path("excel_input")
        entity_path = self.get_path("excel_output")

        if not excel_path:
            QMessageBox.warning(self, "警告", "请先选择Excel文件")
            return
        if not entity_path:
            QMessageBox.warning(self, "警告", "请先选择输出路径")
        try:
            index = int(self.index_edit.text())  # 转换为整数（如需字节单位可后续扩展）
            if index <= 0:
                QMessageBox.critical(self, "参数错误", "起始工作表序号必须大于0")
                return
        except ValueError:
            QMessageBox.critical(self, "参数错误", "起始工作表序号必须是有效的正整数")
            return
        excel_to_entity_main(excel_path, entity_path, index)
