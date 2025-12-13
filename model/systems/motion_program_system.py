# model/systems/motion_program_system.py
"""
MotionProgram 系统：解释执行子弹运动指令。

此系统处理带有 MotionProgram 组件的子弹，执行运动指令
（Wait, SetSpeed, SetAngle, AccelerateTo, TurnTo, AimPlayer）
并相应更新它们的 Velocity 组件。

执行顺序：此系统在 movement_system 之前运行，
使速度变化在同一帧内生效。

**Requirements 14.3**: 优化以避免每帧创建新对象：
- 原地更新 Velocity.vec 而非创建新 Vector2
- 使用 math 模块直接计算，避免预计算 sin/cos 查找表
- 使用 if-elif 链进行指令分发
- 模块级导入避免每次调用的导入开销
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable, Dict

from pygame.math import Vector2

from ..components import Position, Velocity
from ..scripting.motion import (
    MotionProgram,
    MotionInstruction,
    MotionInstructionKind,
    normalize_angle,
    shortest_arc,
    angle_to_vector,
)

if TYPE_CHECKING:
    from ..game_state import GameState

# 预计算角度转换常量（避免重复计算）
_DEG_TO_RAD = math.pi / 180.0


def motion_program_system(state: "GameState", dt: float) -> None:
    """
    处理所有带 MotionProgram 组件的 Actor。
    
    对于每个带 MotionProgram 的子弹：
    1. 执行当前指令
    2. 更新 speed/angle 状态
    3. 将极坐标 (speed, angle) 转换为 Velocity.vec
    
    Args:
        state: 包含所有 Actor 的游戏状态
        dt: 时间增量（不直接使用；指令使用帧计数）
    
    **Requirements 13.6**: 遍历顺序稳定 - actors 列表按添加顺序遍历。
    
    **Requirements 14.3**: 优化以避免每帧创建新对象：
    - 原地更新 Velocity.vec 而非创建新 Vector2
    - 使用预计算的 _DEG_TO_RAD 常量
    - 缓存常用属性到局部变量
    """
    # 缓存常用函数到局部变量（微优化）
    cos = math.cos
    sin = math.sin
    
    # 按稳定顺序遍历（list 保持插入顺序）
    for actor in state.actors:
        program = actor.get(MotionProgram)
        if program is None or program.finished:
            continue
        
        vel = actor.get(Velocity)
        if vel is None:
            continue
        
        # 执行当前指令
        _execute_instruction(program, state, actor)
        
        # 将极坐标转换为速度向量（原地更新）
        # 优化：使用预计算常量和缓存的数学函数
        rad = program.angle * _DEG_TO_RAD
        speed = program.speed
        vel.vec.x = cos(rad) * speed
        vel.vec.y = sin(rad) * speed


def _execute_instruction(
    program: MotionProgram,
    state: "GameState",
    actor,
) -> None:
    """
    执行 MotionProgram 中的当前指令。
    
    处理指令初始化、每帧更新、以及完成后推进到下一条指令。
    """
    # 检查程序是否已完成
    if program.pc >= len(program.instructions):
        program.finished = True
        return
    
    instruction = program.instructions[program.pc]
    
    # 根据指令类型分发执行
    if instruction.kind == MotionInstructionKind.WAIT:
        _execute_wait(program, instruction)
    elif instruction.kind == MotionInstructionKind.SET_SPEED:
        _execute_set_speed(program, instruction)
    elif instruction.kind == MotionInstructionKind.SET_ANGLE:
        _execute_set_angle(program, instruction)
    elif instruction.kind == MotionInstructionKind.ACCELERATE_TO:
        _execute_accelerate_to(program, instruction)
    elif instruction.kind == MotionInstructionKind.TURN_TO:
        _execute_turn_to(program, instruction)
    elif instruction.kind == MotionInstructionKind.AIM_PLAYER:
        _execute_aim_player(program, instruction, state, actor)


def _execute_wait(program: MotionProgram, instruction: MotionInstruction) -> None:
    """
    执行 Wait 指令：保持当前速度 N 帧。
    
    Requirements 6.3: 执行 Wait(frames) 指令时，子弹保持当前速度并等待指定帧数。
    """
    # 首次执行时初始化帧计数器
    if program.frame_counter == 0:
        program.frame_counter = instruction.frames
    
    # 递减帧计数器
    program.frame_counter -= 1
    
    # 检查等待是否完成
    if program.frame_counter <= 0:
        program.frame_counter = 0
        program.pc += 1


def _execute_set_speed(program: MotionProgram, instruction: MotionInstruction) -> None:
    """
    执行 SetSpeed 指令：立即设置速度值。
    
    Requirements 6.4: 执行 SetSpeed(speed) 指令时，子弹立即设置速度值（px/s，保持角度）。
    """
    program.speed = instruction.speed
    program.pc += 1


def _execute_set_angle(program: MotionProgram, instruction: MotionInstruction) -> None:
    """
    执行 SetAngle 指令：立即设置角度值。
    
    Requirements 6.5: 执行 SetAngle(angle) 指令时，子弹立即设置角度（度，保持速度）。
    
    **Requirements 14.3**: 内联 normalize_angle 以避免函数调用开销。
    """
    # 内联 normalize_angle 以提高性能
    angle = instruction.angle % 360
    if angle >= 180:
        angle -= 360
    program.angle = angle
    program.pc += 1


def _execute_accelerate_to(program: MotionProgram, instruction: MotionInstruction) -> None:
    """
    执行 AccelerateTo 指令：在 N 帧内线性变化速度。
    
    Requirements 6.6: 执行 AccelerateTo(target_speed, frames) 指令时，
    子弹在指定帧数内线性变化到目标速度。
    """
    # 首次执行此指令时初始化
    if program.frame_counter == 0:
        # 预计算 delta_speed
        if instruction.frames > 0:
            instruction.delta_speed = (instruction.speed - program.speed) / instruction.frames
        else:
            instruction.delta_speed = 0.0
        program.frame_counter = instruction.frames
    
    # 应用速度变化
    program.speed += instruction.delta_speed
    
    # 递减帧计数器
    program.frame_counter -= 1
    
    # 检查加速是否完成
    if program.frame_counter <= 0:
        # 确保精确到达目标速度
        program.speed = instruction.speed
        program.frame_counter = 0
        program.pc += 1


def _execute_turn_to(program: MotionProgram, instruction: MotionInstruction) -> None:
    """
    执行 TurnTo 指令：在 N 帧内沿最短弧线性变化角度。
    
    Requirements 6.7: 执行 TurnTo(target_angle, frames) 指令时，
    子弹沿最短弧方向线性变化角度。
    
    **Requirements 14.3**: 内联 normalize_angle 以避免函数调用开销。
    """
    # 首次执行此指令时初始化
    if program.frame_counter == 0:
        # 使用最短弧预计算 delta_angle
        if instruction.frames > 0:
            arc = shortest_arc(program.angle, instruction.angle)
            instruction.delta_angle = arc / instruction.frames
        else:
            instruction.delta_angle = 0.0
        program.frame_counter = instruction.frames
    
    # 应用角度变化（内联 normalize_angle）
    angle = program.angle + instruction.delta_angle
    angle = angle % 360
    if angle >= 180:
        angle -= 360
    program.angle = angle
    
    # 递减帧计数器
    program.frame_counter -= 1
    
    # 检查转向是否完成
    if program.frame_counter <= 0:
        # 确保精确到达目标角度（内联 normalize_angle）
        final_angle = instruction.angle % 360
        if final_angle >= 180:
            final_angle -= 360
        program.angle = final_angle
        program.frame_counter = 0
        program.pc += 1


def _execute_aim_player(
    program: MotionProgram,
    instruction: MotionInstruction,
    state: "GameState",
    actor,
) -> None:
    """
    执行 AimPlayer 指令：将角度设置为朝向玩家。
    
    Requirements 6.8: 执行 AimPlayer 指令时，子弹将角度设置为朝向玩家（遵循坐标系约定）。
    
    **Requirements 14.3**: 优化 - Position 导入移至模块级别。
    """
    # 获取子弹位置（Position 在模块级别导入）
    pos = actor.get(Position)
    if pos is None:
        program.pc += 1
        return
    
    # 获取玩家位置
    player = state.get_player()
    if player is None:
        program.pc += 1
        return
    
    player_pos = player.get(Position)
    if player_pos is None:
        program.pc += 1
        return
    
    # 计算朝向玩家的角度
    dx = player_pos.x - pos.x
    dy = player_pos.y - pos.y
    
    # atan2 返回弧度，转换为度
    # 坐标系：0° = 右，90° = 下（Y 轴向下）
    # 内联 normalize_angle 以避免函数调用开销
    angle_deg = math.degrees(math.atan2(dy, dx))
    angle_deg = angle_deg % 360
    if angle_deg >= 180:
        angle_deg -= 360
    program.angle = angle_deg
    
    program.pc += 1
