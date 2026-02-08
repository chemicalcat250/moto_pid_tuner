from app.drivers.mock_driver import MockCommunicator
from app.drivers.wifi_driver import WifiCommunicator  # 假设已写好
from app.core.interface import *

class MotorTunerApp:
    def __init__(self, communicator: ICommunicator):
        # 依赖注入：应用只依赖接口而非具体实现
        self.comm = communicator

    def run(self):
        if self.comm.connect():
            # 模拟业务循环
            for _ in range(5):
                data = self.comm.receive()
                print(f"解析到数据: {data[:10].hex(' ')}...")
            self.comm.disconnect()


if __name__ == "__main__":
    # 在此处决定使用 Mock 还是 真实硬件
    USE_MOCK = True

    driver = MockCommunicator() if USE_MOCK else WifiCommunicator(ip="192.168.1.10")

    app = MotorTunerApp(driver)
    app.run()