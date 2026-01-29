# app/gui/ui_handlers.py
from PySide6.QtCore import Slot


class UIHandler:
    def __init__(self, window, controller):
        self.window = window
        self.controller = controller

        self.controller.log_triggered.connect(self.window.update_log)

        # 1. 循环绑定 7 组电机信号
        for unit in self.window.motor_units:
            idx = unit['index']
            # 使用 lambda 捕获当前索引 idx
            # 正转按钮
            unit['btn_plus'].pressed.connect(lambda i=idx: self.handle_press(i, True))
            unit['btn_plus'].released.connect(lambda i=idx: self.controller.stop_motor(i))

            # 反转按钮
            unit['btn_minus'].pressed.connect(lambda i=idx: self.handle_press(i, False))
            unit['btn_minus'].released.connect(lambda i=idx: self.controller.stop_motor(i))

            # 速度与模式
            unit['btn_speed'].clicked.connect(lambda _, i=idx, u=unit: self.handle_speed(i, u))
            unit['btn_mode'].clicked.connect(lambda _, i=idx, u=unit: self.handle_mode(i, u))

        # 2. 绑定闭环控制信号
        self.window.btn_send_pos.clicked.connect(self.handle_closed_loop_pos)
        self.window.btn_set_pid.clicked.connect(self.handle_closed_loop_pid)
        self.window.btn_connect.clicked.connect(self.handle_connect)

    def handle_press(self, motor_id, is_forward):
        """按下按钮：先设方向再启动"""
        self.controller.set_motor_direction(motor_id, is_forward)
        self.controller.start_motor(motor_id)

    def handle_speed(self, motor_id, unit):
        try:
            speed = int(unit['speed_in'].text())
            self.controller.set_motor_speed(motor_id, speed)
        except ValueError:
            self.window.update_log(f"[ERR] 电机 {motor_id} 速度输入无效")

    def handle_mode(self, motor_id, unit):
        # 按钮选中状态为闭环(1)，未选中为开环(0)
        is_closed = unit['btn_mode'].isChecked()
        self.controller.set_control_mode(motor_id, is_closed)

    def handle_closed_loop_pos(self):
        try:
            m_id = int(self.window.cl_motor_id.text())
            pos = float(self.window.cl_pos_in.text())
            self.controller.set_motor_angle(m_id, pos)
        except ValueError:
            self.window.update_log("[ERR] 闭环位置输入无效")

    def handle_closed_loop_pid(self):
        try:
            m_id = int(self.window.cl_motor_id.text())
            p = float(self.window.p_in.text())
            i = float(self.window.i_in.text())
            d = float(self.window.d_in.text())
            self.controller.set_motor_pid(m_id, p, i, d)
        except ValueError:
            self.window.update_log("[ERR] PID 参数输入无效")

    def handle_connect(self):
        ip = self.window.ip_input.text()
        self.controller.connect_device(ip)