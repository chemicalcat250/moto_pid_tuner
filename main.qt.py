# main.qt.py (重构后 - 统一 PySide6)
import sys
import os
# 关键修改：从 PySide6 导入 QApplication
from PySide6.QtWidgets import QApplication

# 确保路径正确，以便导入 app 包
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.gui.main_window import MainWindow
from app.gui.ui_handlers import UIHandler
from app.core.app_controller import AppController


class MotorTunerApp:
    def __init__(self):
        # 初始化 PySide6 的应用实例
        self.qt_app = QApplication(sys.argv)

        # 核心逻辑控制器
        self.controller = AppController()

        # 视图层 (MainWindow 内部已使用 PySi=de6)
        self.view = MainWindow()

        # 信号绑定处理
        self.handler = UIHandler(self.view, self.controller)

    def run(self):
        self.view.show()
        # PySide6 建议使用 exec()，而 PyQt6 以前常使用 exec_()
        sys.exit(self.qt_app.exec())


if __name__ == "__main__":
    app = MotorTunerApp()
    app.run()