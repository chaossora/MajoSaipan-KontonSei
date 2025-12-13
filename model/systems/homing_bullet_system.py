"""
追踪子弹系统（ECS）：处理带有 HomingBullet 组件的子弹持续追踪逻辑。

每帧更新子弹速度方向，使其朝向最近的敌人。
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional, Tuple

from pygame.math import Vector2

from ..components import (
    Position,
    Velocity,
    HomingBullet,
    PlayerBulletTag,
    EnemyTag,
)

if TYPE_CHECKING:
    from ..game_state import GameState
    from ..actor import Actor


def homing_bullet_system(state: GameState, dt: float) -> None:
    """
    追踪子弹系统：更新所有带 HomingBullet 组件的子弹速度。
    
    符合 ECS 架构：
    - 查询所有带 HomingBullet + Velocity + Position 的实体
    - 根据最近敌人位置调整速度方向
    """
    for actor in state.actors:
        homing = actor.get(HomingBullet)
        if not homing:
            continue
        
        vel = actor.get(Velocity)
        pos = actor.get(Position)
        if not (vel and pos):
            continue
        
        # 查找最近敌人
        target_pos = _find_nearest_enemy_pos(state, pos.x, pos.y)
        if target_pos is None:
            # 没有敌人时保持当前方向
            continue
        
        # 计算目标方向
        dx = target_pos[0] - pos.x
        dy = target_pos[1] - pos.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 1.0:
            continue
        
        # 目标角度（pygame 坐标系，向上为负Y）
        target_angle = math.degrees(math.atan2(dy, dx))
        
        # 当前速度角度
        current_angle = math.degrees(math.atan2(vel.vec.y, vel.vec.x))
        
        # 计算角度差（最短路径）
        angle_diff = _normalize_angle(target_angle - current_angle)
        
        # 限制转向速率
        max_turn = homing.turn_rate * dt
        if abs(angle_diff) > max_turn:
            angle_diff = max_turn if angle_diff > 0 else -max_turn
        
        # 应用新角度
        new_angle = current_angle + angle_diff
        new_angle_rad = math.radians(new_angle)
        
        # 更新速度（保持追踪速度）
        vel.vec.x = math.cos(new_angle_rad) * homing.speed
        vel.vec.y = math.sin(new_angle_rad) * homing.speed


def _find_nearest_enemy_pos(
    state: GameState,
    x: float,
    y: float,
) -> Optional[Tuple[float, float]]:
    """查找最近敌人的位置。"""
    nearest_pos: Optional[Tuple[float, float]] = None
    min_dist_sq = float('inf')
    
    for actor in state.actors:
        if not actor.has(EnemyTag):
            continue
        epos = actor.get(Position)
        if not epos:
            continue
        
        dx = epos.x - x
        dy = epos.y - y
        dist_sq = dx * dx + dy * dy
        
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            nearest_pos = (epos.x, epos.y)
    
    return nearest_pos


def _normalize_angle(angle: float) -> float:
    """将角度归一化到 [-180, 180] 范围。"""
    while angle > 180:
        angle -= 360
    while angle < -180:
        angle += 360
    return angle
