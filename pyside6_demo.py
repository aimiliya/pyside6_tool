import sys
# 导入28+2常用布局管理器和控件
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QLabel, QLineEdit, QTextEdit, QPushButton,
    QCheckBox, QRadioButton,
    QComboBox, QSpinBox, QSlider, QProgressBar,
    QListWidget, QTreeWidget, QTableWidget,
    QTabWidget, QGroupBox,
    QMenuBar, QMenu,
    QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout,
    QDialogButtonBox, QMessageBox, QFileDialog,
    QTreeWidgetItem, QTableWidgetItem  # 必要的数据项类，非UI控件
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt


class CustomDialog(QDialog):
    """自定义对话框类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("对话框")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("这是自定义对话框"))
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """主窗口类，包含菜单栏和多个标签页"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 GUI综合示例")
        self.resize(700, 550)

        # 显式创建并使用 QMenuBar + QMenu + QAction
        menu_bar = QMenuBar()  # 创建菜单栏
        self.setMenuBar(menu_bar)  # 设置为主窗口菜单栏

        # 创建 "文件" 菜单
        file_menu = QMenu("文件", self)  # 创建 QMenu
        menu_bar.addMenu(file_menu)  # 添加到菜单栏

        # 创建菜单项（QAction）
        open_action = QAction("打开文件 QAction", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)  # 添加到 QMenu

        dialog_action = QAction("弹出对话框 QAction", self)
        dialog_action.triggered.connect(self.show_dialog)
        file_menu.addAction(dialog_action)

        exit_action = QAction("退出程序 QAction", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 实例化标签页tabs
        tabs = QTabWidget()

        # Tab 1: 登录和文本 (QFormLayout 表单布局)
        t1 = QWidget()
        # 创建表单布局
        fl = QFormLayout(t1)
        # 添加用户名输入行
        fl.addRow("用户名 QLabel:", QLineEdit("请输入用户名 QLineEdit"))
        # 添加密码输入行，设置为密码模式并添加占位符文本
        pwd = QLineEdit()
        pwd.setEchoMode(QLineEdit.Password)
        pwd.setPlaceholderText("请输入密码：QLineEdit")
        fl.addRow("密码 QLabel:", pwd)
        # 添加登录按钮
        login_btn = QPushButton("登录 QPushButton")
        # 正确添加按钮到布局中
        fl.addRow("登录按钮:", login_btn)

        # 添加文本编辑器部分
        text_label = QLabel("文本编辑器 QTextEdit:")
        fl.addRow(text_label)
        text_edit = QTextEdit()
        text_edit.setPlainText("这是一个多行文本编辑器\n您可以在这里输入和编辑文本内容")
        fl.addRow(text_edit)

        tabs.addTab(t1, "登录 FormLayout")

        # Tab 2: 工具 (QHBoxLayout 水平布局 + QGroupBox 分组框)
        t2 = QWidget()
        # 创建水平布局
        h = QHBoxLayout(t2)
        # 添加自动保存复选框
        auto_save_cb = QCheckBox("自动保存 QCheckBox")
        h.addWidget(auto_save_cb)

        # 创建视图选项分组框
        group = QGroupBox("视图选项 QGroupBox")
        g_layout = QHBoxLayout(group)
        # 添加设计和预览模式单选按钮
        design_rb = QRadioButton("设计模式 QRadioButton")
        preview_rb = QRadioButton("预览模式 QRadioButton")
        g_layout.addWidget(design_rb)
        g_layout.addWidget(preview_rb)
        h.addWidget(group)
        tabs.addTab(t2, "工具 HBoxLayout")

        # Tab 3: 控制 (QVBoxLayout 垂直布局)
        t3 = QWidget()
        # 创建垂直布局
        v = QVBoxLayout(t3)

        # 音量控制、滑块和数值调节
        # 添加音量控制标签和滑块
        v.addWidget(QLabel("音量控制 QSlider:"))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        v.addWidget(slider)

        # 添加音量数值标签和数值调节框
        v.addWidget(QLabel("音量数值 QSpinBox:"))
        spin = QSpinBox()
        spin.setRange(0, 100)
        spin.setValue(50)
        v.addWidget(spin)

        # 连接滑块和数值框
        slider.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(slider.setValue)

        # 质量选择
        # 添加质量设置标签和下拉框
        v.addWidget(QLabel("质量设置 QComboBox:"))
        combo = QComboBox()
        combo.addItems(["低质量", "中等质量", "高质量"])
        v.addWidget(combo)

        # 进度条
        # 添加进度显示标签和进度条
        v.addWidget(QLabel("进度显示 QProgressBar:"))
        progress = QProgressBar()
        progress.setValue(75)
        v.addWidget(progress)

        tabs.addTab(t3, "控制 VBoxLayout")

        # Tab 4: 数据 (QGridLayout 网格布局 + List/Tree/Table)
        t4 = QWidget()
        # 创建网格布局
        g = QGridLayout(t4)

        # 列表控件
        # 添加列表标签和列表控件
        g.addWidget(QLabel("列表 QListWidget:"), 0, 0)
        list_w = QListWidget()
        list_w.addItems(["邮件项目", "日程安排", "待办任务"])
        g.addWidget(list_w, 1, 0)

        # 树形控件
        # 添加树形结构标签和树形控件
        g.addWidget(QLabel("树形结构 QTreeWidget:"), 0, 1)
        tree = QTreeWidget()
        tree.setHeaderLabels(["项目名称"])
        root = QTreeWidgetItem(tree, ["文档目录"])
        QTreeWidgetItem(root, ["报告文件.pdf"])
        QTreeWidgetItem(root, ["预算表格.xlsx"])
        tree.expandAll()
        g.addWidget(tree, 1, 1)

        # 表格控件
        # 添加表格标签和表格控件
        g.addWidget(QLabel("表格 QTableWidget:"), 0, 2)
        table = QTableWidget(3, 2)
        table.setHorizontalHeaderLabels(["种类", "说明"])
        table.setItem(0, 0, QTableWidgetItem("姓名"))
        table.setItem(0, 1, QTableWidgetItem("ianspy"))
        table.setItem(1, 0, QTableWidgetItem("内容"))
        table.setItem(1, 1, QTableWidgetItem("PySide6 示例"))
        table.setItem(2, 0, QTableWidgetItem("状态"))
        table.setItem(2, 1, QTableWidgetItem("进行中"))
        g.addWidget(table, 1, 2)

        tabs.addTab(t4, "数据 GridLayout")
        # 设置中央部件
        self.setCentralWidget(tabs)

    def open_file(self):
        """打开文件对话框"""
        path, _ = QFileDialog.getOpenFileName(self, "打开文件 QFileDialog")
        if path:
            QMessageBox.information(self, "提示", f"已选择：{path}")

    def show_dialog(self):
        """显示自定义对话框"""
        dlg = CustomDialog(self)
        dlg.setWindowTitle("弹出对话框 QDialog")
        dlg.exec()


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
