from __future__ import annotations

from ..game_state import GameState
from ..components import Lifetime


def lifetime_system(state: GameState, dt: float) -> None:
    """
    生命周期系统：
    - 带 Lifetime 的实体 time_left -= dt
    - time_left <= 0 的实体删除
    
    优化：使用反向遍历和 del 删除，避免创建临时列表。
    保持列表顺序以确保确定性（Requirements 13.6）。
    Requirements 14.1: 提供迭代器接口避免创建临时列表
    """
    # 反向遍历，允许原地删除而不影响遍历顺序
    i = len(state.actors) - 1
    while i >= 0:
        actor = state.actors[i]
        life = actor.get(Lifetime)
        
        if life is not None:
            life.time_left -= dt
            if life.time_left <= 0.0:
                del state.actors[i]
        
        i -= 1
