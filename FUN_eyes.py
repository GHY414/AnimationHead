from HDL_servo import Servo
import random

class Eyes:
    def __init__(self):
        self.servos = {
            'LEFT_Eye_L': Servo(pin_id=10, limits=(40, 140)),
            'LEFT_Eye_R': Servo(pin_id=11, limits=(40, 140)),
            'RIGHT_Eye_L': Servo(pin_id=12, limits=(40, 140)),
            'RIGHT_Eye_R': Servo(pin_id=13, limits=(40, 140)),
        }
        
        self.poses = {
            'Center': {'LEFT_Eye_L': 90, 'LEFT_Eye_R': 90, 'RIGHT_Eye_L': 90, 'RIGHT_Eye_R': 90}
        }

    def set_pose(self, pose_name):
        if pose_name in self.poses:
            for name, angle in self.poses[pose_name].items():
                if name in self.servos:
                    self.servos[name].SetTarget(angle)
        else:
            print(f'[Eyes] Pose {pose_name} not found!')

    def reset(self):
        for servo in self.servos.values():
            servo.SetTarget(90)

    def move_random(self):
        for servo_name, limits in self.servos.items():
            angle = random.randint(limits.start, limits.end)
            self.servos[servo_name].SetTarget(angle)

    def update_all(self, easing_factor=0.15):
        for s in self.servos.values():
            s.update_sine()
