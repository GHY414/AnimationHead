from machine import UART, Pin
import uasyncio as asyncio
import time

class Vofa:
    def __init__(self, tx_pin=12, rx_pin=13, baudrate=115200):
        """
        初始化 VOFA+ 通信类，接管对应 UART 通道
        """
        self.tx_pin = tx_pin
        self.rx_pin = rx_pin
        self.baudrate = baudrate
        self.uart = UART(0, baudrate=self.baudrate, tx=Pin(self.tx_pin), rx=Pin(self.rx_pin))
        self.buffer = ""
        self.last_cmd_time = time.ticks_ms() - 10000  # 初始置为过去的时间

    def send(self, msg):
        """
        串口发送数据
        """
        self.uart.write((str(msg) + "\r\n").encode('utf-8'))

    async def rx_task(self, servos):
        """
        异步非阻塞接收串口数据，并解析 VOFA+ 下发的多指令
        指令格式示例：LBL90.5,500# （其中500代表过渡时间ms，可省略逗号和时间）
        """
        while True:
            if self.uart.any() > 0:
                raw_data = self.uart.read()
                if raw_data:
                    try:
                        chars = raw_data.decode('utf-8')
                    except UnicodeError:
                        continue
                    for char in chars:
                        self.buffer += char
                        
                        # 假设 VOFA+ 配置的结束符是 '#'
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
                                    
                                    servos[found_cmd].SetTarget(angle, duration_ms=duration_ms)  # 设置目标角度，持续时间由串口决定
                                    self.last_cmd_time = time.ticks_ms()  # 记录最近一次接收到有效指令的时间
                                    
                                    # 打印各个舵机的当前角度
                                    status_list = [f'"{k}": {v.angle:.1f}' for k, v in servos.items()]
                                    self.send("NowAngle_Servos: " + ", ".join(status_list))
                                except ValueError as e:
                                    self.send(f"转换错误: 指令 {found_cmd} 收到 '{val_str}', 错误: {e}")
                            else:
                                self.send(f"未找到已知包头，当前 buffer: {self.buffer}")
                            
                            self.buffer = ""
            
            if len(self.buffer) > 128:
                self.buffer = ""
                
            await asyncio.sleep_ms(5)
