import sys
import psutil
import time

from logger import get_logger
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QApplication,
    QGridLayout, QTableWidgetItem, QLabel, QTableWidget
)
from PySide6.QtCore import QTimer

# 导入拆分后的备份模块
from backup_module import BackupWidget
# 导入拆分后的文件模块
from split_file_module import SplitFileWidget
# 导入excel转java实体模块
from excel_to_entity_module import ExcelToEntityWidget

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """主窗口类，包含菜单栏和多个标签页"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 GUI综合示例")
        self.resize(700, 550)

        # 初始化表格控件引用 定义支持刷新的组件
        self.table = None
        self.dashboard_index = -1

        # 实例化标签页tabs
        tabs = QTabWidget()
        self.create_ybp_ui(tabs)
        self.create_backup_ui(tabs)  # 简化后的备份UI创建
        self.create_split_ui(tabs)
        self.create_excel_ui(tabs)
        self.create_setup_ui(tabs)
        # 设置中央部件
        self.setCentralWidget(tabs)

        # 创建定时器（每2秒刷新一次）
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_system_stats)
        self.timer.setInterval(2000)  # 2秒

        # 连接标签页切换信号
        tabs.currentChanged.connect(self.on_tab_changed)

    # 创建仪表盘ui
    def create_ybp_ui(self, tab):
        widget = QWidget()
        # 创建网格布局
        g = QGridLayout(widget)
        # 添加表格标签和表格控件
        g.addWidget(QLabel("系统状态:"), 0, 0)
        self.table = QTableWidget(4, 2)
        self.table.setHorizontalHeaderLabels(["功能", "使用情况"])

        # 初始数据填充
        self.refresh_system_stats()

        # 设置表格列宽比例
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, int(self.table.width() * 0.2))
        self.table.setColumnWidth(1, int(self.table.width() * 0.8))
        # 设置表格占满可用空间
        self.table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        g.addWidget(self.table)

        tab.addTab(widget, "📊 仪表盘")
        # 保存仪表盘标签页索引
        self.dashboard_index = tab.indexOf(widget)

    # 标签页切换事件处理
    def on_tab_changed(self, index):
        """当标签页切换时启动或停止刷新定时器"""
        if index == self.dashboard_index:
            self.timer.start()
        else:
            self.timer.stop()

    # 刷新系统状态数据
    def refresh_system_stats(self):
        if self.table is None:
            return

        process = psutil.Process()
        memory_info = process.memory_info()
        memory_used_mb = round(memory_info.rss / (1024 * 1024), 2)
        memory_total_mb = round(psutil.virtual_memory().total / (1024 * 1024), 2)
        memory_percent = round(process.memory_percent(), 2)
        cpu_percent = round(process.cpu_percent(interval=0.1), 2)
        process_id = process.pid
        uptime = time.strftime("%H:%M:%S", time.gmtime(time.time() - process.create_time()))

        # 更新表格数据
        self.table.setItem(0, 0, QTableWidgetItem("内存使用:"))
        self.table.setItem(0, 1, QTableWidgetItem(f"{memory_used_mb}MB / {memory_total_mb}MB, 占比: {memory_percent}%"))
        self.table.setItem(1, 0, QTableWidgetItem("CPU使用率:"))
        self.table.setItem(1, 1, QTableWidgetItem(f"{cpu_percent}%"))
        self.table.setItem(2, 0, QTableWidgetItem("进程ID:"))
        self.table.setItem(2, 1, QTableWidgetItem(f"{process_id}"))
        self.table.setItem(3, 0, QTableWidgetItem("运行时间:"))
        self.table.setItem(3, 1, QTableWidgetItem(uptime))

    # 简化后的备份UI创建
    def create_backup_ui(self, tab):
        """创建备份标签页（直接使用拆分后的BackupWidget）"""
        backup_widget = BackupWidget(self)
        tab.addTab(backup_widget, "📁 备份")

    def create_split_ui(self, tab):
        split_widget = SplitFileWidget(self)
        tab.addTab(split_widget, "✂️ 文件分割")

    def create_excel_ui(self, tabs):
        excel_widget = ExcelToEntityWidget(self)
        tabs.addTab(excel_widget, "🗄️ Excel转实体")

    def create_setup_ui(self, tabs):
        pass


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()