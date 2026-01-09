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
        """
        初始化 UDP Socket。
        注意：UDP 是无连接的，这里的 connect 主要是准备套接字资源。
        """
        try:
            # 创建 UDP 套接字 (AF_INET 为 IPv4, SOCK_DGRAM 为 UDP)
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # 设置超时，防止 receive 永远阻塞
            self._sock.settimeout(self._timeout)

            # 可以在这里尝试发送一个“心跳/握手”包来确认 ESP32 是否在线
            # 目前先简单标记为已连接
            self._connected = True
            print(f"[WiFi] 已准备好通讯，目标地址: {self._target_addr}")
            return True
        except Exception as e:
            print(f"[WiFi] 连接初始化失败: {e}")
            self._connected = False
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
        """
        接收 32 字节定长响应。
        如果超时或出错，返回空字节。
        """
        if not self._connected or not self._sock:
            return b""

        try:
            # 这里的缓冲区大小设为 1024，但我们只取前 32 字节或验证长度
            data, addr = self._sock.recvfrom(1024)

            if len(data) == self.FRAME_SIZE:
                return data
            else:
                # 记录异常长度包，或者直接丢弃处理
                # print(f"[WiFi] 收到异常长度数据: {len(data)}")
                return b""
        except socket.timeout:
            # 正常现象，表示当前没有数据回传
            return b""
        except Exception as e:
            print(f"[WiFi] 接收异常: {e}")
            return b""

    @property
    def is_connected(self) -> bool:
        return self._connected