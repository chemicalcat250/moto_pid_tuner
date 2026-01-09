import socket
import time
from typing import Optional
from ..core.interface import ICommunicator


class WifiCommunicator(ICommunicator):
    """
    基于 UDP 的 WiFi 通讯驱动实现
    """

    def __init__(self, target_ip: str, target_port: int, timeout: float = 1.0):
        self._target_addr = (target_ip, target_port)
        self._timeout = timeout
        self._sock: Optional[socket.socket] = None
        self._connected = False

        # 32 字节定长
        self.FRAME_SIZE = 32

    def connect(self) -> bool:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 核心优化：设置为非阻塞模式
            self._sock.setblocking(False)
            self._connected = True
            print(f"[WiFi] 非阻塞模式已就绪")
            return True
        except Exception as e:
            print(f"[WiFi] 初始化失败: {e}")
            return False

    def disconnect(self):
        """关闭套接字"""
        if self._sock:
            self._sock.close()
            self._sock = None
        self._connected = False
        print("[WiFi] 通讯已关闭")

    def send(self, data: bytes) -> bool:
        """发送 32 字节定长指令"""
        if not self._connected or not self._sock:
            return False

        try:
            # 发送数据到预设的目标地址
            sent_len = self._sock.sendto(data, self._target_addr)
            return sent_len == len(data)
        except Exception as e:
            print(f"[WiFi] 发送失败: {e}")
            return False

    def receive(self) -> bytes:
        if not self._connected or not self._sock:
            return b""
        try:
            # 非阻塞模式下，如果没有数据会立即抛出 BlockingIOError
            data, addr = self._sock.recvfrom(1024)
            if len(data) == self.FRAME_SIZE:
                return data
            return b""
        except (BlockingIOError, socket.error):
            # 捕获异常表示当前缓冲区无数据，立即返回
            return b""
        except Exception as e:
            print(f"[WiFi] 接收异常: {e}")
            return b""

    @property
    def is_connected(self) -> bool:
        return self._connected