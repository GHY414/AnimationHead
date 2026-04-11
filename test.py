import time
from machine import Pin
from HDL_actuator import Actuator
#初始点亮pico25引脚的LED

# 初始化推杆电机对象，控制引脚为 17 和 16
my_actuator = Actuator(17, 16)

def test_actuator():
    print("=== 开始测试推杆电机 (使用 HDL_actuator 库) ===")
    my_actuator.stop()  # 初始保护，进入休眠
    time.sleep(1)
    
    print("电机伸出 2 秒...")
    my_actuator.out()
    time.sleep(2)
    my_actuator.stop()
    print("电机停止")
    time.sleep(1)
    
    print("电机收回 2 秒...")
    my_actuator.back()
    time.sleep(2)
    my_actuator.stop()
    print("电机停止")
    time.sleep(1)
    
    print("=== 测试结束 ===")

if __name__ == "__main__":
    try:
        while True:
            test_actuator()
    except KeyboardInterrupt:
        # 遇Ctrl+C强制停止，防止危险
        my_actuator.stop()
        print("\n已强制中止程序并断电休眠电机")

