# main.qt.py (完整入口)
import sys
import os
from PyQt6.QtWidgets import QApplication

# 确保路径正确
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.gui.main_window import MainWindow
from app.gui.ui_handlers import UIHandler
from app.core.app_controller import AppController

class MotorTunerApp:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.controller = AppController()
        self.view = MainWindow()
        # Handler 会在内部自动处理 7 组电机的循环绑定
        self.handler = UIHandler(self.view, self.controller)

    def run(self):
        self.view.show()
        sys.exit(self.qt_app.exec())

if __name__ == "__main__":
    app = MotorTunerApp()
    app.run()