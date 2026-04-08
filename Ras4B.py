import serial
import time
import threading

# 预设的表情字典
# 现在支持统一默认 duration，也支持分别指定某个舵机的 (angle, duration)
expressions = {
    "happy": {
        "default_duration": 500,  # 该表情的默认全局过渡时间 (毫秒)
        "servos": {
            # 如果只写数字，则使用 default_duration
            # 如果需要单独指定某个舵机的运动时间，就用元组或者列表: (角度, 毫秒)
            "LEL": (92.0, 300), "MLO": (20.0, 800), "JR": 90.0, "MRI": 20.0,
            "CR": 96.0, "MRO": 20.0, "JL": 91.0, "LBL": 90.0,
            "RBR": 95.0, "LBR": 102.0, "RBL": 89.0, "LEU": 35.0,
            "REU": 118.0, "CL": 100.0, "REL": 88.0, "MLI": 20.0
        }
    },
    "sad": {
        "default_duration": 800,  # 悲伤动作可能整体更缓慢
        "servos": {
            # 同样支持单独重写
            # "LBL": (60.0, 1200), "LBR": 120.0, ... 
        }
    }
}

class Ras4B_Host:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        """
        初始化上位机串口通信
        注意：Linux/树莓派下 port 通常是 '/dev/ttyUSB0' 或 '/dev/serial0'
              Windows下就是 'COM1', 'COM3' 等
        """
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            print(f"成功连接串口: {port}")
            
            # 开启个子线程持续接收下位机(Pico)的返回数据，方便调试
            self.rx_thread = threading.Thread(target=self.receive_loop, daemon=True)
            self.rx_thread.start()
        except Exception as e:
            print(f"串口打开失败: {e}")
            self.ser = None

    def receive_loop(self):
        """循环接收下位机打印的信息"""
        while self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    raw_data = self.ser.readline()
                    print(f"[Pico 返回] {raw_data.decode('utf-8', 'ignore').strip()}")
            except Exception:
                break
            time.sleep(0.01)

    def send_cmd(self, cmd_str):
        """底层方法：直接发送字符串命令"""
        if self.ser and self.ser.is_open:
            self.ser.write((cmd_str + '\n').encode('utf-8'))
            time.sleep(0.005) # 防止发太快单片机处理不过来

    def send_expression(self, expr_name):
        """发送指定的表情字典数据到单片机"""
        if expr_name not in expressions:
            print(f"找不到表情: {expr_name}")
            return
        
        print(f"正在发送表情: {expr_name} ...")
        expr_data = expressions[expr_name]
        default_duration = expr_data.get("default_duration", 500)
        servos_data = expr_data.get("servos", {})
        
        # 遍历该表情下的所有舵机，处理时间合并并拼接命令发送
        # 格式为：包头 + 角度 + , + 持续时间 + #
        for servo_name, value in servos_data.items():
            # 检查是否有单独指定时长，例如 value 是 tuple 或 list -> (angle, duration)
            if isinstance(value, (list, tuple)):
                angle = float(value[0])
                duration = int(value[1])
            else:
                angle = float(value)
                duration = default_duration
                
            # 生成类似 "LBL90.0,500#" 的字符串
            command = f"{servo_name}{angle},{duration}#"
            self.send_cmd(command)
        
        print("发送完成！")

if __name__ == "__main__":
    # 使用前请根据实际情况修改串口号（树莓派可能是 /dev/ttyS0 或 /dev/ttyUSB0）
    host = Ras4B_Host(port='/dev/ttyUSB0', baudrate=115200)
    
    if host.ser is not None:
        time.sleep(2) # 等待下位机复位/初始化完毕
        
        print("========== 树莓派上位机控制端 ==========")
        print("输入表情名称 (如 'happy', 'sad') 发送给 Pico")
        print("输入 'q' 退出程序")
        print("========================================")
        
        while True:
            cmd = input("请输入表情指令: ").strip()
            if cmd.lower() == 'q':
                break
            elif cmd:
                host.send_expression(cmd)
                
        host.ser.close()
        print("串口已关闭。")