# app/gui/signals.py
from PySide6.QtCore import QObject, Signal

class CommSignals(QObject):
    # 当解析出合法的业务数据时触发，传递字典格式的数据
    data_received = Signal(dict)
    # 通讯状态改变信号
    status_changed = Signal(bool, str)

global_signals = CommSignals()