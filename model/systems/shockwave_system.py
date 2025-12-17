from __future__ import annotations

from model.game_state import GameState
from model.components import Shockwave, Position

def shockwave_system(state: GameState, dt: float) -> None:
    """
    更新 Shockwave 组件的状态（扩散、淡出）。
    """
    to_remove = []
    
    for actor in state.actors:
        wave = actor.get(Shockwave)
        if not wave:
            continue
            
        # 1. 扩散
        wave.radius += wave.speed * dt
        
        # 2. 淡出
        if wave.fade_speed > 0:
            wave.alpha -= wave.fade_speed * dt
            
        # 3. 检查生命周期
        finished = False
        if wave.radius >= wave.max_radius:
            finished = True
        elif wave.alpha <= 0:
            finished = True
            
        if finished:
            to_remove.append(actor)
            
    for actor in to_remove:
        state.remove_actor(actor)
