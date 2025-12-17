from __future__ import annotations

from model.game_state import GameState
from model.components import Animation, SpriteInfo

def vfx_system(state: GameState, dt: float) -> None:
    """
    Update Animation components and sync with SpriteInfo.
    """
    to_remove = []
    
    for actor in state.actors:
        anim = actor.get(Animation)
        if not anim:
            continue
            
        anim.timer += dt
        if anim.timer >= anim.duration:
            anim.timer = 0.0
            anim.current_frame += 1
            
            if anim.current_frame >= anim.total_frames:
                if anim.loop:
                    anim.current_frame = 0
                elif anim.auto_remove:
                    to_remove.append(actor)
                    continue
                else:
                    anim.current_frame = anim.total_frames - 1
        
        # Sync with SpriteInfo
        sprite = actor.get(SpriteInfo)
        if sprite:
            sprite.name = f"{anim.base_name}_{anim.current_frame}"

    for actor in to_remove:
        state.remove_actor(actor)
