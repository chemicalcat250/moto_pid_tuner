# app/gui/ui_handlers.py
import os
import yaml
import struct
from PySide6.QtCore import Slot


class UIHandler:
    def __init__(self, window, controller):
        self.window = window
        self.controller = controller
        self.config_path = "multi_motor_config.yaml"

        # 核心信号绑定：日志输出
        self.controller.log_triggered.connect(self.window.update_log)

        # 1. 循环绑定 7 组单电机控制信号 (第一页)
        for unit in self.window.motor_units:
            idx = unit['index']
            # 正转按钮
            unit['btn_plus'].pressed.connect(lambda i=idx: self.handle_press(i, True))
            unit['btn_plus'].released.connect(lambda i=idx: self.controller.stop_motor(i))
            # 反转按钮
            unit['btn_minus'].pressed.connect(lambda i=idx: self.handle_press(i, False))
            unit['btn_minus'].released.connect(lambda i=idx: self.controller.stop_motor(i))
            # 速度与模式
            unit['btn_speed'].clicked.connect(lambda _, i=idx, u=unit: self.handle_speed(i, u))
            unit['btn_mode'].clicked.connect(lambda _, i=idx, u=unit: self.handle_mode(i, u))

        # 2. 绑定多电机同步控制信号 (第二页 - 5组交互)
        # 假设 window.multi_units 是一个包含 5 组 UI 组件字典的列表
            # --- 2. 绑定多电机同步控制信号 (第二页 - 5组交互) ---
        for i, unit in enumerate(self.window.multi_units):
            # 改为按下触发：handle_multi_move 处理具体的掩码和速度逻辑
            unit['btn_plus'].pressed.connect(lambda idx=i: self.handle_multi_move(idx, True))
            unit['btn_minus'].pressed.connect(lambda idx=i: self.handle_multi_move(idx, False))

            # 改为松开触发：直接调用控制器的全局停止指令
            unit['btn_plus'].released.connect(self.controller.stop_multi_motors)
            unit['btn_minus'].released.connect(self.controller.stop_multi_motors)

        # 3. 绑定全局信号
        self.window.btn_send_pos.clicked.connect(self.handle_closed_loop_pos)
        self.window.btn_set_pid.clicked.connect(self.handle_closed_loop_pid)
        self.window.btn_connect.clicked.connect(self.handle_connect)

        # 4. 绑定 YAML 配置保存按钮
        if hasattr(self.window, 'btn_save_config'):
            self.window.btn_save_config.clicked.connect(self.save_to_yaml)

        # 5. 启动时自动加载配置
        self.load_from_yaml()

    # --- 单电机控制逻辑 ---
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
        is_closed = unit['btn_mode'].isChecked()
        self.controller.set_control_mode(motor_id, is_closed)

    # --- 多电机同步控制逻辑 (核心新增) ---
    def handle_multi_move(self, group_idx, is_positive_trigger):
        """
        处理多机同步动作
        :param group_idx: 5组交互中的哪一组
        :param is_positive_trigger: True 为按 + 号，False 为按 - 号
        """
        try:
            unit = self.window.multi_units[group_idx]

            # 1. 解析二进制掩码字符串
            # 例如 "0100000" -> 32 (即 2^5)
            sel_mask = int(unit['mask_in'].text(), 2)
            dir_mask_preset = int(unit['dir_in'].text(), 2)

            # 2. 解析速度
            speed = int(unit['speed_in'].text())
            if not (0 <= speed <= 1024):
                raise ValueError("速度超出范围")

            # 3. 计算实际方向掩码
            # 如果按 +，直接使用预设方向
            # 如果按 -，则需要将预设方向取反（仅针对选中的电机）
            if is_positive_trigger:
                final_dir_mask = dir_mask_preset
            else:
                # 使用异或运算：选中的位如果原来是1则变0，原来是0则变1
                final_dir_mask = dir_mask_preset ^ sel_mask

            # 4. 调用控制器发送 0x41 指令
            self.controller.sync_multi_motors(sel_mask, final_dir_mask, speed)

        except ValueError as e:
            self.window.update_log(f"[ERR] 多机组 {group_idx + 1} 输入错误: 请确保掩码为二进制且速度合法")
        except Exception as e:
            self.window.update_log(f"[ERR] 多机控制执行失败: {str(e)}")

    # --- 配置持久化逻辑 (YAML) ---
    def save_to_yaml(self):
        """将当前 5 组多机预设保存到 YAML 文件"""
        config_data = []
        for unit in self.window.multi_units:
            config_data.append({
                'selection': unit['mask_in'].text(),
                'direction': unit['dir_in'].text(),
                'speed': unit['speed_in'].text()
            })

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            self.window.update_log("[INFO] 多机配置已保存至 YAML")
        except Exception as e:
            self.window.update_log(f"[ERR] 保存 YAML 失败: {e}")

    def load_from_yaml(self):
        """从 YAML 文件读取配置并填充 UI"""
        if not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                return

            for i, data in enumerate(config_data):
                if i < len(self.window.multi_units):
                    unit = self.window.multi_units[i]
                    unit['mask_in'].setText(data.get('selection', '0000000'))
                    unit['dir_in'].setText(data.get('direction', '0000000'))
                    unit['speed_in'].setText(str(data.get('speed', '0')))

            self.window.update_log("[INFO] 已自动加载多机配置")
        except Exception as e:
            self.window.update_log(f"[ERR] 加载 YAML 失败: {e}")

    # --- 其他原有逻辑 ---
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