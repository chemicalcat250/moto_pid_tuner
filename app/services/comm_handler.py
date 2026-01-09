import threading
import time
from .parser import FrameParser
from .data_processor import DataProcessor
# 导入驱动层
from ..drivers.wifi_driver import WifiCommunicator


class UdpTransceiver:
    """
    通信处理器：基于 WifiCommunicator 驱动，
    实现后台自动接收、解析以及主动发送功能。
    """

    def __init__(self, remote_ip: str, remote_port: int, local_port: int = 8081):
        # 1. 初始化驱动层
        # 注意：为了能接收数据，我们需要确保驱动能绑定本地端口
        self.driver = WifiCommunicator(remote_ip, remote_port)
        self.local_port = local_port

        # 2. 初始化协议解析工具
        self.parser = FrameParser()
        self.processor = DataProcessor()

        # 3. 状态维护
        self.latest_data = None
        self.running = False
        self._lock = threading.Lock()
        self._thread = None

    def start(self):
        """启动驱动并开启监听线程"""
        if not self.driver.connect():
            print("[Comm] 驱动初始化失败，请检查网络")
            return False

        # 修正：WiFiCommunicator 默认不 bind，我们需要在底层 socket 准备好后绑定本地端口
        # 这样从机才能主动发数据到本机的 8081
        if self.driver._sock:
            try:
                self.driver._sock.bind(("", self.local_port))
                print(f"[Comm] 已绑定本地端口 {self.local_port} 用于接收反馈")
            except Exception as e:
                print(f"[Comm] 绑定端口失败: {e}")

        self.running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        return True

    def _listen_loop(self):
        """后台循环：通过驱动层 receive 数据"""
        while self.running:
            try:
                # 调用驱动层的 receive 方法（内部已处理 32 字节判断和超时）
                raw_data = self.driver.receive()

                if raw_data:
                    # 1. 协议层脱壳
                    unwrapped = self.parser.unwrap(raw_data)
                    if unwrapped:
                        # 2. 业务层解析并输出
                        result = self.processor.process(unwrapped)
                        with self._lock:
                            self.latest_data = result
            except Exception as e:
                print(f"[Comm] 监听线程异常: {e}")

            # 微小休眠避免空转
            time.sleep(0.001)

    def send_packet(self, frame: bytes) -> bool:
        """调用驱动层发送 32 字节物理帧"""
        if len(frame) != 32:
            print(f"[Comm] 错误：尝试发送非法长度的数据 ({len(frame)}B)")
            return False
        return self.driver.send(frame)

    def stop(self):
        """停止服务并关闭驱动"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self.driver.disconnect()
        print("[Comm] 收发服务已停止")