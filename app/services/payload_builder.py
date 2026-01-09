import struct


class PayloadBuilder:
    """
    业务载荷构建器：负责生成 29 字节的 Body 载荷。
    结构：Ctrl(1B) + Type(1B) + Data(24B) + Reserved(3B) = 29 Bytes
    """

    # 定义功能类型常量 (Type)
    TYPE_PID = 0x01  # PID 参数类
    TYPE_MOTION = 0x02  # 运动控制类 (目标位置/速度)
    TYPE_ADVANCED = 0x03  # 高级算法参数 (前馈/滤波)
    TYPE_STATUS = 0x04  # 状态查询类 (位置/电流反馈)
    TYPE_SYSTEM = 0xFF  # 系统指令 (重启/急停)

    @staticmethod
    def _build_base(motor_id: int, is_write: bool, type_code: int, data_floats: list) -> bytes:
        """
        内部通用构建方法
        """
        # 1. 构造 Ctrl (Bit 7: Read/Write, Bit 0-6: ID)
        ctrl = (0x80 if is_write else 0x00) | (motor_id & 0x7F)

        # 2. 补齐 6 个 float (24字节)
        if len(data_floats) < 6:
            data_floats += [0.0] * (6 - len(data_floats))

        # 3. 打包: B(Ctrl) + B(Type) + 6f(Data) + 3x(Reserved)
        # 使用 < 表示小端字节序
        return struct.pack("<BB6f3x", ctrl, type_code, *data_floats[:6])

    # --- 具体的业务调用方法 ---

    @classmethod
    def set_pid(cls, motor_id: int, p: float, i: float, d: float,
                i_limit: float = 100.0, out_limit: float = 100.0, deadzone: float = 0.0) -> bytes:
        """
        生成修改 PID 参数的载荷 (写操作)
        """
        return cls._build_base(motor_id, True, cls.TYPE_PID, [p, i, d, i_limit, out_limit, deadzone])

    @classmethod
    def set_target(cls, motor_id: int, pos: float, vel: float = 0.0, acc: float = 0.0) -> bytes:
        """
        生成设定运动目标的载荷 (写操作)
        """
        return cls._build_base(motor_id, True, cls.TYPE_MOTION, [pos, vel, acc, 0, 0, 0])

    @classmethod
    def query_pid(cls, motor_id: int) -> bytes:
        """
        生成查询当前 PID 参数的载荷 (读操作)
        """
        # 读操作时，Data 区通常填充 0
        return cls._build_base(motor_id, False, cls.TYPE_PID, [0] * 6)

    @classmethod
    def query_status(cls, motor_id: int) -> bytes:
        """
        生成查询电机实时状态(位置/电流/速度)的载荷 (读操作)
        """
        return cls._build_base(motor_id, False, cls.TYPE_STATUS, [0] * 6)

    @classmethod
    def system_control(cls, motor_id: int, stop: bool = False, reset: bool = False, set_zero: bool = False) -> bytes:
        """
        系统级控制
        """
        # 这里用 float 的位来模拟标志位，或者直接定义协议
        f1 = 1.0 if stop else 0.0
        f2 = 1.0 if reset else 0.0
        f3 = 1.0 if set_zero else 0.0
        return cls._build_base(motor_id, True, cls.TYPE_SYSTEM, [f1, f2, f3, 0, 0, 0])