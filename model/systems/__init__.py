# model/systems/__init__.py
"""
ECS 系统层导出。

Systems by category:
- Input/Movement: player_movement, movement, boundary_system
- Shooting: player_shoot, enemy_shoot
- Collision: collision, collision_damage_system, bomb_hit_system, graze_system, item_pickup
- Player state: player_damage, bomb_system, poc_system
- Enemy: enemy_death
- Physics: gravity, item_autocollect
- Stage: stage_system
- Lifecycle: lifetime
- Render data: render_hint_system, hud_data_system, stats_system
"""

from .movement import movement_system
from .player_movement import player_move_system
from .player_shoot import player_shoot_system
from .enemy_shoot import enemy_shoot_system
from .collision import collision_detection_system
from .collision_damage_system import collision_damage_system
from .bomb_hit_system import bomb_hit_system
from .graze_system import graze_system
from .item_pickup import item_pickup_system
from .player_damage import player_damage_system
from .bomb_system import bomb_system
from .enemy_death import enemy_death_system
from .lifetime import lifetime_system
from .gravity import gravity_system
from .item_autocollect import item_autocollect_system
from .poc_system import poc_system
from .stage_system import stage_system

# 新增系统
from .boundary_system import boundary_system
from .render_hint_system import render_hint_system
from .hud_data_system import hud_data_system
from .stats_system import stats_system
from .bullet_motion_system import bullet_motion_system

__all__ = [
    "movement_system",
    "player_move_system",
    "player_shoot_system",
    "enemy_shoot_system",
    "collision_detection_system",
    "collision_damage_system",
    "bomb_hit_system",
    "graze_system",
    "item_pickup_system",
    "player_damage_system",
    "bomb_system",
    "enemy_death_system",
    "lifetime_system",
    "gravity_system",
    "item_autocollect_system",
    "poc_system",
    "stage_system",
    "boundary_system",
    "render_hint_system",
    "hud_data_system",
    "stats_system",
    "bullet_motion_system",
]
