from machine import UART, Pin
import uasyncio as asyncio

class Ras4B:
    def __init__(self, tx_pin=4, rx_pin=5, baudrate=115200):
        """
        初始化 树莓派4B 通信类，接管对应 UART 通道
        """
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin
        self.baudrate = baudrate
        # 使用 UART 1，tx=4, rx=5
        self.uart = UART(1, baudrate=self.baudrate, tx=Pin(self.tx_pin), rx=Pin(self.rx_pin))
        self.buffer = ""
        self.last_cmd_time = 0  # 记录上一次接收到有效指令的时间戳

    def send(self, msg):
        """
        串口发送数据
        """
        self.uart.write((str(msg) + "\r\n").encode('utf-8'))

    async def rx_task(self, servos):
        """
        异步非阻塞接收串口数据，并解析树莓派下发的多指令
        这里沿用了与 VOFA 类似的指令格式示例：LBL90.5#，你可以根据需要自行修改通信协议
        """
        while True:
            if self.uart.any() > 0:
                raw_data = self.uart.read()
                self.send(f"raw_data: {raw_data}")  # 可选：调试时查看原始数据
                if raw_data:
                    chars = raw_data.decode('utf-8', 'ignore')
                    for char in chars:
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
                                    angle = float(val_str)
                                    import time
                                    self.last_cmd_time = time.ticks_ms() # 刷新最新收到指令的时间
                                    
                                    # 假设 servos 对象实现了 SetTarget
                                    servos[found_cmd].SetTarget(angle, duration_ms=0)
                                    
                                    # 这个打印可选，用于调试反馈
                                    status_list = [f"{k}:{v.angle:.1f}" for k, v in servos.items()]
                                    self.send("收到树莓派指令 | 各舵机当前角度: " + " | ".join(status_list))
                                except Exception as e:
                                    self.send(f"树莓派指令处理异常: 指令 {found_cmd} 收到 '{val_str}', 错误: {e}")
                            else:
                                self.send(f"未找到已知包头，当前 buffer: {self.buffer}")
                            
                            self.buffer = ""
            
            if len(self.buffer) > 128:
                self.buffer = ""
                
            await asyncio.sleep_ms(5)
