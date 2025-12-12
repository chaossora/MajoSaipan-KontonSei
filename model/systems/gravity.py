from __future__ import annotations

from ..game_state import GameState
from ..components import Velocity, Gravity


def gravity_system(state: GameState, dt: float) -> None:
    """
    通用重力系统：
    - 遍历所有有 Velocity + Gravity 的实体
    - vy += g * dt
    - vy 不超过 max_fall_speed
    现在 item 用它；以后你想让别的东西也“受重力”就给它挂 Gravity 即可。
    """
    for actor in state.actors:
        vel = actor.get(Velocity)
        g = actor.get(Gravity)
        if not (vel and g):
            continue

        # 只作用于 Y 方向
        vel.vec.y += g.g * dt

        # 限制最大下落速度
        if vel.vec.y > g.max_fall_speed:
            vel.vec.y = g.max_fall_speed
