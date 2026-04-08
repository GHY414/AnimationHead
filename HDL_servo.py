# servo.py 模块代码（通用版，适配Pico的MicroPython）
from machine import PWM, Pin
import time
import math
class Servo:
    def __init__(self, pin_id, limits=None, freq=50, min_us=500, max_us=2500, angle_range=180,direction=1):
        """
        初始化舵机
        :param pin_id: 舵机信号线连接的GPIO引脚号（如4、5等）
        :param limits: 舵机的活动范围元组 (start_angle, end_angle)，供 step 自动扫描使用。如果不传则默认为 (0, angle_range)
        :param freq: 舵机工作频率（默认50Hz，绝大多数舵机通用）
        :param min_us: 最小脉冲宽度（对应0°，默认500μs，部分舵机需调整为600μs）
        :param max_us: 最大脉冲宽度（对应180°，默认2500μs，部分舵机需调整为2400μs）
        :param angle_range: 舵机总转动角度（默认180°，部分舵机为270°）
        """
        
        self.min_us = min_us
        self.max_us = max_us
        self.angle_range = angle_range

        self.pwm = PWM(Pin(pin_id))
        self.pwm.freq(freq)
        self.direction = direction  # 初始方向
        
        if limits is None:
            self.start, self.end = (0, angle_range)
        else:
            self.start, self.end = limits
        #如果start>end,交换start和end
        if self.start > self.end:
            self.start, self.end = self.end, self.start
        
        
        self.angle = self.start
        self.target_angle = self.start  # 目标角度缓存，用于平滑过渡

         # === 新增：用于时间驱动动画的状态变量 ===
        self.anim_start_angle = self.start  # 动画开始时的角度
        self.anim_start_time = 0            # 动画开始的时间戳
        self.anim_duration = 0              # 动画持续时间
        
        
        # 预计算常量，优化执行效率
        us_to_duty = 65535 * freq / 1000000
        self.min_duty = min_us * us_to_duty
        self.duty_per_angle = (max_us - min_us) * us_to_duty / angle_range

    def SetAngle(self, angle):
        """
        限制幅度并且输出角度。如果 direction == -1，则会自动反转输出角度。
        :param angle: 目标角度（逻辑角度）
        """
        # 注意：这里我们限制逻辑角度
        self.angle = max(self.start, min(angle, self.end))
        
        # 判断是否需要翻转真实的物理输出角度
        actual_angle = self.angle
        if self.direction == -1:
            actual_angle = self.angle_range - self.angle

        # 直接利用预计算的系数计算并输出 duty 占空比
        self.pwm.duty_u16(int(self.min_duty + actual_angle * self.duty_per_angle))

    def SetTarget(self, angle, duration_ms=0):
        """
        设定目标角度，并记录起始状态供 update 使用
        :param angle: 目标角度
        :param duration_ms: 动作预计耗时(毫秒)。如果为0，代表瞬间到达。
        """
        target = max(self.start, min(angle, self.end))
        
        # 如果目标发生变化，或者要求重新开始动画
        if target != self.target_angle or duration_ms > 0:
            self.target_angle = target
            self.anim_start_angle = self.angle         # 记录当前角度作为动画起点
            self.anim_start_time = time.ticks_ms()     # 记录当前时间戳
            self.anim_duration = duration_ms           # 记录总耗时

    # ==========================================
    # 方式一：线性匀速过渡 (按 duration_ms)
    # ==========================================
    def update_linear(self):
        """在主循环中调用，根据设定的 duration_ms 匀速直线逼近目标"""
        if self.angle == self.target_angle:
            return

        if self.anim_duration <= 0:
            # 没有设定时间，直接瞬间到达
            self.SetAngle(self.target_angle)
            return

        # 计算已流逝的时间
        elapsed = time.ticks_diff(time.ticks_ms(), self.anim_start_time)
        
        if elapsed >= self.anim_duration:
            # 时间到，锁定到目标角度
            self.SetAngle(self.target_angle)
        else:
            # 计算当前进度百分比 (0.0 ~ 1.0)
            progress = elapsed / self.anim_duration
            new_angle = self.anim_start_angle + (self.target_angle - self.anim_start_angle) * progress
            self.SetAngle(new_angle)

    # ==========================================
    # 方式二：正弦平滑缓动 (Ease-in-out Sine)
    # ==========================================
    def update_sine(self):
        """在主循环中调用，采用正弦曲线（慢起步->快加速->慢停止）逼近目标"""
        if self.angle == self.target_angle:
            return

        if self.anim_duration <= 0:
            self.SetAngle(self.target_angle)
            return

        elapsed = time.ticks_diff(time.ticks_ms(), self.anim_start_time)
        
        if elapsed >= self.anim_duration:
            self.SetAngle(self.target_angle)
        else:
            # 1. 计算线性进度 (0.0 ~ 1.0)
            t = elapsed / self.anim_duration
            # 2. 转换为正弦缓动进度 (0.0 ~ 1.0)，呈现S型曲线
            eased_t = -(math.cos(math.pi * t) - 1) / 2
            # 3. 计算实际角度
            new_angle = self.anim_start_angle + (self.target_angle - self.anim_start_angle) * eased_t
            self.SetAngle(new_angle)
