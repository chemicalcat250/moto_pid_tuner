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