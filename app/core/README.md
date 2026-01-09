📂 文件：app/core/interface.py
📝 功能描述
该文件定义了底层通讯的抽象基类 (Abstract Base Class, ABC) —— ICommunicator。它是整个项目驱动层的接口规范，规定了无论使用何种物理媒介（如 WiFi、串口、蓝牙），其对应的驱动类都必须实现这一套标准方法。

核心作用：依赖倒置 (Dependency Inversion)
在架构中，上层的 UdpTransceiver（收发器）不直接依赖于具体的物理驱动，而是依赖于这个接口。这意味着如果你未来想把 WiFi 换成串口，你只需要编写一个新的实现类，而不需要修改任何业务层代码。

方法/属性,返回类型,功能描述
connect(),bool,初始化通讯资源（如创建 Socket），成功返回 True。
disconnect(),None,释放通讯资源，关闭连接。
send(data),bool,发送原始字节流（bytes）。要求实现类处理具体的发送逻辑。
receive(),bytes,接收原始字节流。实现类需负责读取数据并返回。
is_connected,bool,属性：获取当前通讯链路的连接状态。


