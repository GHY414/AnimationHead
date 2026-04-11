from HDL_servo import Servo
from HDL_vofa import Vofa
from HDL_Ras4B import Ras4B
import uasyncio as asyncio
import time
import sys
import random
from machine import Pin
from HDL_actuator import Actuator
actuator = Actuator(21, 20)
# 实例化 VOFA 串口通信对象
vofa = Vofa(tx_pin=0, rx_pin=1, baudrate=115200)

# 实例化 树莓派4B USB通信对象
ras4b = Ras4B()

servos = {
    # 眉毛 (限制角度 50~120)
    "LBL": Servo(pin_id=16, limits=(75, 160)),
    "LBR": Servo(pin_id=2, limits=(20, 180), direction=-1),
    
    "RBL": Servo(pin_id=3, limits=(85, 125),direction=-1),
    "RBR": Servo(pin_id=17, limits=(75, 160), direction=-1),
    
    # 眼睛 (默认初始化)
    "LEU": Servo(pin_id=14,limits=(75,105)),
    "LEL": Servo(pin_id=7,limits=(75,105),direction=-1),
    "REU": Servo(pin_id=15,limits=(75,105),direction=-1),
    "REL": Servo(pin_id=11,limits=(75,105),direction=-1),
    
    # 嘴部和下巴 (限制角度 20~180, 方向翻转)
    "CL":  Servo(pin_id=8, limits=(86, 102), direction=-1),
    "CR":  Servo(pin_id=9, limits=(80, 93),direction=-1),

    "MRI":  Servo(pin_id=26, limits=(100, 135), direction=1),
    "MRO":  Servo(pin_id=10, limits=(100, 135), direction=1),
    "MLI":  Servo(pin_id=22, limits=(100, 135), direction=-1),
    "MLO":  Servo(pin_id=6, limits=(100, 135), direction=-1),

    

    "JL":  Servo(pin_id=12, limits=(60, 105), direction=-1),
    "JR":  Servo(pin_id=13, limits=(60, 100))
}

def reset_to_center(duration_ms=1000):
    """
    统一归中函数
    将所有参与动作的舵机平滑过渡回默认中立原定坐标
    :param duration_ms: 归中过程花费的过渡时间(毫秒)
    """

    servos["LBL"].SetTarget(90, duration_ms)
    servos["LBR"].SetTarget(90, duration_ms)
    servos["RBL"].SetTarget(90, duration_ms)
 
    servos["LEU"].SetTarget(90, duration_ms)
    servos["LEL"].SetTarget(90, duration_ms)
    servos["REU"].SetTarget(90, duration_ms)
    servos["REL"].SetTarget(90, duration_ms)
  
    servos["CL"].SetTarget(90, duration_ms)
    servos["CR"].SetTarget(90, duration_ms)
    servos["MLI"].SetTarget(90, duration_ms)
    servos["MLO"].SetTarget(90, duration_ms)
    servos["MRI"].SetTarget(90, duration_ms)
    servos["MRO"].SetTarget(90, duration_ms)
    servos["JL"].SetTarget(90, duration_ms)
    servos["JR"].SetTarget(90, duration_ms)


vofa.send("初始化完成，请将发送格式设置为: [舵机名称][角度],[持续时间]#")
vofa.send("例如左眉毛左边的舵机,发送: LBL90.5#或LBL90.5,1000#")

# ======= 1. 舵机平滑更新协程 (模拟 50FPS 刷新) =======
async def servo_update_task():
    """以协程方式每 20ms 刷新一次所有舵机的位置 (Easing)"""
    while True:
        for s in servos.values():
            s.update_sine()
        await asyncio.sleep_ms(20)  # 挂起自身 20ms，把 CPU 交给其他协程



# ======= 2. 待机仿生动作协程 (测试 AI/随机动作示例) =======
async def idle_animation_task():
    """
    没有上位机数据时，循环执行固定表情。一旦收到串口指令则让出控制权，
    直到每个舵机都达到指令角度3秒后，归中,再恢复循环执行固定表情
    """
    # 状态标记：当前是否处于待机(无主控制)循环中
    is_idle_mode = False
    
    while True:
        try:
            # ================= 1. 检查各舵机是否到达目标状态 =================
            all_reached = True
            for s in servos.values():
                # 如果当前角度离目标角度差距大于 1.0度，说明舵机还在朝目标角度赶去
                if abs(s.angle - s.target_angle) > 1.0:
                    all_reached = False
                    break
                    
            # 距离上位机最后一次下发命令过了多久
            last_cmd_time = max(vofa.last_cmd_time, ras4b.last_cmd_time)
            elapsed_since_cmd = time.ticks_diff(time.ticks_ms(), last_cmd_time)
            
            # ================= 2. 串口处于高频控制期间 =================
            # 只要上位机还在持续发数据(如不到1秒前刚发过)，或者舵机还在朝上位机位置运动，就挂起不干预
            if elapsed_since_cmd < 1000 or not all_reached:
                is_idle_mode = False       # 打断待机
                await asyncio.sleep(0.1)   # 继续交出使用权，给舵机运转的时间
                continue
                
            # ================= 3. 当舵机全都在目标位上，且停顿了一小会 =================
            if not is_idle_mode and all_reached:
                # 这说明上位机刚刚停发指令，并且脸部动作停稳了。现在我们要它在原地停留 3 秒
                interrupted = False
                # 利用 15次 * 0.1秒 = 1.5秒 的分片休眠法，期间如果突然又来串口指令了，可以极速打破这个 3 秒等待
                for _ in range(15):
                    await asyncio.sleep(0.1)
                    if time.ticks_diff(time.ticks_ms(), max(vofa.last_cmd_time, ras4b.last_cmd_time)) < 1000:
                        interrupted = True
                        break
                        
                if interrupted:
                    continue  # 被新指令打断，退出尝试，交还控制权

                # ✅ 经历了漫长的等待和 3秒 的观察期，确认外界没有指令，正式全自动“归中”
                vofa.send("[Idle_Mode] 长时间无新指令，各舵机进入待机归中还原...")
                
                # 开始为各个特征区域设定平滑的自动归中命令，例如花 1 秒钟统一回到基准0位
                reset_to_center(1000)
                
                await asyncio.sleep(1.0) # 耐心等待 1.0 秒让身体完成上面设定的 1.0 秒归中动作
                
                # 宣布正式进入无人接管的待机动画(固定动作)死循环环节
                is_idle_mode = True
                continue

            # ================= 4. 无人接管时，循环执行固定表情 =================
            if is_idle_mode:
                # 产生微小的随机扰动 (模拟真实的眼球跳视)
                UandD_eye_offset = random.uniform(-10, 10)
                RandL_eye_offset = random.uniform(-10, 10)
                Brow_offset = random.uniform(-15, 15)
                Cheek_offset = random.uniform(-5, 5)
                
                # 快速且平滑地移动过去
                move_time = random.randint(500, 700)
                servos["LBL"].SetTarget(100 + Brow_offset, duration_ms=move_time)
                servos["LBR"].SetTarget(105 - Brow_offset, duration_ms=move_time)
                servos["RBL"].SetTarget(100 - Brow_offset, duration_ms=move_time)
                servos["RBR"].SetTarget(100 + Brow_offset, duration_ms=move_time)

                servos["LEL"].SetTarget(90 + RandL_eye_offset, duration_ms=move_time)
                servos["REL"].SetTarget(90 + RandL_eye_offset, duration_ms=move_time)
                servos["LEU"].SetTarget(90 + UandD_eye_offset, duration_ms=move_time)
                servos["REU"].SetTarget(90 + UandD_eye_offset, duration_ms=move_time)
                
                # 停顿一段随机时间 (500~1500ms)
                # 使用分片休眠响应串口指令进行极速打断
                pause_time = random.randint(500, 1500)
                sleep_steps = max(1, pause_time // 100)
                for _ in range(sleep_steps):
                    await asyncio.sleep(0.1)
                    if time.ticks_diff(time.ticks_ms(), max(vofa.last_cmd_time, ras4b.last_cmd_time)) < 1000:
                        is_idle_mode = False # 一旦被打断，立刻解除待机状态并进入下一次主循环
                        break
                        
        except Exception as e:
            # 防止任务崩溃死锁导致系统瘫痪
            print("Idle task error:", e)
            await asyncio.sleep(1)


# ======= 3. 主事件循环调度器 =======
async def main():
    # 将所有的独立任务丢入 uasyncio 的事件循环池（它们会自动轮流穿插运行）
    asyncio.create_task(servo_update_task())
    
    # 程序刚开始时，让所有特定舵机统一归位到指定中立角度
    #reset_to_center(1000)
        
    asyncio.create_task(vofa.rx_task(servos)) # 挂载 VOFA 的串口接收协程
    asyncio.create_task(ras4b.rx_task(servos)) # 挂载 树莓派 USB 的接收协程
    asyncio.create_task(idle_animation_task())
    
    vofa.send("uasyncio 事件循环已启动！")
    
    # 保持主程序存活并运行其它高级逻辑
    while True:
        await asyncio.sleep(1)

try:
    # MicroPython 入口标准动作：启动异步事件循环
    asyncio.run(main())
except KeyboardInterrupt:
    vofa.send("\n程序已终止。")