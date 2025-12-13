"""
弹幕图案工具库。

提供创建常见弹幕图案的高级函数。
所有函数内部调用 ctx.fire() 原语。

**Requirements: 4.4, 4.5**
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Any, Optional

if TYPE_CHECKING:
    from model.actor import Actor
    from model.scripting.context import TaskContext


def fire_ring(
    ctx: "TaskContext",
    x: float,
    y: float,
    count: int,
    speed: float,
    archetype: str = "default",
    motion: Optional[Any] = None,
    start_angle: float = 0.0,
) -> List["Actor"]:
    """
    发射环形弹幕，子弹均匀分布在圆周上。
    
    在位置 (x, y) 创建 `count` 颗子弹，角度均匀分布在 360 度范围内。
    
    Args:
        ctx: 用于发射子弹的 TaskContext
        x: 子弹生成的 X 位置
        y: 子弹生成的 Y 位置
        count: 环形弹幕的子弹数量（必须 >= 1）
        speed: 子弹速度 (px/s)
        archetype: 子弹原型 ID
        motion: 可选的 MotionProgram
        start_angle: 起始角度偏移（度，默认 0）
    
    Returns:
        创建的子弹 Actor 列表
    
    **Requirements: 4.1**
    """
    if count < 1:
        return []
    
    bullets = []
    angle_step = 360.0 / count
    
    for i in range(count):
        angle = start_angle + i * angle_step
        bullet = ctx.fire(x, y, speed, angle, archetype, motion)
        bullets.append(bullet)
    
    return bullets


def fire_fan(
    ctx: "TaskContext",
    x: float,
    y: float,
    count: int,
    spread: float,
    base_angle: float,
    speed: float,
    archetype: str = "default",
    motion: Optional[Any] = None,
) -> List["Actor"]:
    """
    发射扇形弹幕。
    
    在位置 (x, y) 创建 `count` 颗子弹，角度均匀分布在
    以 base_angle 为中心的 spread 范围内。
    
    Args:
        ctx: 用于发射子弹的 TaskContext
        x: 子弹生成的 X 位置
        y: 子弹生成的 Y 位置
        count: 扇形弹幕的子弹数量（必须 >= 1）
        spread: 总展开角度（度）
        base_angle: 扇形中心角度（度）
        speed: 子弹速度 (px/s)
        archetype: 子弹原型 ID
        motion: 可选的 MotionProgram
    
    Returns:
        创建的子弹 Actor 列表
    
    **Requirements: 4.2**
    """
    if count < 1:
        return []
    
    bullets = []
    
    # 处理 count=1 的边界情况：直接发射到 base_angle
    if count == 1:
        bullet = ctx.fire(x, y, speed, base_angle, archetype, motion)
        return [bullet]
    
    # 计算扇形分布的角度
    start_angle = base_angle - spread / 2
    angle_step = spread / (count - 1)
    
    for i in range(count):
        angle = start_angle + i * angle_step
        bullet = ctx.fire(x, y, speed, angle, archetype, motion)
        bullets.append(bullet)
    
    return bullets


def fire_spiral(
    ctx: "TaskContext",
    x: float,
    y: float,
    arms: int,
    bullets_per_arm: int,
    speed: float,
    archetype: str = "default",
    angle_offset: float = 0.0,
    motion: Optional[Any] = None,
) -> List["Actor"]:
    """
    发射螺旋弹幕。
    
    创建多臂螺旋图案，每臂包含多颗角度递进偏移的子弹。
    
    Args:
        ctx: 用于发射子弹的 TaskContext
        x: 子弹生成的 X 位置
        y: 子弹生成的 Y 位置
        arms: 螺旋臂数量（必须 >= 1）
        bullets_per_arm: 每臂子弹数量（必须 >= 1）
        speed: 子弹速度 (px/s)
        archetype: 子弹原型 ID
        angle_offset: 起始角度偏移（度）
        motion: 可选的 MotionProgram
    
    Returns:
        创建的子弹 Actor 列表
    
    **Requirements: 4.3**
    """
    if arms < 1 or bullets_per_arm < 1:
        return []
    
    bullets = []
    arm_angle_step = 360.0 / arms
    bullet_angle_step = 360.0 / (arms * bullets_per_arm)
    
    for arm in range(arms):
        for i in range(bullets_per_arm):
            angle = angle_offset + arm * arm_angle_step + i * bullet_angle_step
            bullet = ctx.fire(x, y, speed, angle, archetype, motion)
            bullets.append(bullet)
    
    return bullets


def fire_aimed(
    ctx: "TaskContext",
    x: float,
    y: float,
    speed: float,
    archetype: str = "default",
    motion: Optional[Any] = None,
) -> "Actor":
    """
    发射朝向玩家当前位置的子弹（自机狙）。
    
    ctx.fire_aimed() 的便捷包装。
    
    Args:
        ctx: 用于发射子弹的 TaskContext
        x: 子弹生成的 X 位置
        y: 子弹生成的 Y 位置
        speed: 子弹速度 (px/s)
        archetype: 子弹原型 ID
        motion: 可选的 MotionProgram
    
    Returns:
        创建的子弹 Actor
    """
    return ctx.fire_aimed(x, y, speed, archetype, motion)
