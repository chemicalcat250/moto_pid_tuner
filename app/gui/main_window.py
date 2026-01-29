from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QLabel, QGroupBox, QTextEdit, QScrollArea)
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    """
    柜台 (View): 纯 UI 定义类。
    负责 7 组电机开环控制区和 1 组全局闭环控制区的布局。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Motor Tuner V3 - 逻辑解耦版")
        self.setMinimumWidth(1100)
        self.setMinimumHeight(800)

        # 存储所有电机的控件引用，方便 Handler 绑定
        self.motor_units = []

        self.init_ui()

    def init_ui(self):
        """部署整体 UI 结构"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_h_layout = QHBoxLayout(main_widget)

        # --- 左侧：7 组电机开环控制 (使用滚动区域防止界面过长) ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.motor_list_layout = QVBoxLayout(scroll_content)

        for i in range(1, 8):
            unit = self._create_motor_control_block(i)
            self.motor_units.append(unit)
            self.motor_list_layout.addWidget(unit['group'])

        scroll.setWidget(scroll_content)
        self.main_h_layout.addWidget(scroll, stretch=2)

        # --- 右侧：系统设置与全局闭环控制区 ---
        right_panel = QVBoxLayout()

        # 1. 通讯设置
        right_panel.addWidget(self._create_connection_group())

        # 2. 全局闭环控制 (位置与 PID)
        right_panel.addWidget(self._create_closed_loop_group())

        # 3. 日志显示区
        log_group = QGroupBox("通讯日志")
        log_layout = QVBoxLayout()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: 'Consolas';")
        log_layout.addWidget(self.log_area)
        log_group.setLayout(log_layout)
        right_panel.addWidget(log_group)

        self.main_h_layout.addLayout(right_panel, stretch=1)

    def _create_motor_control_block(self, index):
        """创建单个电机的控制面板 (开环控制 0x11-0x14)"""
        group = QGroupBox(f"电机 {index} 开环控制")
        layout = QHBoxLayout()

        # 正/反转点动按钮
        btn_plus = QPushButton("+")
        btn_minus = QPushButton("-")
        btn_plus.setFixedSize(45, 40)
        btn_minus.setFixedSize(45, 40)
        btn_plus.setStyleSheet("font-weight: bold; background-color: #e67e22; color: white;")
        btn_minus.setStyleSheet("font-weight: bold; background-color: #e67e22; color: white;")

        # 速度设置
        speed_input = QLineEdit("512")
        speed_input.setPlaceholderText("0-1024")
        speed_input.setFixedWidth(60)
        btn_set_speed = QPushButton("更改速度")

        # 模式切换按钮 (Checkable)
        btn_mode = QPushButton("开环")
        btn_mode.setCheckable(True)
        btn_mode.setFixedWidth(80)
        btn_mode.setStyleSheet("""
            QPushButton:checked { background-color: #2ecc71; color: white; }
            QPushButton { background-color: #bdc3c7; }
        """)
        # 切换文本的逻辑我们在 Handler 处理，这里只负责外观

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
        """全局闭环控制面板 (0x21/0x22)"""
        group = QGroupBox("全局闭环控制与 PID 调试")
        layout = QVBoxLayout()

        # 目标电机选择
        h1 = QHBoxLayout()
        self.cl_motor_id = QLineEdit("1")
        self.cl_motor_id.setFixedWidth(50)
        h1.addWidget(QLabel("目标电机 ID:"))
        h1.addWidget(self.cl_motor_id)
        h1.addStretch()
        layout.addLayout(h1)

        # 角度控制 (0x21)
        h2 = QHBoxLayout()
        self.cl_pos_in = QLineEdit("0.0")
        self.btn_send_pos = QPushButton("发送位置")
        self.btn_send_pos.setStyleSheet("background-color: #3498db; color: white;")
        h2.addWidget(QLabel("目标角度:"))
        h2.addWidget(self.cl_pos_in)
        h2.addWidget(self.btn_send_pos)
        layout.addLayout(h2)

        # PID 调节 (0x22)
        grid = QVBoxLayout()
        p_layout = QHBoxLayout()
        self.p_in = QLineEdit("15.0");
        self.i_in = QLineEdit("0.5");
        self.d_in = QLineEdit("0.1")
        p_layout.addWidget(QLabel("P:"));
        p_layout.addWidget(self.p_in)
        p_layout.addWidget(QLabel("I:"));
        p_layout.addWidget(self.i_in)
        p_layout.addWidget(QLabel("D:"));
        p_layout.addWidget(self.d_in)

        self.btn_set_pid = QPushButton("修改 PID 参数")
        self.btn_set_pid.setStyleSheet("background-color: #9b59b6; color: white;")

        grid.addLayout(p_layout)
        grid.addWidget(self.btn_set_pid)
        layout.addLayout(grid)

        group.setLayout(layout)
        return group

    def _create_connection_group(self):
        """通讯设置区域"""
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