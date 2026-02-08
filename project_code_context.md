# Project Source Code Archive
- **Generated at**: 2026-02-07 22:49:48
- **Root**: `F:\滑雪机器人\moto_pid_tuner-master`

## Project Structure
```text
main.qt.py
app\__init__.py
app\core\app_controller.py
app\core\interface.py
app\core\__init__.py
app\drivers\mock_driver.py
app\drivers\wifi_driver.py
app\drivers\__init__.py
app\gui\main_window.py
app\gui\signals.py
app\gui\ui_handlers.py
app\gui\__init__.py
app\services\comm_handler.py
app\services\data_processor.py
app\services\parser.py
app\services\payload_builder.py
app\services\__init__.py
```

---

## Source Code Content

### File: main.qt.py
```python
# main.qt.py (重构后 - 统一 PySide6)
import sys
import os
# 关键修改：从 PySide6 导入 QApplication
from PySide6.QtWidgets import QApplication

# 确保路径正确，以便导入 app 包
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.gui.main_window import MainWindow
from app.gui.ui_handlers import UIHandler
from app.core.app_controller import AppController


class MotorTunerApp:
    def __init__(self):
        # 初始化 PySide6 的应用实例
        self.qt_app = QApplication(sys.argv)

        # 核心逻辑控制器
        self.controller = AppController()

        # 视图层 (MainWindow 内部已使用 PySi=de6)
        self.view = MainWindow()

        # 信号绑定处理
        self.handler = UIHandler(self.view, self.controller)

    def run(self):
        self.view.show()
        # PySide6 建议使用 exec()，而 PyQt6 以前常使用 exec_()
        sys.exit(self.qt_app.exec())


if __name__ == "__main__":
    app = MotorTunerApp()
    app.run()
```

### File: app\__init__.py
```python

```

### File: app\core\app_controller.py
```python
from PySide6.QtCore import QObject, Signal
from ..services.comm_handler import UdpTransceiver
from ..services.payload_builder import PayloadBuilder
from ..services.parser import FrameParser


class AppController(QObject):
    """
    总控制器 (Manager): 负责业务逻辑调度与指令下发 。
    作为 UI 与 Service 层之间的中转站。
    """

    # 定义 PySide 信号：用于将异步收到的数据安全地推送到 UI 线程
    # 这样 UI 监听此信号即可，无需再用 QTimer 轮询 [cite: 304, 313]
    data_received = Signal(dict)
    log_triggered = Signal(str)

    def __init__(self):
        super().__init__()

        # 1. 初始化核心服务组件
        # 默认 IP 与 端口，后续可通过 connect_device 动态修改 [cite: 304-305]
        self.comm = UdpTransceiver(remote_ip="192.168.70.129", remote_port=9000)
        self.builder = PayloadBuilder()

        # 2. 绑定通讯层回调 [cite: 271-272]
        # 当 UdpTransceiver 在后台线程解析完包后，会调用此匿名函数
        self.comm.on_data_received = lambda data: self.data_received.emit(data)

    def connect_device(self, ip: str, port: int = 9000) -> bool:
        """
        连接设备并启动监听线程 [cite: 311-312]。
        """
        self.comm.driver._target_addr = (ip, port)
        success = self.comm.start()

        if success:
            self.log_triggered.emit(f"[SYS] 控制中心已启动，目标: {ip}:{port}")
        else:
            self.log_triggered.emit(f"[ERR] 启动通讯失败，请检查网络设置")
        return success

    def disconnect_device(self):
        """断开设备连接"""
        self.comm.stop()
        self.log_triggered.emit("[SYS] 通讯已断开")

    def _execute_send(self, payload: bytes) -> bool:
        """
        私有方法：执行底层封包与物理发送 [cite: 53, 127]。
        """
        if not payload:
            return False

        # 自动调用 Parser 进行 32 字节封包（加包头与校验）[cite: 127, 290]
        frame = FrameParser.wrap(payload)
        return self.comm.send_packet(frame)

    # --- 高级业务接口 (提供给 UIHandler 调用) ---

    def start_motor(self, motor_id: int):
        """[0x11] 开始转动"""
        payload = self.builder.motor_move(motor_id)
        if self._execute_send(payload):
            self.log_triggered.emit(f"[TX] ID:{motor_id} 指令: 开始转动")

    def stop_motor(self, motor_id: int):
        """[0x12] 停止转动"""
        payload = self.builder.motor_stop(motor_id)
        if self._execute_send(payload):
            self.log_triggered.emit(f"[TX] ID:{motor_id} 指令: 停止转动")

    def set_motor_direction(self, motor_id: int, is_forward: bool):
        """[0x13] 设置方向"""
        dir_val = 1 if is_forward else 0
        payload = self.builder.motor_dir(motor_id, dir_val)
        if self._execute_send(payload):
            label = "正转" if is_forward else "反转"
            self.log_triggered.emit(f"[TX] ID:{motor_id} 设置方向: {label}")

    def set_motor_speed(self, motor_id: int, speed: int):
        """[0x14] 设置速度"""
        payload = self.builder.motor_speed(motor_id, speed)
        if self._execute_send(payload):
            self.log_triggered.emit(f"[TX] ID:{motor_id} 设置速度: {speed}")

    def set_motor_angle(self, motor_id: int, angle: float):
        """[0x21] 设置角度"""
        payload = self.builder.set_pos(motor_id, angle)
        if self._execute_send(payload):
            self.log_triggered.emit(f"[TX] ID:{motor_id} 设定角度: {angle:.2f}")

    def set_motor_pid(self, motor_id: int, p: float, i: float, d: float):
        """[0x22] 设置 PID"""
        payload = self.builder.set_pid(motor_id, p, i, d)
        if self._execute_send(payload):
            self.log_triggered.emit(f"[TX] ID:{motor_id} PID更新: P={p} I={i} D={d}")

    def set_control_mode(self, motor_id: int, is_closed_loop: bool):
        """[0x31] 切换模式"""
        mode_val = 1 if is_closed_loop else 0
        payload = self.builder.ctrl_mode(motor_id, mode_val)
        if self._execute_send(payload):
            label = "闭环控制" if is_closed_loop else "开环控制"
            self.log_triggered.emit(f"[TX] ID:{motor_id} 模式切换: {label}")
```

### File: app\core\interface.py
```python
from abc import ABC, abstractmethod


class ICommunicator(ABC):
    """底层通讯接口"""

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def send(self, data: bytes) -> bool:
        """发送定长指令"""
        pass

    @abstractmethod
    def receive(self) -> bytes:
        """接收定长指令"""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        pass
```

### File: app\core\__init__.py
```python
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
```

### File: app\drivers\mock_driver.py
```python
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
```

### File: app\drivers\wifi_driver.py
```python
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
```

### File: app\drivers\__init__.py
```python

```

### File: app\gui\main_window.py
```python
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QLabel, QGroupBox, QTextEdit, QScrollArea)
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    """
    柜台 (View): 纯 UI 定义类。
    负责 7 组电机开环控制区和 1 组全局闭环控制区的布局。
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Motor Tuner V3 - 逻辑解耦版")
        self.setMinimumWidth(1100)
        self.setMinimumHeight(800)

        # 存储所有电机的控件引用，方便 Handler 绑定
        self.motor_units = []

        self.init_ui()

    def init_ui(self):
        """部署整体 UI 结构"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_h_layout = QHBoxLayout(main_widget)

        # --- 左侧：7 组电机开环控制 (使用滚动区域防止界面过长) ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.motor_list_layout = QVBoxLayout(scroll_content)

        for i in range(1, 8):
            unit = self._create_motor_control_block(i)
            self.motor_units.append(unit)
            self.motor_list_layout.addWidget(unit['group'])

        scroll.setWidget(scroll_content)
        self.main_h_layout.addWidget(scroll, stretch=2)

        # --- 右侧：系统设置与全局闭环控制区 ---
        right_panel = QVBoxLayout()

        # 1. 通讯设置
        right_panel.addWidget(self._create_connection_group())

        # 2. 全局闭环控制 (位置与 PID)
        right_panel.addWidget(self._create_closed_loop_group())

        # 3. 日志显示区
        log_group = QGroupBox("通讯日志")
        log_layout = QVBoxLayout()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: 'Consolas';")
        log_layout.addWidget(self.log_area)
        log_group.setLayout(log_layout)
        right_panel.addWidget(log_group)

        self.main_h_layout.addLayout(right_panel, stretch=1)

    def _create_motor_control_block(self, index):
        """创建单个电机的控制面板 (开环控制 0x11-0x14)"""
        group = QGroupBox(f"电机 {index} 开环控制")
        layout = QHBoxLayout()

        # 正/反转点动按钮
        btn_plus = QPushButton("+")
        btn_minus = QPushButton("-")
        btn_plus.setFixedSize(45, 40)
        btn_minus.setFixedSize(45, 40)
        btn_plus.setStyleSheet("font-weight: bold; background-color: #e67e22; color: white;")
        btn_minus.setStyleSheet("font-weight: bold; background-color: #e67e22; color: white;")

        # 速度设置
        speed_input = QLineEdit("512")
        speed_input.setPlaceholderText("0-1024")
        speed_input.setFixedWidth(60)
        btn_set_speed = QPushButton("更改速度")

        # 模式切换按钮 (Checkable)
        btn_mode = QPushButton("开环")
        btn_mode.setCheckable(True)
        btn_mode.setFixedWidth(80)
        btn_mode.setStyleSheet("""
            QPushButton:checked { background-color: #2ecc71; color: white; }
            QPushButton { background-color: #bdc3c7; }
        """)
        # 切换文本的逻辑我们在 Handler 处理，这里只负责外观

        layout.addWidget(btn_plus)
        layout.addWidget(btn_minus)
        layout.addWidget(QLabel("速度:"))
        layout.addWidget(speed_input)
        layout.addWidget(btn_set_speed)
        layout.addStretch()
        layout.addWidget(btn_mode)

        group.setLayout(layout)

        return {
            "index": index,
            "group": group,
            "btn_plus": btn_plus,
            "btn_minus": btn_minus,
            "speed_in": speed_input,
            "btn_speed": btn_set_speed,
            "btn_mode": btn_mode
        }

    def _create_closed_loop_group(self):
        """全局闭环控制面板 (0x21/0x22)"""
        group = QGroupBox("全局闭环控制与 PID 调试")
        layout = QVBoxLayout()

        # 目标电机选择
        h1 = QHBoxLayout()
        self.cl_motor_id = QLineEdit("1")
        self.cl_motor_id.setFixedWidth(50)
        h1.addWidget(QLabel("目标电机 ID:"))
        h1.addWidget(self.cl_motor_id)
        h1.addStretch()
        layout.addLayout(h1)

        # 角度控制 (0x21)
        h2 = QHBoxLayout()
        self.cl_pos_in = QLineEdit("0.0")
        self.btn_send_pos = QPushButton("发送位置")
        self.btn_send_pos.setStyleSheet("background-color: #3498db; color: white;")
        h2.addWidget(QLabel("目标角度:"))
        h2.addWidget(self.cl_pos_in)
        h2.addWidget(self.btn_send_pos)
        layout.addLayout(h2)

        # PID 调节 (0x22)
        grid = QVBoxLayout()
        p_layout = QHBoxLayout()
        self.p_in = QLineEdit("15.0");
        self.i_in = QLineEdit("0.5");
        self.d_in = QLineEdit("0.1")
        p_layout.addWidget(QLabel("P:"));
        p_layout.addWidget(self.p_in)
        p_layout.addWidget(QLabel("I:"));
        p_layout.addWidget(self.i_in)
        p_layout.addWidget(QLabel("D:"));
        p_layout.addWidget(self.d_in)

        self.btn_set_pid = QPushButton("修改 PID 参数")
        self.btn_set_pid.setStyleSheet("background-color: #9b59b6; color: white;")

        grid.addLayout(p_layout)
        grid.addWidget(self.btn_set_pid)
        layout.addLayout(grid)

        group.setLayout(layout)
        return group

    def _create_connection_group(self):
        """通讯设置区域"""
        group = QGroupBox("通讯设置")
        layout = QHBoxLayout()
        self.ip_input = QLineEdit("192.168.70.129")
        self.btn_connect = QPushButton("连接设备")
        self.btn_connect.setStyleSheet("background-color: #27ae60; color: white;")

        layout.addWidget(QLabel("IP:"))
        layout.addWidget(self.ip_input)
        layout.addWidget(self.btn_connect)
        group.setLayout(layout)
        return group

    def update_log(self, message: str):
        """系统日志打印接口"""
        self.log_area.append(message)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())
```

### File: app\gui\signals.py
```python
# app/gui/signals.py
from PySide6.QtCore import QObject, Signal

class CommSignals(QObject):
    # 当解析出合法的业务数据时触发，传递字典格式的数据
    data_received = Signal(dict)
    # 通讯状态改变信号
    status_changed = Signal(bool, str)

global_signals = CommSignals()
```

### File: app\gui\ui_handlers.py
```python
# app/gui/ui_handlers.py
from PySide6.QtCore import Slot


class UIHandler:
    def __init__(self, window, controller):
        self.window = window
        self.controller = controller

        self.controller.log_triggered.connect(self.window.update_log)

        # 1. 循环绑定 7 组电机信号
        for unit in self.window.motor_units:
            idx = unit['index']
            # 使用 lambda 捕获当前索引 idx
            # 正转按钮
            unit['btn_plus'].pressed.connect(lambda i=idx: self.handle_press(i, True))
            unit['btn_plus'].released.connect(lambda i=idx: self.controller.stop_motor(i))

            # 反转按钮
            unit['btn_minus'].pressed.connect(lambda i=idx: self.handle_press(i, False))
            unit['btn_minus'].released.connect(lambda i=idx: self.controller.stop_motor(i))

            # 速度与模式
            unit['btn_speed'].clicked.connect(lambda _, i=idx, u=unit: self.handle_speed(i, u))
            unit['btn_mode'].clicked.connect(lambda _, i=idx, u=unit: self.handle_mode(i, u))

        # 2. 绑定闭环控制信号
        self.window.btn_send_pos.clicked.connect(self.handle_closed_loop_pos)
        self.window.btn_set_pid.clicked.connect(self.handle_closed_loop_pid)
        self.window.btn_connect.clicked.connect(self.handle_connect)

    def handle_press(self, motor_id, is_forward):
        """按下按钮：先设方向再启动"""
        self.controller.set_motor_direction(motor_id, is_forward)
        self.controller.start_motor(motor_id)

    def handle_speed(self, motor_id, unit):
        try:
            speed = int(unit['speed_in'].text())
            self.controller.set_motor_speed(motor_id, speed)
        except ValueError:
            self.window.update_log(f"[ERR] 电机 {motor_id} 速度输入无效")

    def handle_mode(self, motor_id, unit):
        # 按钮选中状态为闭环(1)，未选中为开环(0)
        is_closed = unit['btn_mode'].isChecked()
        self.controller.set_control_mode(motor_id, is_closed)

    def handle_closed_loop_pos(self):
        try:
            m_id = int(self.window.cl_motor_id.text())
            pos = float(self.window.cl_pos_in.text())
            self.controller.set_motor_angle(m_id, pos)
        except ValueError:
            self.window.update_log("[ERR] 闭环位置输入无效")

    def handle_closed_loop_pid(self):
        try:
            m_id = int(self.window.cl_motor_id.text())
            p = float(self.window.p_in.text())
            i = float(self.window.i_in.text())
            d = float(self.window.d_in.text())
            self.controller.set_motor_pid(m_id, p, i, d)
        except ValueError:
            self.window.update_log("[ERR] PID 参数输入无效")

    def handle_connect(self):
        ip = self.window.ip_input.text()
        self.controller.connect_device(ip)
```

### File: app\gui\__init__.py
```python

```

### File: app\services\comm_handler.py
```python
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
```

### File: app\services\data_processor.py
```python
import struct
from typing import Dict, Any, Optional, Callable

class DataProcessor:
    """
    数据处理器：负责将 29 字节业务载荷解析为结构化数据 。
    采用注册制设计，方便后期动态扩展新指令。
    结构：Ctrl(1B) + Type(1B) + Data(24B) + Reserved(3B) [cite: 280, 293]。
    """

    def __init__(self):
        # 定义解析函数注册表，Key 为功能码 (Type)
        self._parsers: Dict[int, Callable[[bytes, dict], None]] = {
            0x01: self._parse_pid,    # PID 参数类 [cite: 283]
            0x04: self._parse_status, # 状态反馈类 [cite: 285]
            0x31: self._parse_status, # 兼容位置查询响应 [cite: 293]
        }

    def process(self, body: bytes) -> Optional[Dict[str, Any]]:
        """统一入口：解析 29 字节 Body 载荷 """
        if len(body) != 29:
            print(f"[Processor] 长度错误: 期望 29, 实际 {len(body)} [cite: 281]")
            return None

        try:
            # 1. 提取控制信息 [cite: 281]
            # B=uint8, 24s=24字节原始数据
            ctrl, msg_type = struct.unpack("<BB", body[:2])
            data_part = body[2:26] # 提取 24 字节数据区 [cite: 282]

            result = {
                "motor_id": ctrl & 0x7F,     # Bit 0-6 为 ID [cite: 282]
                "is_response": not bool(ctrl & 0x80), # Bit 7 为读写位 [cite: 282]
                "type": msg_type,
                "data": {}
            }

            # 2. 根据功能码分发解析逻辑
            parser_func = self._parsers.get(msg_type)
            if parser_func:
                parser_func(data_part, result["data"])
            else:
                # 默认打印原始十六进制便于分析未知类型 [cite: 288]
                result["data"]["raw_hex"] = data_part.hex(' ')

            return result

        except Exception as e:
            print(f"[Processor] 解析异常: {e}")
            return None

    # --- 具体的业务解析函数 ---

    def _parse_pid(self, data: bytes, out: dict):
        """解析 PID 常用参数 (6个 float) [cite: 284]"""
        p, i, d, i_lim, out_lim, deadzone = struct.unpack("<6f", data)
        out.update({
            "p": p, "i": i, "d": d,
            "i_limit": i_lim, "out_limit": out_lim, "deadzone": deadzone
        })

    def _parse_status(self, data: bytes, out: dict):
        """解析电机状态反馈 (6个 float) [cite: 286]"""
        pos, vel, cur, volt, err, state = struct.unpack("<6f", data)
        out.update({
            "position": pos,
            "velocity": vel,
            "current": cur,
            "voltage": volt,
            "error": int(err),
            "state": int(state)
        })
```

### File: app\services\parser.py
```python
import struct


class FrameParser:
    """
    通用帧管理器：负责 32 字节定长帧的打包(Wrapping)与拆解(Unwrapping)
    结构：Header(2B) + Body(29B) + Checksum(1B) = 32B
    """
    HEADER = b'\x55\xAA'
    FRAME_SIZE = 32
    BODY_SIZE = 29

    @staticmethod
    def wrap(body: bytes) -> bytes:
        """
        给 29 字节的 Body 加上包头和校验和
        """
        if len(body) != FrameParser.BODY_SIZE:
            raise ValueError(f"Body length must be {FrameParser.BODY_SIZE} bytes")

        # 1. 拼接 Header + Body
        packet_pre = FrameParser.HEADER + body

        # 2. 计算 Checksum (前 31 字节累加)
        checksum = sum(packet_pre) & 0xFF

        # 3. 返回完整的 32 字节
        return packet_pre + struct.pack("<B", checksum)

    @staticmethod
    def unwrap(raw_frame: bytes) -> bytes:
        """
        验证帧合法性并剥离出 29 字节的 Body
        """
        if len(raw_frame) != FrameParser.FRAME_SIZE:
            return None

        if raw_frame[:2] != FrameParser.HEADER:
            return None

        if (sum(raw_frame[:-1]) & 0xFF) != raw_frame[-1]:
            # 校验失败
            return None

        # 返回中间 29 字节
        return raw_frame[2:31]
```

### File: app\services\payload_builder.py
```python
# app/services/payload_builder.py
import struct


class PayloadBuilder:
    """
    业务载荷构建器：负责生成 29 字节的 Body 载荷。
    结构：Ctrl(1B) + Type(1B) + Data(24B) + Reserved(3B) = 29 Bytes
    """

    # --- 指令功能码定义 (根据 image_d6c518.png) ---
    CMD_MOTOR_MOVE = 0x11  # 电机开始转动
    CMD_MOTOR_STOP = 0x12  # 电机停止转动
    CMD_MOTOR_DIR = 0x13  # 方向改变 (0:反转, 1:正转)
    CMD_MOTOR_SPEED = 0x14  # 速度改变

    CMD_SET_POS = 0x21  # 设定目标角度
    CMD_SET_PID = 0x22  # 设定 PID 参数

    CMD_CTRL_MODE = 0x31  # 控制模式转换 (0:开环, 1:闭环)

    @staticmethod
    def _build_base(motor_id: int, is_write: bool, type_code: int, data_floats: list) -> bytes:
        """通用构建方法：打包为 B + B + 6f + 3x"""
        ctrl = (0x80 if is_write else 0x00) | (motor_id & 0x7F)
        if len(data_floats) < 6:
            data_floats += [0.0] * (6 - len(data_floats))
        return struct.pack("<BB6f3x", ctrl, type_code, *data_floats[:6])

    # --- 具体的业务调用方法 ---

    @classmethod
    def motor_move(cls, motor_id: int):
        """0x11: 电机开始转动"""
        return cls._build_base(motor_id, True, cls.CMD_MOTOR_MOVE, [])

    @classmethod
    def motor_stop(cls, motor_id: int):
        """0x12: 电机停止转动"""
        return cls._build_base(motor_id, True, cls.CMD_MOTOR_STOP, [])

    @classmethod
    def motor_dir(cls, motor_id: int, direction: int):
        """0x13: 方向改变 (0:反转, 1:正转)"""
        return cls._build_base(motor_id, True, cls.CMD_MOTOR_DIR, [float(direction)])

    @classmethod
    def motor_speed(cls, motor_id: int, speed: int):
        """0x14: 速度改变"""
        return cls._build_base(motor_id, True, cls.CMD_MOTOR_SPEED, [float(speed)])

    @classmethod
    def set_pos(cls, motor_id: int, target_angle: float):
        """0x21: 设定角度目标值"""
        return cls._build_base(motor_id, True, cls.CMD_SET_POS, [target_angle])

    @classmethod
    def set_pid(cls, motor_id: int, p: float, i: float, d: float):
        """0x22: 设定 PID 参数"""
        return cls._build_base(motor_id, True, cls.CMD_SET_PID, [p, i, d])

    @classmethod
    def ctrl_mode(cls, motor_id: int, mode: int):
        """0x31: 控制模式转换 (0:开环, 1:闭环)"""
        return cls._build_base(motor_id, True, cls.CMD_CTRL_MODE, [float(mode)])
```

### File: app\services\__init__.py
```python

```

