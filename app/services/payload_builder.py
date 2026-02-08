# app/services/payload_builder.py
import struct


class PayloadBuilder:
    """
    业务载荷构建器：负责生成 29 字节的 Body 载荷。
    结构：Ctrl(1B) + Type(1B) + Data(24B) + Reserved(3B) = 29 Bytes
    """

    # --- 指令功能码定义 (根据 image_d6c518.png) ---
    CMD_MOTOR_MOVE = 0x11  # 电机开始转动
    CMD_MOTOR_STOP = 0x12  # 电机停止转动
    CMD_MOTOR_DIR = 0x13  # 方向改变 (0:反转, 1:正转)
    CMD_MOTOR_SPEED = 0x14  # 速度改变

    CMD_SET_POS = 0x21  # 设定目标角度
    CMD_SET_PID = 0x22  # 设定 PID 参数

    CMD_CTRL_MODE = 0x31  # 控制模式转换 (0:开环, 1:闭环)

    # 新增：多电机同步控制功能码
    CMD_MULTI_MOVE = 0x41
    CMD_MULTI_STOP = 0x42
    @staticmethod
    def _build_base(motor_id: int, is_write: bool, type_code: int, data_floats: list) -> bytes:
        """通用构建方法：打包为 B + B + 6f + 3x"""
        ctrl = (0x80 if is_write else 0x00) | (motor_id & 0x7F)
        if len(data_floats) < 6:
            data_floats += [0.0] * (6 - len(data_floats))
        return struct.pack("<BB6f3x", ctrl, type_code, *data_floats[:6])

    # --- 具体的业务调用方法 ---

    @classmethod
    def motor_move(cls, motor_id: int):
        """0x11: 电机开始转动"""
        return cls._build_base(motor_id, True, cls.CMD_MOTOR_MOVE, [])

    @classmethod
    def motor_stop(cls, motor_id: int):
        """0x12: 电机停止转动"""
        return cls._build_base(motor_id, True, cls.CMD_MOTOR_STOP, [])

    @classmethod
    def motor_dir(cls, motor_id: int, direction: int):
        """0x13: 方向改变 (0:反转, 1:正转)"""
        return cls._build_base(motor_id, True, cls.CMD_MOTOR_DIR, [float(direction)])

    @classmethod
    def motor_speed(cls, motor_id: int, speed: int):
        """0x14: 速度改变"""
        return cls._build_base(motor_id, True, cls.CMD_MOTOR_SPEED, [float(speed)])

    @classmethod
    def set_pos(cls, motor_id: int, target_angle: float):
        """0x21: 设定角度目标值"""
        return cls._build_base(motor_id, True, cls.CMD_SET_POS, [target_angle])

    @classmethod
    def set_pid(cls, motor_id: int, p: float, i: float, d: float):
        """0x22: 设定 PID 参数"""
        return cls._build_base(motor_id, True, cls.CMD_SET_PID, [p, i, d])

    @classmethod
    def ctrl_mode(cls, motor_id: int, mode: int):
        """0x31: 控制模式转换 (0:开环, 1:闭环)"""
        return cls._build_base(motor_id, True, cls.CMD_CTRL_MODE, [float(mode)])

    @classmethod
    def multi_motor_move(cls, selection_mask: int, direction_mask: int, speed: int):
        """
        0x41: 多电机同步控制运动
        :param selection_mask: 电机选择掩码 (Bit 0-6 对应电机 1-7)
        :param direction_mask: 电机方向掩码 (Bit 0-6 对应电机 1-7 方向)
        :param speed: 同步运动速度 (范围: 0-1024)
        """
        # 使用 0x7F 作为广播/群组 ID
        # 将掩码和速度依次存入 data_floats 列表，由 _build_base 打包为 float 发送
        data_list = [
            float(selection_mask),
            float(direction_mask),
            float(speed)
        ]
        return cls._build_base(0x7F, True, cls.CMD_MULTI_MOVE, data_list)

    @classmethod
    def multi_motor_stop(cls):
        """0x42: 所有同步运动的电机停止"""
        # 使用广播 ID 0x7F 告知所有相关电机停止
        return cls._build_base(0x7F, True, cls.CMD_MULTI_STOP, [])