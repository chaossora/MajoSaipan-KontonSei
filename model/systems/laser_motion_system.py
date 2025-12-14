"""
激光运动系统：处理激光旋转、反射、预热等运动逻辑。

功能：
- 预热计时器递减（预热期间显示预警线但无判定）
- 角速度旋转处理
- 边界反射处理（直线激光）

坐标系约定：
- 0° = 右（+X 方向）
- 90° = 下（+Y 方向）
- 角度顺时针增加
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.game_state import GameState
    from model.components import LaserState, Position


def _handle_reflection(
    state: "GameState",
    laser_pos: "Position",
    laser_state: "LaserState"
) -> None:
    """
    处理直线激光的边界反射。

    当激光端点碰到屏幕边界时，计算反射角度。
    反射规则：
    - 碰到左右边界：angle = 180 - angle
    - 碰到上下边界：angle = -angle

    Args:
        state: GameState 引用
        laser_pos: 激光起点位置
        laser_state: 激光状态组件
    """
    from model.components import LaserType

    # 只处理直线激光的反射
    if laser_state.laser_type != LaserType.STRAIGHT:
        return

    # 检查是否已达到最大反射次数
    if laser_state.reflect_count >= laser_state.max_reflects:
        return

    # 计算激光端点位置
    rad = math.radians(laser_state.angle)
    end_x = laser_pos.x + laser_state.length * math.cos(rad)
    end_y = laser_pos.y + laser_state.length * math.sin(rad)

    margin = 5.0
    reflected = False
    new_angle = laser_state.angle

    # 左右边界反射
    if end_x < margin or end_x > state.width - margin:
        new_angle = 180 - new_angle
        reflected = True

    # 上下边界反射
    if end_y < margin or end_y > state.height - margin:
        new_angle = -new_angle
        reflected = True

    if reflected:
        # 归一化角度到 [0, 360)
        laser_state.angle = new_angle % 360
        laser_state.reflect_count += 1


def laser_motion_system(state: "GameState", dt: float) -> None:
    """
    激光运动系统。

    每帧更新所有激光的运动状态：
    1. 预热计时器递减
    2. 角速度旋转
    3. 边界反射处理

    Args:
        state: GameState 引用
        dt: 帧时间间隔（秒），当前未使用（使用帧计数）
    """
    from model.components import Position, LaserState, LaserTag

    for actor in state.actors:
        if not actor.has(LaserTag):
            continue

        laser_state = actor.get(LaserState)
        laser_pos = actor.get(Position)

        if not (laser_state and laser_pos):
            continue

        # 1. 预热计时器递减
        if laser_state.warmup_timer > 0:
            laser_state.warmup_timer -= 1
            # 预热期间不执行其他运动逻辑
            continue

        # 2. 角速度旋转
        if laser_state.angular_velocity != 0:
            laser_state.angle += laser_state.angular_velocity
            # 归一化角度到 [0, 360)
            laser_state.angle = laser_state.angle % 360

        # 3. 边界反射处理（仅当启用反射时）
        if laser_state.can_reflect:
            _handle_reflection(state, laser_pos, laser_state)
