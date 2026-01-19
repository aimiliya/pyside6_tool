import os

from pathlib import Path
from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QPushButton, QComboBox, QLineEdit, QHBoxLayout, QFileDialog, \
    QMessageBox
from database import Database
from logger import get_logger
from file_splitter import FileSplitter

# 初始化日志
logger = get_logger(__name__)

## 文件分割窗口模块
class SplitFileWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 初始化数据库
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "backup.db")
        logger.info(f"数据库路径: {db_path}")
        self.db = Database(db_path)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("未选择文件，点击右侧按钮选择")
        self.input_edit.setReadOnly(True)  # 推荐设置为只读，仅通过按钮更新

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("未选择文件，点击右侧按钮选择")
        self.output_edit.setReadOnly(True)  # 推荐设置为只读，仅通过按钮更新
        self.chunk_size_edit = QLineEdit()

        self.combo1 = QComboBox()
        self.combo2 = QComboBox()

        self.init_ui()
        self.refresh_ui()

    def init_ui(self):
        fl = QFormLayout(self)
        fl.addRow(QLabel("文件分割工具"))
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

        fl.addRow("请选择要分割的文件",input_file_operate_layout)
        fl.addRow("请选择输出路径",output_file_operate_layout)
        # 下拉选

        self.combo1.addItems(["binary", "text"])
        fl.addRow(QLabel("分割模式"), self.combo1)

        self.combo2.addItems(["GBK", "UTF-8", "GB2312"])
        fl.addRow(QLabel("文件编码方式"), self.combo2)
        fl.addRow(QLabel("分割大小(MB)"), self.chunk_size_edit)
        split_button = QPushButton("开始分割")
        split_button.clicked.connect(self.start_split)
        fl.addRow(QLabel(""), split_button)

    def refresh_ui(self):
        self.input_edit.setPlaceholderText(self.get_path("input"))
        self.output_edit.setPlaceholderText(self.get_path("output"))

    def on_select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if self.add_path(path,"input"):
            self.refresh_ui()

    def on_select_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择备份输出文件夹")
        if self.add_path(path,"output"):
            self.refresh_ui()

    # 用于保存路径
    def add_path(self, file_path: str,path_type):
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

    # 开始分割方法
    def start_split(self):
        # 获取表单提交参数
        input_path = self.get_path("input")
        output_dir = self.get_path("output")
        chunk_size = self.chunk_size_edit.text()
        mode = self.combo1.currentText()
        encoding = self.combo2.currentText()
        # 标记校验是否通过
        check_passed = True

        # 1. 校验输入文件路径（input_path）
        if not input_path:  # 校验是否为空
            QMessageBox.critical(self, "参数错误", "输入文件路径不能为空！")
            check_passed = False
        elif not os.path.exists(input_path):  # 校验文件是否存在
            QMessageBox.critical(self, "参数错误", f"输入文件不存在：\n{input_path}")
            check_passed = False
        elif not os.path.isfile(input_path):  # 校验是否为文件（非文件夹）
            QMessageBox.critical(self, "参数错误", f"输入路径不是有效文件：\n{input_path}")
            check_passed = False

        # 2. 校验输出文件夹路径（output_dir）- 若不存在则提示创建，或直接自动创建
        if not check_passed:  # 前置校验失败，直接跳过后续校验
            return
        if not output_dir:
            QMessageBox.critical(self, "参数错误", "输出文件夹路径不能为空！")
            check_passed = False
        else:
            if not os.path.exists(output_dir):
                check_passed = False  # 用户取消创建，终止流程
            elif not os.path.isdir(output_dir):  # 校验是否为文件夹（非文件）
                QMessageBox.critical(self, "参数错误", f"输出路径不是有效文件夹：\n{output_dir}")
                check_passed = False

        # 3. 校验分片大小（chunk_size）- 非空、可转换为整数、大于0
        if not check_passed:
            return
        if not chunk_size:
            QMessageBox.critical(self, "参数错误", "分片大小不能为空！")
            check_passed = False
        else:
            try:
                chunk_size_int = int(chunk_size)  # 转换为整数（如需字节单位可后续扩展）
                if chunk_size_int <= 0:
                    QMessageBox.critical(self, "参数错误", "分片大小必须大于0！")
                    check_passed = False
            except ValueError:
                QMessageBox.critical(self, "参数错误", "分片大小必须是有效的正整数！")
                check_passed = False
        # ---------------------- 校验通过，执行文件分割 ----------------------
        if check_passed:
            # 可选：将分片大小转换为整数（如需其他类型可在此处理）
            final_chunk_size = int(chunk_size)
            try:
                FileSplitter.split_file(input_path, output_dir, final_chunk_size, mode, encoding)
                QMessageBox.information(self, "执行成功", "文件分割任务已启动！")
            except Exception as e:
                QMessageBox.critical(self, "执行失败", f"文件分割过程中出现异常：\n{str(e)}")

