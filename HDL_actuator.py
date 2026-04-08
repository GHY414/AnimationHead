# actuator.py 模块代码（推杆电机，适配Pico的MicroPython）
from machine import PWM, Pin

class Actuator:
    def __init__(self, pin_A, pin_B):
        # 初始化控制引脚
        self.in1 = Pin(pin_A, Pin.OUT)
        self.in2 = Pin(pin_B, Pin.OUT)
        self.stop()  # 默认初始化为断电休眠状态
        
    def out(self):
        """正转：伸出推杆 (对应手册 1, 0)"""
        self.in1.value(1)
        self.in2.value(0)
        
    def back(self):
        """反转：收回推杆 (对应手册 0, 1)"""
        self.in1.value(0)
        self.in2.value(1)
        
    def brake(self):
        """急刹车：电机瞬间锁死停止 (对应手册 1, 1)
        适合在运动中需要精准停下的瞬间调用
        """
        self.in1.value(1)
        self.in2.value(1)

    def stop(self):
        """断电滑行并休眠：失去动力 (对应手册 0, 0)
        1ms 后驱动芯片进入低功耗待机模式，适合长时间不用时调用
        """
        self.in1.value(0)
        self.in2.value(0)
