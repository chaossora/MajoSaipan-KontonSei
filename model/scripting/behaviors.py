"""
敌人行为脚本。

提供常见敌人行为的 Task 生成器函数。
这些行为控制敌人的移动和射击模式。

**Requirements: 12.1, 12.3**
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from model.scripting.context import TaskContext

from model.scripting.patterns import fire_fan, fire_aimed


def fairy_behavior_1(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    基础小妖精行为：进入 → 停顿 → 射击 → 离开
    
    小妖精移动到目标位置，停顿并发射 3 次扇形弹，然后向下离开。
    
    **Requirements: 12.1, 12.3**
    """
    x, y = ctx.owner_pos()
    
    # 移动到屏幕中部 (y=200)
    yield from ctx.move_to(x, 200, frames=60)
    
    # 停顿并射击 3 次
    for _ in range(3):
        yield 30  # 等待 0.5 秒
        # 发射 5-way 扇形弹，朝下
        ox, oy = ctx.owner_pos()
        fire_fan(ctx, ox, oy, count=5, spread=60, 
                 base_angle=90, speed=120, archetype="bullet_small")
    
    yield 60  # 等待 1 秒
    
    # 向下离开屏幕
    ox, oy = ctx.owner_pos()
    yield from ctx.move_to(ox, ctx.state.height + 50, frames=90)


def fairy_behavior_sine(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    正弦波小妖精行为：水平摇摆下降 + 周期射击
    
    小妖精以正弦波模式移动，同时缓慢下降，
    定期发射自机狙。
    
    **Requirements: 12.1, 12.3**
    """
    from model.components import Position, Velocity
    from pygame.math import Vector2
    
    start_x, start_y = ctx.owner_pos()
    amplitude = 60  # 水平摇摆幅度
    frequency = 0.025  # 摇摆频率（每帧周期数）
    descent_speed = 2.0  # 每帧下降像素
    shoot_interval = 50  # 射击间隔帧数
    
    # 设置初始速度以平滑移动
    vel = ctx.owner.get(Velocity)
    if vel:
        vel.vec = Vector2(0, descent_speed * 60)  # 转换为 px/s
    
    frame = 0
    while True:
        # 计算正弦波位置
        new_x = start_x + amplitude * math.sin(frame * frequency * 2 * math.pi)
        new_y = start_y + frame * descent_speed
        
        # 直接更新位置以获得精确的正弦波
        pos = ctx.owner.get(Position)
        if pos:
            pos.x = new_x
            pos.y = new_y
        
        # 每 shoot_interval 帧发射自机狙
        if frame % shoot_interval == 0 and frame > 0:
            fire_aimed(ctx, new_x, new_y, speed=120, archetype="bullet_small")
        
        # 出界时退出
        if new_y > ctx.state.height + 50:
            break
        
        frame += 1
        yield 1


def fairy_behavior_straight(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    简单直线小妖精行为：缓慢向下移动，偶尔射击
    
    基础行为，小妖精直线向下移动并发射自机狙。
    
    **Requirements: 12.1, 12.3**
    """
    from model.components import Position, Velocity
    from pygame.math import Vector2
    
    descent_speed = 2.0  # 每帧像素
    shoot_interval = 70  # 射击间隔帧数
    
    # 使用速度进行平滑移动
    vel = ctx.owner.get(Velocity)
    if vel:
        vel.vec = Vector2(0, descent_speed * 60)  # 转换为 px/s
    
    frame = 0
    while True:
        pos = ctx.owner.get(Position)
        if pos:
            # 定期发射自机狙
            if frame % shoot_interval == 0 and frame > 0:
                fire_aimed(ctx, pos.x, pos.y, speed=100, archetype="bullet_small")
            
            # 出界时退出
            if pos.y > ctx.state.height + 50:
                break
        
        frame += 1
        yield 1


def fairy_behavior_diagonal(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    斜向移动小妖精行为：斜向穿越屏幕
    
    小妖精斜向移动（根据位置向右下或左下），
    同时偶尔发射自机狙。
    
    **Requirements: 12.1, 12.3**
    """
    from model.components import Position, Velocity
    from pygame.math import Vector2
    
    start_x, _ = ctx.owner_pos()
    center_x = ctx.state.width / 2
    
    # 根据起始位置决定方向
    # 如果在左侧，向右移动；如果在右侧，向左移动
    dx = 2.5 if start_x < center_x else -2.5
    dy = 2.0  # 始终向下移动
    
    # 使用速度进行平滑移动
    vel = ctx.owner.get(Velocity)
    if vel:
        vel.vec = Vector2(dx * 60, dy * 60)  # 转换为 px/s
    
    shoot_interval = 60  # 射击间隔帧数
    
    frame = 0
    while True:
        pos = ctx.owner.get(Position)
        if pos:
            # 定期发射自机狙
            if frame % shoot_interval == 0 and frame > 0:
                fire_aimed(ctx, pos.x, pos.y, speed=110, archetype="bullet_small")
            
            # 出界时退出（任意边缘）
            if (pos.y > ctx.state.height + 50 or 
                pos.x < -50 or pos.x > ctx.state.width + 50):
                break
        
        frame += 1
        yield 1
