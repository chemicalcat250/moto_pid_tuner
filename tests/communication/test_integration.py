import sys
import os
import time
import random

# 1. 自动处理路径，确保能导入 app.services
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.comm_handler import UdpTransceiver
from app.services.payload_builder import PayloadBuilder
from app.services.parser import FrameParser

# ================= 配置区 =================
SLAVE_IP = "192.168.70.129"  # 如果是在同一台机器测试用 127.0.0.1，跨机请改从机真实 IP
SLAVE_PORT = 9000  # 从机监听的端口
HOST_LOCAL_PORT = 8081  # 主机监听的端口 (从机必须往这个端口发)


# ==========================================

def start_host_test():
    print(f"[*] 正在初始化收发器...")
    # 初始化收发器
    comm = UdpTransceiver(remote_ip=SLAVE_IP, remote_port=SLAVE_PORT, local_port=HOST_LOCAL_PORT)
    builder = PayloadBuilder()

    # 启动通讯服务
    if not comm.start():
        print("[!] 无法启动通讯服务，请检查端口是否被占用")
        return

    print(f"\n[√] 主机测试程序已就绪")
    print(f"    - 发送目标: {SLAVE_IP}:{SLAVE_PORT}")
    print(f"    - 本地监听: 0.0.0.0:{HOST_LOCAL_PORT} (等待从机回传)")
    print("-" * 50)

    try:
        count = 0
        while True:
            # 1. 模拟发送指令 (每秒 1 次)
            # 假设发送一个 PID 设置指令 (CMD: 0x03)
            # 注意：请确保你的 PayloadBuilder 中有对应的 set_pid 方法
            try:
                # 构造 29 字节 Payload
                m_id = random.randint(1, 6)
                p_val = round(random.uniform(1.0, 20.0), 2)

                # 如果 PayloadBuilder 还没写好 set_pid，可以先用这个临时构造
                # payload = b'\x03' + b'\x00' * 28
                payload = builder.set_pid(motor_id=m_id, p=p_val, i=0.5, d=0.1)

                # 包装 32 字节帧
                frame = FrameParser.wrap(payload)

                # 发送
                comm.send_packet(frame)
                print(f"[TX] 已发送指令 #{count}: ID={m_id}, P={p_val}")
            except Exception as e:
                print(f"[TX ERROR] 发送逻辑报错: {e}")

            # 2. 检查接收状态
            # 我们直接从 comm 对象的最新数据中读取，看看后台线程有没有干活
            with comm._lock:
                if comm.latest_data:
                    print(f"[RX LATEST] 接收到从机反馈: {comm.latest_data}")
                    # 处理完建议清空，方便下次观察是否有新包
                    # comm.latest_data = None
                else:
                    # 如果一直没收到，打印一下提示
                    if count % 5 == 0:
                        print("[...] 等待接收数据中 (检查从机 IP 是否指向本机, 端口是否为 8081)...")

            time.sleep(1.0)
            count += 1

    except KeyboardInterrupt:
        print("\n[*] 正在停止服务...")
    finally:
        comm.stop()


if __name__ == "__main__":
    start_host_test()