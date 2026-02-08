from PySide6.QtCore import QObject, Signal
from ..services.comm_handler import UdpTransceiver
from ..services.payload_builder import PayloadBuilder
from ..services.parser import FrameParser


class AppController(QObject):
    """
    总控制器 (Manager): 负责业务逻辑调度与指令下发 。
    作为 UI 与 Service 层之间的中转站。
    """

    # 定义 PySide 信号：用于将异步收到的数据安全地推送到 UI 线程
    # 这样 UI 监听此信号即可，无需再用 QTimer 轮询 [cite: 304, 313]
    data_received = Signal(dict)
    log_triggered = Signal(str)

    def __init__(self):
        super().__init__()

        # 1. 初始化核心服务组件
        # 默认 IP 与 端口，后续可通过 connect_device 动态修改 [cite: 304-305]
        self.comm = UdpTransceiver(remote_ip="192.168.70.129", remote_port=9000)
        self.builder = PayloadBuilder()

        # 2. 绑定通讯层回调 [cite: 271-272]
        # 当 UdpTransceiver 在后台线程解析完包后，会调用此匿名函数
        self.comm.on_data_received = lambda data: self.data_received.emit(data)

    def connect_device(self, ip: str, port: int = 9000) -> bool:
        """
        连接设备并启动监听线程 [cite: 311-312]。
        """
        self.comm.driver._target_addr = (ip, port)
        success = self.comm.start()

        if success:
            self.log_triggered.emit(f"[SYS] 控制中心已启动，目标: {ip}:{port}")
        else:
            self.log_triggered.emit(f"[ERR] 启动通讯失败，请检查网络设置")
        return success

    def disconnect_device(self):
        """断开设备连接"""
        self.comm.stop()
        self.log_triggered.emit("[SYS] 通讯已断开")

    def _execute_send(self, payload: bytes) -> bool:
        """
        私有方法：执行底层封包与物理发送 [cite: 53, 127]。
        """
        if not payload:
            return False

        # 自动调用 Parser 进行 32 字节封包（加包头与校验）[cite: 127, 290]
        frame = FrameParser.wrap(payload)
        return self.comm.send_packet(frame)

    # --- 高级业务接口 (提供给 UIHandler 调用) ---

    def start_motor(self, motor_id: int):
        """[0x11] 开始转动"""
        payload = self.builder.motor_move(motor_id)
        if self._execute_send(payload):
            self.log_triggered.emit(f"[TX] ID:{motor_id} 指令: 开始转动")

    def stop_motor(self, motor_id: int):
        """[0x12] 停止转动"""
        payload = self.builder.motor_stop(motor_id)
        if self._execute_send(payload):
            self.log_triggered.emit(f"[TX] ID:{motor_id} 指令: 停止转动")

    def set_motor_direction(self, motor_id: int, is_forward: bool):
        """[0x13] 设置方向"""
        dir_val = 1 if is_forward else 0
        payload = self.builder.motor_dir(motor_id, dir_val)
        if self._execute_send(payload):
            label = "正转" if is_forward else "反转"
            self.log_triggered.emit(f"[TX] ID:{motor_id} 设置方向: {label}")

    def set_motor_speed(self, motor_id: int, speed: int):
        """[0x14] 设置速度"""
        payload = self.builder.motor_speed(motor_id, speed)
        if self._execute_send(payload):
            self.log_triggered.emit(f"[TX] ID:{motor_id} 设置速度: {speed}")

    def set_motor_angle(self, motor_id: int, angle: float):
        """[0x21] 设置角度"""
        payload = self.builder.set_pos(motor_id, angle)
        if self._execute_send(payload):
            self.log_triggered.emit(f"[TX] ID:{motor_id} 设定角度: {angle:.2f}")

    def set_motor_pid(self, motor_id: int, p: float, i: float, d: float):
        """[0x22] 设置 PID"""
        payload = self.builder.set_pid(motor_id, p, i, d)
        if self._execute_send(payload):
            self.log_triggered.emit(f"[TX] ID:{motor_id} PID更新: P={p} I={i} D={d}")

    def set_control_mode(self, motor_id: int, is_closed_loop: bool):
        """[0x31] 切换模式"""
        mode_val = 1 if is_closed_loop else 0
        payload = self.builder.ctrl_mode(motor_id, mode_val)
        if self._execute_send(payload):
            label = "闭环控制" if is_closed_loop else "开环控制"
            self.log_triggered.emit(f"[TX] ID:{motor_id} 模式切换: {label}")

    def sync_multi_motors(self, selection_mask: int, direction_mask: int, speed: int):
        """
        [0x41] 多电机同步控制接口
        :param selection_mask: 电机选择掩码
        :param direction_mask: 电机方向掩码
        :param speed: 0-1024 范围的速度
        """
        # 调用我们刚刚在 PayloadBuilder 中写好的方法
        payload = self.builder.multi_motor_move(selection_mask, direction_mask, speed)

        # 执行物理发送
        if self._execute_send(payload):
            # 将操作记录到日志，方便调试
            msg = (f"[TX] 多机控制 - 掩码: {bin(selection_mask)} "
                   f"方向: {bin(direction_mask)} 速度: {speed}")
            self.log_triggered.emit(msg)

    def stop_multi_motors(self):
        """
        [0x42] 发送同步停止指令
        """
        payload = self.builder.multi_motor_stop()
        if self._execute_send(payload):
            self.log_triggered.emit("[TX] 多机同步停止 (0x42)")