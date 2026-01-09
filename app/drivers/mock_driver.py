import time
import random
import struct
from ..core.interface import ICommunicator


class MockCommunicator(ICommunicator):
    """模拟通讯器，用于无硬件调试"""

    def __init__(self):
        self._connected = False
        self.packet_size = 32  # 假设定长 32 字节

    def connect(self) -> bool:
        print("[Mock] 正在连接模拟电机...")
        time.sleep(0.5)
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False
        print("[Mock] 模拟连接已断开")

    def send(self, data: bytes) -> bool:
        if not self._connected: return False
        print(f"[Mock] 发送指令: {data.hex(' ')}")
        return True

    def receive(self) -> bytes:
        """模拟 ESP32 回传的电机状态数据"""
        if not self._connected: return b""
        time.sleep(0.01)  # 模拟 100Hz 的采样率

        # 模拟生成一帧数据：[帧头, 电机ID, 当前位置, 当前电流, 状态位...]
        # 这里仅作演示，具体格式取决于你的指令集定义
        header = 0xAA
        motor_id = 1
        pos = 100.0 + random.uniform(-1, 1)
        current = 0.5 + random.uniform(-0.1, 0.1)

        # 使用 struct 打包成字节流
        return struct.pack("<BBff22x", header, motor_id, pos, current)

    @property
    def is_connected(self) -> bool:
        return self._connected