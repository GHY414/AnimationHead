import uasyncio as asyncio
import sys
import uselect
import time

class Ras4B:
    def __init__(self):
        """
        初始化 树莓派4B 通信类，通过 USB CDC (标准输入输出) 接收数据
        """
        self.buffer = ""
        self.last_cmd_time = time.ticks_ms() - 10000  # 记录上一次接收到有效指令的时间戳
        
        # 注册 poll 监听 sys.stdin 做到非阻塞读取
        self.poller = uselect.poll()
        self.poller.register(sys.stdin, uselect.POLLIN)

    def send(self, msg):
        """
        通过 USB CDC发送数据，由于是USB直接使用print即可
        """
        print(msg)

    async def rx_task(self, servos):
        """
        异步非阻塞接收USB数据，并解析树莓派下发的多指令
        指令格式示例：LBL90.5,500# （其中500代表过渡时间ms）
        """
        while True:
            if self.poller.poll(0):
                # 读取全部缓冲区的字符
                try:
                    char = sys.stdin.read(1)
                except UnicodeError:
                    # 忽略不合法的 UTF-8 字符/乱码引起的异常
                    continue
                except Exception as e:
                    print(f"USB Read Error: {e}")
                    continue

                if char:
                    self.buffer += char
                    
                    # 假设配置的结束符是 '#'
                    if char == '#':  
                        found_cmd = ""
                        start_idx = -1
                        # 遍历查找包头
                        for cmd in servos.keys():
                            idx = self.buffer.rfind(cmd)
                            if idx > start_idx:
                                start_idx = idx
                                found_cmd = cmd

                        if start_idx != -1:
                            val_str = self.buffer[start_idx+len(found_cmd) : -1]
                            try:
                                val_parts = val_str.split(',')
                                angle = float(val_parts[0])
                                duration_ms = int(val_parts[1]) if len(val_parts) > 1 else 0
                                
                                self.last_cmd_time = time.ticks_ms() # 刷新最新收到指令的时间
                                
                                servos[found_cmd].SetTarget(angle, duration_ms=duration_ms)
                                
                                # 这个打印可选，用于调试反馈
                                status_list = [f"{k}:{v.angle:.1f}" for k, v in servos.items()]
                                self.send("收到树莓派指令 | 各舵机当前角度: " + " | ".join(status_list))
                            except Exception as e:
                                self.send(f"树莓派指令处理异常: 指令 {found_cmd} 收到 '{val_str}', 错误: {e}")
                        else:
                            self.send(f"未找到已知包头，当前 buffer: {self.buffer}")
                        
                        self.buffer = ""
            else:
                # 让出 CPU 给其他协程
                await asyncio.sleep_ms(5)
            
            if len(self.buffer) > 128:
                self.buffer = ""
