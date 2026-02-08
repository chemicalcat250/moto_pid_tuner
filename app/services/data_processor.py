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
            0x41: self._parse_multi_response,
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

    def _parse_multi_response(self, data: bytes, out: dict):
        """解析多机同步控制的回传数据 (根据硬件设计而定)"""
        # 假设硬件回传当前生效的掩码和速度作为确认
        sel_mask, dir_mask, speed = struct.unpack("<fff", data[:12])
        out.update({
            "applied_selection": int(sel_mask),
            "applied_direction": int(dir_mask),
            "current_speed": speed
        })