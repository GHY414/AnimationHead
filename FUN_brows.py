from HDL_servo import Servo

class Brows:
    def __init__(self):
        self.servos = {
            'LEFT_Brow_L': Servo(pin_id=8, limits=(80, 100)),
            'LEFT_Brow_R': Servo(pin_id=9, limits=(80, 100)),
            'RIGHT_Brow_L': Servo(pin_id=13, limits=(80, 100)),
            'RIGHT_Brow_R': Servo(pin_id=12, limits=(80, 100))
        }
        
        self.poses = {
            'Down': {'LEFT_Brow_L': 80, 'LEFT_Brow_R': 100, 'RIGHT_Brow_L': 80, 'RIGHT_Brow_R': 100},
            'Up': {'LEFT_Brow_L': 120, 'LEFT_Brow_R': 60, 'RIGHT_Brow_L': 120, 'RIGHT_Brow_R': 60},
            'Neutral': {'LEFT_Brow_L': 90, 'LEFT_Brow_R': 90, 'RIGHT_Brow_L': 90, 'RIGHT_Brow_R': 90},
            'Angry': {'LEFT_Brow_L': 80, 'LEFT_Brow_R': 60, 'RIGHT_Brow_L': 80, 'RIGHT_Brow_R': 60},
            'Sad': {'LEFT_Brow_L': 120, 'LEFT_Brow_R': 100, 'RIGHT_Brow_L': 120, 'RIGHT_Brow_R': 100},
            'Confused': {'LEFT_Brow_L': 120, 'LEFT_Brow_R': 60, 'RIGHT_Brow_L': 80, 'RIGHT_Brow_R': 100}
        }

    def set_pose(self, pose_name):
        if pose_name in self.poses:
            for name, angle in self.poses[pose_name].items():
                if name in self.servos:
                    self.servos[name].SetTarget(angle)
        else:
            print(f'[Brows] Pose {pose_name} not found!')

    def reset(self):
        for s in self.servos.values():
            s.SetTarget(90)

    def update_all(self, easing_factor=0.15):
        for s in self.servos.values():
            s.update_sine()
