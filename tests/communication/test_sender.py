import time
import random
from app.drivers.wifi_driver import WifiCommunicator
from app.services.payload_builder import PayloadBuilder
from app.services.parser import FrameParser

# 配置信息：请修改为接收端电脑的实际 IP 地址
RECEIVER_IP = "192.168.70.129"  # 替换为另一台电脑的 IP
RECEIVER_PORT = 8080


def start_sender_test():
    # 1. 初始化通讯驱动
    comm = WifiCommunicator(RECEIVER_IP, RECEIVER_PORT)

    if not comm.connect():
        print("无法初始化通讯驱动")
        return

    print(f"--- 通讯性能测试启动 (目标: {RECEIVER_IP}) ---")
    print("按下 Ctrl+C 停止测试\n")

    try:
        while True:
            # 2. 模拟随机参数
            m_id = random.randint(1, 5)
            p = round(random.uniform(0.1, 20.0), 2)
            i = round(random.uniform(0.01, 2.0), 2)
            d = round(random.uniform(0.0, 1.0), 2)

            # 3. 业务层：构建载荷 (29 Bytes)
            payload = PayloadBuilder.set_pid(
                motor_id=m_id,
                p=p, i=i, d=d,
                i_limit=100.0,
                out_limit=100.0
            )

            # 4. 协议层：封装成物理帧 (32 Bytes)
            frame = FrameParser.wrap(payload)

            # 5. 驱动层：通过 WiFi 发送
            success = comm.send(frame)

            if success:
                print(f"[SEND OK] ID:{m_id} | P:{p:<5} I:{i:<5} D:{d:<5}")
                # print(f"  HEX: {frame.hex(' ')}") # 如果需要看原始字节流可以取消注释
            else:
                print("[SEND FAIL] 发送失败，请检查网络")

            # 每秒循环一次
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n测试被用户终止")
    finally:
        comm.disconnect()


if __name__ == "__main__":
    start_sender_test()