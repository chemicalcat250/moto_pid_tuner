📂 文件：app/drivers/mock_driver.py
📝 功能描述
MockCommunicator 是底层通讯接口 ICommunicator 的一个模拟实现 (Mock Implementation)。它的存在是为了在没有真实电机硬件或 ESP32 从机的情况下，允许开发者直接在 PC 端完成上层控制逻辑、GUI 界面及 PID 调优算法的闭环调试。

核心作用
脱离硬件开发：模拟真实的连接延迟和数据回传，确保软件逻辑在硬件到位前即可运行。

逻辑验证：通过打印发送的十六进制指令，验证 PayloadBuilder 和 Parser 的封装是否正确。

闭环模拟：自动生成带有随机噪声的模拟电机状态（位置、电流），用于测试 DataProcessor 的解析能力。

方法/属性,行为描述
connect(),模拟 0.5 秒的连接延迟，随后将连接状态置为 True。
send(data),不进行实际网络传输，而是将接收到的字节流以十六进制格式打印到控制台，以便观察指令内容。
receive(),模拟 100Hz 的回传频率（10ms 延迟），并利用 struct 模块生成一个固定的 32 字节数据包。
is_connected,返回当前的模拟连接状态。

📂 文件：app/drivers/wifi_driver.py
📝 功能描述
WifiCommunicator 是底层通讯接口 ICommunicator 的真实硬件实现类。它基于 UDP (User Datagram Protocol) 协议，负责 PC 与从机（如 ESP32 或 Ubuntu 从机）之间的无线数据传输。

核心特性
非阻塞 I/O (Non-blocking)：通过 setblocking(False) 优化，receive 方法在缓冲区无数据时会立即返回空字节，而不会挂起线程。这对于高频控制循环（100Hz+）至关重要。

定长通信：严格遵循 32 字节的物理帧定义，自动过滤掉长度不符的异常干扰包。

资源管理：封装了 Socket 的创建、绑定及释放逻辑，确保程序退出时通讯资源能正确回收。

方法/属性,行为描述
connect(),初始化 AF_INET (IPv4) 和 SOCK_DGRAM (UDP) 套接字，并开启非阻塞模式。
disconnect(),安全关闭套接字，释放系统端口资源。
send(data),"将 32 字节数据通过 sendto 发送到预设的目标地址 (target_ip, target_port)。"
receive(),尝试从缓冲区抓取数据。若无数据，捕获 BlockingIOError 并静默返回；若有数据，仅保留符合 FRAME_SIZE 的有效帧。
is_connected,返回驱动是否已完成初始化并准备好收发。

🛠 技术关键点：非阻塞逻辑
在传统的 socket 编程中，recvfrom 会阻塞程序直到收到数据。本驱动通过以下逻辑实现了高性能轮询：

设置非阻塞：self._sock.setblocking(False)。

异常捕获：在 receive 中捕获 BlockingIOError。

零延迟响应：这种模式允许 comm_handler 的后台线程以极高的频率循环，而不会因为网络延迟导致主程序卡顿。