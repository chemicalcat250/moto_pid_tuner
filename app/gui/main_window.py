# app/gui/main_window.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QLabel, QGroupBox, QTextEdit,
                               QScrollArea, QTabWidget)
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    """
    柜台 (View): 纯 UI 定义类。
    支持单电机控制（页1）与多电机同步控制（页2），右侧固定通讯与日志区。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Motor Tuner V3 - 多机同步版")
        self.setMinimumWidth(1200)
        self.setMinimumHeight(850)

        # 存储控件引用供 UIHandler 绑定
        self.motor_units = []  # 第一页：7组单电机
        self.multi_units = []  # 第二页：5组多机同步动作

        self.init_ui()

    def init_ui(self):
        """部署整体 UI 结构"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_h_layout = QHBoxLayout(main_widget)

        # --- 左侧：分页控制区 (Tabs) ---
        self.tabs = QTabWidget()

        # 第一页：单电机开环控制
        self.tabs.addTab(self._create_single_motor_page(), "单电机控制")
        # 第二页：多电机同步控制
        self.tabs.addTab(self._create_multi_motor_page(), "多机同步预设")

        self.main_h_layout.addWidget(self.tabs, stretch=2)

        # --- 右侧：通讯设置、全局闭环与日志 (始终固定) ---
        right_panel = QVBoxLayout()
        right_panel.addWidget(self._create_connection_group())
        right_panel.addWidget(self._create_closed_loop_group())

        # 日志显示区
        log_group = QGroupBox("通讯日志")
        log_layout = QVBoxLayout()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: 'Consolas';")
        log_layout.addWidget(self.log_area)
        log_group.setLayout(log_layout)
        right_panel.addWidget(log_group)

        self.main_h_layout.addLayout(right_panel, stretch=1)

    def _create_single_motor_page(self):
        """创建第一页：7组电机开环控制"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)

        for i in range(1, 8):
            unit = self._create_motor_control_block(i)
            self.motor_units.append(unit)
            layout.addWidget(unit['group'])

        layout.addStretch()
        scroll.setWidget(scroll_content)
        return scroll

    def _create_multi_motor_page(self):
        """创建第二页：5组多电机同步控制"""
        container = QWidget()
        main_v_layout = QVBoxLayout(container)

        # 头部说明
        header = QLabel("说明：掩码使用二进制(如 1100000 表示控制电机1,2)。点击 + 运行预设，点击 - 反向运行。")
        header.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        main_v_layout.addWidget(header)

        # 创建 5 组交互
        for i in range(1, 6):
            unit = self._create_multi_control_row(i)
            self.multi_units.append(unit)
            main_v_layout.addWidget(unit['group'])

        # 配置保存按钮
        self.btn_save_config = QPushButton("保存当前多机配置至 YAML")
        self.btn_save_config.setFixedHeight(40)
        self.btn_save_config.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        main_v_layout.addWidget(self.btn_save_config)

        main_v_layout.addStretch()
        return container

    def _create_multi_control_row(self, index):
        """创建多机同步控制的单行交互组件"""
        group = QGroupBox(f"同步动作预设 {index}")
        layout = QHBoxLayout()

        # 电机选择掩码 (二进制)
        mask_in = QLineEdit("0000000")
        mask_in.setPlaceholderText("选择掩码")
        mask_in.setFixedWidth(80)
        mask_in.setAlignment(Qt.AlignCenter)

        # 方向掩码 (二进制)
        dir_in = QLineEdit("0000000")
        dir_in.setPlaceholderText("方向掩码")
        dir_in.setFixedWidth(80)
        dir_in.setAlignment(Qt.AlignCenter)

        # 同步速度
        speed_in = QLineEdit("512")
        speed_in.setFixedWidth(60)

        # 动作执行按钮
        btn_plus = QPushButton("+")
        btn_minus = QPushButton("-")
        for btn in [btn_plus, btn_minus]:
            btn.setFixedSize(50, 40)
            btn.setStyleSheet("font-weight: bold; font-size: 18px; background-color: #e67e22; color: white;")

        # 布局组装
        layout.addWidget(QLabel("选择掩码(2进制):"))
        layout.addWidget(mask_in)
        layout.addSpacing(10)
        layout.addWidget(QLabel("预设方向(2进制):"))
        layout.addWidget(dir_in)
        layout.addSpacing(10)
        layout.addWidget(QLabel("速度:"))
        layout.addWidget(speed_in)
        layout.addStretch()
        layout.addWidget(btn_plus)
        layout.addWidget(btn_minus)

        group.setLayout(layout)

        return {
            "group": group,
            "mask_in": mask_in,
            "dir_in": dir_in,
            "speed_in": speed_in,
            "btn_plus": btn_plus,
            "btn_minus": btn_minus
        }

    def _create_motor_control_block(self, index):
        """创建单个电机的控制面板 (原有逻辑)"""
        group = QGroupBox(f"电机 {index} 开环控制")
        layout = QHBoxLayout()

        btn_plus = QPushButton("+")
        btn_minus = QPushButton("-")
        btn_plus.setFixedSize(45, 40)
        btn_minus.setFixedSize(45, 40)
        btn_plus.setStyleSheet("font-weight: bold; background-color: #e67e22; color: white;")
        btn_minus.setStyleSheet("font-weight: bold; background-color: #e67e22; color: white;")

        speed_input = QLineEdit("512")
        speed_input.setFixedWidth(60)
        btn_set_speed = QPushButton("更改速度")

        btn_mode = QPushButton("开环")
        btn_mode.setCheckable(True)
        btn_mode.setFixedWidth(80)
        btn_mode.setStyleSheet("""
            QPushButton:checked { background-color: #2ecc71; color: white; }
            QPushButton { background-color: #bdc3c7; }
        """)

        layout.addWidget(btn_plus)
        layout.addWidget(btn_minus)
        layout.addWidget(QLabel("速度:"))
        layout.addWidget(speed_input)
        layout.addWidget(btn_set_speed)
        layout.addStretch()
        layout.addWidget(btn_mode)

        group.setLayout(layout)
        return {
            "index": index,
            "group": group,
            "btn_plus": btn_plus,
            "btn_minus": btn_minus,
            "speed_in": speed_input,
            "btn_speed": btn_set_speed,
            "btn_mode": btn_mode
        }

    def _create_closed_loop_group(self):
        """全局闭环控制面板 (原有逻辑)"""
        group = QGroupBox("全局闭环与 PID 调试")
        layout = QVBoxLayout()

        h1 = QHBoxLayout()
        self.cl_motor_id = QLineEdit("1")
        self.cl_motor_id.setFixedWidth(50)
        h1.addWidget(QLabel("目标电机 ID:"))
        h1.addWidget(self.cl_motor_id)
        h1.addStretch()
        layout.addLayout(h1)

        h2 = QHBoxLayout()
        self.cl_pos_in = QLineEdit("0.0")
        self.btn_send_pos = QPushButton("发送位置")
        self.btn_send_pos.setStyleSheet("background-color: #3498db; color: white;")
        h2.addWidget(QLabel("目标角度:"))
        h2.addWidget(self.cl_pos_in)
        h2.addWidget(self.btn_send_pos)
        layout.addLayout(h2)

        grid = QVBoxLayout()
        p_layout = QHBoxLayout()
        self.p_in = QLineEdit("15.0")
        self.i_in = QLineEdit("0.5")
        self.d_in = QLineEdit("0.1")
        p_layout.addWidget(QLabel("P:"))
        p_layout.addWidget(self.p_in)
        p_layout.addWidget(QLabel("I:"))
        p_layout.addWidget(self.i_in)
        p_layout.addWidget(QLabel("D:"))
        p_layout.addWidget(self.d_in)

        self.btn_set_pid = QPushButton("修改 PID 参数")
        self.btn_set_pid.setStyleSheet("background-color: #9b59b6; color: white;")

        grid.addLayout(p_layout)
        grid.addWidget(self.btn_set_pid)
        layout.addLayout(grid)

        group.setLayout(layout)
        return group

    def _create_connection_group(self):
        """通讯设置区域 (原有逻辑)"""
        group = QGroupBox("通讯设置")
        layout = QHBoxLayout()
        self.ip_input = QLineEdit("192.168.70.129")
        self.btn_connect = QPushButton("连接设备")
        self.btn_connect.setStyleSheet("background-color: #27ae60; color: white;")

        layout.addWidget(QLabel("IP:"))
        layout.addWidget(self.ip_input)
        layout.addWidget(self.btn_connect)
        group.setLayout(layout)
        return group

    def update_log(self, message: str):
        """系统日志打印接口"""
        self.log_area.append(message)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())