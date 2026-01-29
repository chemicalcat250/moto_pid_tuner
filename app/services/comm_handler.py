import threading
import time
from typing import Callable, Optional
from .parser import FrameParser
from .data_processor import DataProcessor
from ..drivers.wifi_driver import WifiCommunicator


class UdpTransceiver:
    """
    通信处理器：实现后台自动接收、解析以及主动发送功能 [cite: 271]。
    不再直接持有数据，而是通过回调通知上层逻辑。
    """

    def __init__(self, remote_ip: str, remote_port: int, local_port: int = 8081):
        # 1. 初始化通讯层组件
        self.driver = WifiCommunicator(remote_ip, remote_port)
        self.local_port = local_port
        self.parser = FrameParser()
        self.processor = DataProcessor()

        # 2. 状态与线程维护 [cite: 273]
        self.running = False
        self._thread = None

        # 数据接收回调函数：当解析出合法包时调用此函数
        self.on_data_received: Optional[Callable[[dict], None]] = None

    def start(self) -> bool:
        """启动驱动并开启异步监听线程 [cite: 273]"""
        if not self.driver.connect():
            return False

        # 绑定本地端口用于接收从机反馈 [cite: 274]
        if self.driver._sock:
            try:
                self.driver._sock.bind(("", self.local_port))
                print(f"[Comm] 已绑定本地端口 {self.local_port} ")
            except Exception as e:
                print(f"[Comm] 端口绑定失败: {e}")
                return False

        self.running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)  # 使用守护线程 [cite: 275]
        self._thread.start()
        return True

    def _listen_loop(self):
        """后台轮询线程 [cite: 275]"""
        while self.running:
            try:
                # 1. 从驱动层获取 32 字节原始数据 [cite: 276]
                raw_data = self.driver.receive()

                if raw_data:
                    # 2. 验证帧结构并脱壳 (剥离包头包尾校验) [cite: 276, 289]
                    body = self.parser.unwrap(raw_data)
                    if body:
                        # 3. 业务层解析 [cite: 277, 280]
                        result = self.processor.process(body)
                        # 4. 如果设置了回调，则将结果推送出去
                        if result and self.on_data_received:
                            self.on_data_received(result)
            except Exception as e:
                print(f"[Comm] 监听线程异常: {e} ")

            time.sleep(0.001)  # 微休眠避免 CPU 空转

    def send_packet(self, frame: bytes) -> bool:
        """发送 32 字节物理帧 """
        if len(frame) != 32:
            print(f"[Comm] 非法帧长度: {len(frame)}B")
            return False
        return self.driver.send(frame)

    def stop(self):
        """停止服务并关闭驱动 [cite: 279]"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self.driver.disconnect()
        print("[Comm] 通讯服务已停止")