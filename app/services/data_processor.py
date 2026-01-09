import struct
from typing import Dict, Any, Optional

class DataProcessor:
    """
    数据处理器：负责将 29 字节的业务载荷解析为结构化数据。
    """

    # 对应协议中的 Type 定义
    TYPE_PID = 0x01
    TYPE_MOTION = 0x02
    TYPE_ADVANCED = 0x03
    TYPE_STATUS = 0x04
    TYPE_SYSTEM = 0xFF

    def process(self, body: bytes) -> Optional[Dict[str, Any]]:
        """
        统一入口方法：解析 29 字节的 Body 载荷
        结构：Ctrl(1B) + Type(1B) + Data(24B) + Reserved(3B)
        """
        if len(body) != 29:
            print(f"[Processor] 长度错误: 期望 29, 实际 {len(body)}")
            return None

        try:
            # 1. 提取基本信息
            # B=uint8, 24s=24字节原始数据
            ctrl, msg_type = struct.unpack("<BB", body[:2])
            data_part = body[2:26]

            motor_id = ctrl & 0x7F
            is_write = bool(ctrl & 0x80)

            result = {
                "motor_id": motor_id,
                "type": msg_type,
                "is_response": not is_write,
                "data": {}
            }

            # 2. 根据 Type 进行解析
            if msg_type == DataProcessor.TYPE_PID:
                # 解析 PID 常用参数 (6个float)
                p, i, d, i_lim, out_lim, deadzone = struct.unpack("<6f", data_part)
                result["data"] = {
                    "p": p, "i": i, "d": d,
                    "i_limit": i_lim, "out_limit": out_lim, "deadzone": deadzone
                }
                # 打印解析结果用于调试
                print(f"[Processor] 解析到 PID -> ID:{motor_id} P:{p} I:{i}")

            elif msg_type == DataProcessor.TYPE_STATUS or msg_type == 0x01:
                # 这里兼容你从机测试程序里的 0x01
                # 解析状态信息 (6个float)
                pos, vel, cur, volt, err_code, state = struct.unpack("<6f", data_part)
                result["data"] = {
                    "position": pos,
                    "velocity": vel,
                    "current": cur,
                    "voltage": volt,
                    "error": int(err_code),
                    "state": int(state)
                }
                print(f"[Processor] 解析到状态 -> ID:{motor_id} Pos:{pos:.2f} Vel:{vel:.2f}")

            else:
                # 默认打印原始十六进制，便于分析未定义类型
                print(f"[Processor] 收到未知类型 {hex(msg_type)} | Raw: {body.hex(' ')}")

            return result

        except Exception as e:
            print(f"[Processor] 解析出错: {e}")
            return None