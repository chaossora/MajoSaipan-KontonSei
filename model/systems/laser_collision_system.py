"""
激光碰撞检测系统。

实现点到线段距离判定：
- 直线激光：单线段判定
- 正弦波激光：采样离散化后多线段判定

判定公式：distance <= laser_half_width + player_hitbox_radius

坐标系约定：
- 0° = 右（+X 方向）
- 90° = 下（+Y 方向）
- 角度顺时针增加
"""
from __future__ import annotations

import math
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from model.game_state import GameState
    from model.components import LaserState, Position


def _point_to_segment_distance(
    px: float, py: float,
    x1: float, y1: float,
    x2: float, y2: float
) -> float:
    """
    计算点 (px, py) 到线段 (x1,y1)-(x2,y2) 的最短距离。

    使用投影法：
    1. 计算点到直线的投影参数 t
    2. 钳制 t 到 [0, 1] 得到线段上的最近点
    3. 返回点到最近点的距离

    Args:
        px, py: 点坐标
        x1, y1: 线段起点
        x2, y2: 线段终点

    Returns:
        点到线段的最短距离
    """
    dx = x2 - x1
    dy = y2 - y1

    # 线段长度的平方
    seg_len_sq = dx * dx + dy * dy

    if seg_len_sq < 1e-10:  # 线段退化为点
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

    # 投影参数 t = dot(AP, AB) / |AB|^2
    # AP = (px - x1, py - y1), AB = (dx, dy)
    t = ((px - x1) * dx + (py - y1) * dy) / seg_len_sq
    t = max(0.0, min(1.0, t))  # 钳制到 [0, 1]

    # 线段上的最近点
    nearest_x = x1 + t * dx
    nearest_y = y1 + t * dy

    return math.sqrt((px - nearest_x) ** 2 + (py - nearest_y) ** 2)


def _get_laser_segments(
    laser_pos: "Position",
    laser_state: "LaserState"
) -> List[Tuple[float, float, float, float]]:
    """
    获取激光的线段列表 [(x1, y1, x2, y2), ...]

    - 直线激光：返回单个线段
    - 正弦波激光：沿主轴采样，返回多个线段

    Args:
        laser_pos: 激光起点位置
        laser_state: 激光状态组件

    Returns:
        线段列表，每个线段为 (x1, y1, x2, y2)
    """
    from model.components import LaserType

    segments: List[Tuple[float, float, float, float]] = []

    if laser_state.laser_type == LaserType.STRAIGHT:
        # 直线激光：从原点沿角度延伸
        rad = math.radians(laser_state.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        end_x = laser_pos.x + laser_state.length * cos_a
        end_y = laser_pos.y + laser_state.length * sin_a
        segments.append((laser_pos.x, laser_pos.y, end_x, end_y))

    elif laser_state.laser_type == LaserType.SINE_WAVE:
        # 正弦波激光：沿主轴采样，形成多线段
        rad = math.radians(laser_state.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        # 采样点数（每20像素一个点，确保曲线平滑）
        sample_count = max(int(laser_state.length / 20), 2)

        # 起点
        prev_x = laser_pos.x
        prev_y = laser_pos.y

        for i in range(1, sample_count + 1):
            t = i / sample_count
            dist = t * laser_state.length

            # 沿主轴的位置
            main_x = laser_pos.x + dist * cos_a
            main_y = laser_pos.y + dist * sin_a

            # 正弦偏移（垂直于主轴）
            # 相位随距离变化：phase = base_phase + (dist / wavelength) * 360
            phase_deg = laser_state.sine_phase + (dist / laser_state.sine_wavelength) * 360
            offset = laser_state.sine_amplitude * math.sin(math.radians(phase_deg))

            # 垂直方向（旋转90度）：(-sin_a, cos_a)
            perp_x = -sin_a * offset
            perp_y = cos_a * offset

            curr_x = main_x + perp_x
            curr_y = main_y + perp_y

            segments.append((prev_x, prev_y, curr_x, curr_y))
            prev_x, prev_y = curr_x, curr_y

    return segments


def laser_collision_system(state: "GameState") -> None:
    """
    激光碰撞检测系统。

    检测所有激活激光与玩家的碰撞，生成 LaserHitPlayer 事件。

    判定逻辑：
    - 遍历所有激光实体
    - 跳过预热中的激光（warmup_timer > 0）
    - 对每个激光，获取其线段列表
    - 计算玩家到每个线段的距离
    - 如果距离 <= laser_width/2 + player_radius，记录碰撞事件

    Args:
        state: GameState 引用
    """
    from model.components import (
        Position, Collider, PlayerTag, LaserState, LaserTag
    )
    from model.collision_events import LaserHitPlayer

    events = state.collision_events

    # 收集玩家
    players = []
    for actor in state.actors:
        if actor.has(PlayerTag):
            pos = actor.get(Position)
            col = actor.get(Collider)
            if pos and col:
                players.append((actor, pos, col))

    if not players:
        return

    # 收集激活的激光
    lasers = []
    for actor in state.actors:
        if actor.has(LaserTag):
            laser_state = actor.get(LaserState)
            laser_pos = actor.get(Position)
            if laser_state and laser_pos and laser_state.active:
                # 跳过预热中的激光
                if laser_state.warmup_timer > 0:
                    continue
                lasers.append((actor, laser_pos, laser_state))

    # 碰撞检测
    for laser_actor, laser_pos, laser_state in lasers:
        segments = _get_laser_segments(laser_pos, laser_state)
        half_width = laser_state.width / 2

        for player_actor, player_pos, player_col in players:
            player_radius = player_col.radius
            hit_threshold = half_width + player_radius

            # 检查每个线段
            hit = False
            for x1, y1, x2, y2 in segments:
                dist = _point_to_segment_distance(
                    player_pos.x, player_pos.y,
                    x1, y1, x2, y2
                )

                if dist <= hit_threshold:
                    hit = True
                    break

            if hit:
                events.laser_hits_player.append(
                    LaserHitPlayer(laser=laser_actor, player=player_actor)
                )
