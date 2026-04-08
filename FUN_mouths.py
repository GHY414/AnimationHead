from HDL_servo import Servo
import random
import time

class Mouth:
    def __init__(self):
        self.servos = {
            'Mouth_L': Servo(pin_id=4, limits=(50, 90)),
            'Mouth_R': Servo(pin_id=5, limits=(90, 130)),
            'Mouth_UP': Servo(pin_id=6, limits=(80, 100)),
            'Mouth_Down': Servo(pin_id=7, limits=(80, 100)),
            'Jaw_L': Servo(pin_id=8, limits=(10, 170)),
            'Jaw_R': Servo(pin_id=9, limits=(80, 100))
        }
        
        self.poses = {
            'mouth_closed': {'Jaw_L': 90, 'Jaw_R': 90, 'Mouth_L': 90, 'Mouth_R': 90},
            'mouth_open': {'Jaw_L': 60, 'Jaw_R': 120, 'Mouth_L': 70, 'Mouth_R': 110}
        }
        self.is_talking = False
        self.last_talk_time = 0

    def set_pose(self, pose_name):
        if pose_name in self.poses:
            for servo_name, angle in self.poses[pose_name].items():
                if servo_name in self.servos:
                    self.servos[servo_name].SetTarget(angle)
        else:
            print(f'[Mouth] Pose {pose_name} not found!')

    def reset(self):
        for s in self.servos.values():
            s.SetTarget(90)
            
    def set_talking(self, state):
        self.is_talking = state
        if not state:
            self.set_pose('mouth_closed')

    def random_talk(self):
        # 随机生成说话时的下巴开合角度
        jaw_angle_l = random.randint(50, 90)
        jaw_angle_r = 180 - jaw_angle_l # 假设左右对称相反设计
        if 'Jaw_L' in self.servos:
            self.servos['Jaw_L'].SetTarget(jaw_angle_l)
        if 'Jaw_R' in self.servos:
            self.servos['Jaw_R'].SetTarget(jaw_angle_r)

    def update_all(self, easing_factor=0.15):
        # 如果处于说话状态，定时切换嘴巴张合度以模拟说话
        if self.is_talking:
            current_time = time.ticks_ms() if hasattr(time, 'ticks_ms') else time.time() * 1000
            if current_time - self.last_talk_time > 150: # 每150ms变换一次开合度
                self.random_talk()
                self.last_talk_time = current_time

        for s in self.servos.values():
            s.update_sine()
