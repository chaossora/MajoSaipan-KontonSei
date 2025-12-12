# model/systems/boss_movement_system.py
"""
Boss 移动系统（东方风格）：
- 状态机模式：IDLE（静止）→ MOVING（滑动）循环
- 间隔移动：每 1.5-3 秒向玩家方向滑动一次
- ease-out 缓动：开始快、接近目标减速
- Y 方向波动：移动时有小幅垂直变化
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from ..components import (
    Position, PlayerTag,
    EnemyKind, EnemyKindTag,
    BossMovementState, BossState,
)

if TYPE_CHECKING:
    from ..game_state import GameState


def ease_out_quad(t: float) -> float:
    """二次缓出函数：开始快，结束时减速。"""
    return 1.0 - (1.0 - t) ** 2


def lerp(a: float, b: float, t: float) -> float:
    """线性插值。"""
    return a + (b - a) * t


def boss_movement_system(state: GameState, dt: float) -> None:
    """
    Boss 移动系统：实现东方风格的间隔滑动移动。
    """
    # 获取玩家位置
    player_pos = _get_player_position(state)
    if not player_pos:
        return

    for actor in state.actors:
        # 检查是否为 Boss
        kind_tag = actor.get(EnemyKindTag)
        if not kind_tag or kind_tag.kind != EnemyKind.BOSS:
            continue

        move = actor.get(BossMovementState)
        pos = actor.get(Position)
        boss_state = actor.get(BossState)

        if not (move and pos):
            continue

        # 阶段转换期间不移动
        if boss_state and boss_state.phase_transitioning:
            continue

        if move.is_moving:
            # === 滑动状态 ===
            _update_moving_state(move, pos, dt)
        else:
            # === 静止状态 ===
            _update_idle_state(move, pos, player_pos, state, dt)


def _update_moving_state(move: BossMovementState, pos: Position, dt: float) -> None:
    """处理滑动状态：平滑移动到目标位置。"""
    move.move_progress += dt / move.move_duration

    if move.move_progress >= 1.0:
        # 到达目标，切换到静止状态
        pos.x = move.target_x
        pos.y = move.target_y
        move.is_moving = False
        move.move_progress = 0.0
        move.move_timer = random.uniform(move.idle_time_min, move.idle_time_max)
    else:
        # 使用 ease-out 插值
        t = ease_out_quad(move.move_progress)
        pos.x = lerp(move.start_x, move.target_x, t)
        pos.y = lerp(move.start_y, move.target_y, t)


def _update_idle_state(
    move: BossMovementState,
    pos: Position,
    player_pos: Position,
    state: GameState,
    dt: float,
) -> None:
    """处理静止状态：等待并准备下一次移动。"""
    move.move_timer -= dt

    if move.move_timer <= 0:
        # 开始新的移动
        move.is_moving = True
        move.move_progress = 0.0
        move.move_duration = random.uniform(move.move_duration_min, move.move_duration_max)

        # 记录起始位置
        move.start_x = pos.x
        move.start_y = pos.y

        # 计算目标 X：玩家位置 + 随机偏移
        offset_x = random.uniform(-move.target_offset_range, move.target_offset_range)
        margin = 40.0
        move.target_x = max(margin, min(player_pos.x + offset_x, state.width - margin))

        # 计算目标 Y：在允许范围内随机选择
        # 基于当前 Y 的小幅波动，而非完全随机
        base_y = (move.y_min + move.y_max) / 2
        y_offset = random.uniform(-move.y_variation, move.y_variation)
        move.target_y = max(move.y_min, min(base_y + y_offset, move.y_max))


def _get_player_position(state: GameState) -> Position | None:
    """获取玩家位置。"""
    for actor in state.actors:
        if actor.get(PlayerTag):
            return actor.get(Position)
    return None
