"""
MotionProgram：指令式子弹运动系统。

提供一系列运动指令（Wait, SetSpeed, SetAngle, AccelerateTo, TurnTo, AimPlayer）
来控制子弹随时间的运动。

坐标系约定：
- 0° = 右（+X 方向）
- 90° = 下（+Y 方向，因为 Y 轴向下）
- 角度顺时针增加
- 角度归一化到 [-180, 180)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, TYPE_CHECKING

from pygame.math import Vector2

if TYPE_CHECKING:
    pass


# ============================================================
# 角度工具函数
# ============================================================

def normalize_angle(angle: float) -> float:
    """
    将角度归一化到 [-180, 180)。
    
    Args:
        angle: 角度（度）
    
    Returns:
        归一化后的角度，范围 [-180, 180)
    """
    # 先用取模运算归到 [0, 360)，再平移到 [-180, 180)
    angle = angle % 360
    if angle >= 180:
        angle -= 360
    return angle


def shortest_arc(from_angle: float, to_angle: float) -> float:
    """
    计算从 from_angle 到 to_angle 的最短弧角度差。
    
    结果在 [-180, 180) 范围内，表示最短旋转方向和幅度。
    
    Args:
        from_angle: 起始角度（度）
        to_angle: 目标角度（度）
    
    Returns:
        角度差（度），正值 = 顺时针，负值 = 逆时针
    """
    diff = normalize_angle(to_angle - from_angle)
    return diff


def angle_to_vector(angle: float, speed: float) -> Vector2:
    """
    将极坐标 (angle, speed) 转换为速度向量。
    
    坐标系约定：
    - 0° = 右（+X 方向）
    - 90° = 下（+Y 方向）
    - 角度顺时针增加
    
    Args:
        angle: 角度（度）
        speed: 速度（px/s）
    
    Returns:
        速度向量 (px/s)
    """
    rad = math.radians(angle)
    return Vector2(math.cos(rad) * speed, math.sin(rad) * speed)


def vector_to_angle(vec: Vector2) -> float:
    """
    将速度向量转换为角度。
    
    坐标系约定：
    - 0° = 右（+X 方向）
    - 90° = 下（+Y 方向）
    - 角度顺时针增加
    
    Args:
        vec: 速度向量
    
    Returns:
        角度（度），归一化到 [-180, 180)
    """
    return math.degrees(math.atan2(vec.y, vec.x))


# ============================================================
# MotionInstruction 和 MotionProgram
# ============================================================

class MotionInstructionKind(Enum):
    """运动指令类型。"""
    WAIT = auto()           # 等待 N 帧，保持当前速度
    SET_SPEED = auto()      # 立即设置速度 (px/s)
    SET_ANGLE = auto()      # 立即设置角度（度）
    ACCELERATE_TO = auto()  # 在 N 帧内线性变化速度
    TURN_TO = auto()        # 在 N 帧内线性变化角度（最短弧）
    AIM_PLAYER = auto()     # 将角度设置为朝向玩家


@dataclass
class MotionInstruction:
    """
    单条运动指令。
    
    不同指令类型使用不同字段：
    - WAIT: frames
    - SET_SPEED: speed
    - SET_ANGLE: angle
    - ACCELERATE_TO: speed（目标）, frames
    - TURN_TO: angle（目标）, frames
    - AIM_PLAYER:（无参数）
    
    delta_speed 和 delta_angle 字段在指令开始执行时预计算
    （用于 ACCELERATE_TO 和 TURN_TO）。
    """
    kind: MotionInstructionKind
    
    # 参数（使用取决于 kind）
    frames: int = 0           # WAIT, ACCELERATE_TO, TURN_TO
    speed: float = 0.0        # SET_SPEED, ACCELERATE_TO（目标速度 px/s）
    angle: float = 0.0        # SET_ANGLE, TURN_TO（目标角度，度）
    
    # 预计算的每帧增量（指令开始时设置）
    delta_speed: float = 0.0  # ACCELERATE_TO: 每帧速度变化
    delta_angle: float = 0.0  # TURN_TO: 每帧角度变化


@dataclass
class MotionProgram:
    """
    子弹运动指令序列。
    
    包含指令列表、程序计数器 (pc) 和用于定时指令的帧计数器。
    还存储当前运动状态（极坐标形式的 speed 和 angle）。
    
    MotionSystem 每帧解释执行这些指令，
    根据 speed/angle 更新子弹的 Velocity 组件。
    """
    instructions: List[MotionInstruction] = field(default_factory=list)
    pc: int = 0                # 程序计数器（当前指令索引）
    frame_counter: int = 0     # 帧计数器（用于定时指令）
    
    # 当前运动状态（极坐标）
    speed: float = 0.0         # 当前速度 (px/s)
    angle: float = 0.0         # 当前角度（度）
    
    # 执行状态
    finished: bool = False     # 所有指令执行完毕时为 True


# ============================================================
# MotionBuilder（流式 API）
# ============================================================

class MotionBuilder:
    """
    用于构建 MotionProgram 实例的流式构建器。
    
    使用示例：
        motion = (MotionBuilder(speed=100, angle=90)
            .wait(30)
            .accelerate_to(200, 60)
            .aim_player()
            .build())
    """
    
    def __init__(self, speed: float = 0.0, angle: float = 0.0):
        """
        使用初始速度和角度初始化构建器。
        
        Args:
            speed: 初始速度 (px/s)
            angle: 初始角度（度）
        """
        self._initial_speed = speed
        self._initial_angle = angle
        self._instructions: List[MotionInstruction] = []
    
    def wait(self, frames: int) -> "MotionBuilder":
        """
        添加 Wait 指令。
        
        子弹在指定帧数内保持当前速度。
        
        Args:
            frames: 等待帧数
        
        Returns:
            self，用于方法链
        """
        self._instructions.append(MotionInstruction(
            kind=MotionInstructionKind.WAIT,
            frames=frames,
        ))
        return self
    
    def set_speed(self, speed: float) -> "MotionBuilder":
        """
        添加 SetSpeed 指令。
        
        立即设置子弹速度（角度不变）。
        
        Args:
            speed: 目标速度 (px/s)
        
        Returns:
            self，用于方法链
        """
        self._instructions.append(MotionInstruction(
            kind=MotionInstructionKind.SET_SPEED,
            speed=speed,
        ))
        return self
    
    def set_angle(self, angle: float) -> "MotionBuilder":
        """
        添加 SetAngle 指令。
        
        立即设置子弹角度（速度不变）。
        
        Args:
            angle: 目标角度（度）
        
        Returns:
            self，用于方法链
        """
        self._instructions.append(MotionInstruction(
            kind=MotionInstructionKind.SET_ANGLE,
            angle=angle,
        ))
        return self
    
    def accelerate_to(self, target_speed: float, frames: int) -> "MotionBuilder":
        """
        添加 AccelerateTo 指令。
        
        在指定帧数内线性变化速度到目标值。
        
        Args:
            target_speed: 目标速度 (px/s)
            frames: 过渡帧数
        
        Returns:
            self，用于方法链
        """
        self._instructions.append(MotionInstruction(
            kind=MotionInstructionKind.ACCELERATE_TO,
            speed=target_speed,
            frames=frames,
        ))
        return self
    
    def turn_to(self, target_angle: float, frames: int) -> "MotionBuilder":
        """
        添加 TurnTo 指令。
        
        在指定帧数内沿最短弧方向线性变化角度到目标值。
        
        Args:
            target_angle: 目标角度（度）
            frames: 过渡帧数
        
        Returns:
            self，用于方法链
        """
        self._instructions.append(MotionInstruction(
            kind=MotionInstructionKind.TURN_TO,
            angle=target_angle,
            frames=frames,
        ))
        return self
    
    def aim_player(self) -> "MotionBuilder":
        """
        添加 AimPlayer 指令。
        
        将子弹角度设置为朝向玩家当前位置。
        
        Returns:
            self，用于方法链
        """
        self._instructions.append(MotionInstruction(
            kind=MotionInstructionKind.AIM_PLAYER,
        ))
        return self
    
    def build(self) -> MotionProgram:
        """
        构建并返回 MotionProgram。
        
        Returns:
            配置好指令的新 MotionProgram
        """
        return MotionProgram(
            instructions=self._instructions.copy(),
            speed=self._initial_speed,
            angle=self._initial_angle,
        )
