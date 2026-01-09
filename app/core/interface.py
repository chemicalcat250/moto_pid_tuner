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