from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Optional, TYPE_CHECKING

from pygame.math import Vector2

from .registry import Registry
from .components import ShotConfig, ShotOriginOffset, FocusState, PlayerBulletKind

if TYPE_CHECKING:
    from .game_state import GameState
    from .character import EnhancedShotConfig


class ShotKind(Enum):
    """射击类型枚举"""
    SPREAD = auto()   # 扩散弹
    MISSILE = auto()  # 导弹（目前与扩散弹相同）


shot_registry: Registry[ShotKind] = Registry("player_shot")


def dispatch_player_shot(
    state: GameState,
    shot_cfg: ShotConfig,
    pos,
    shot_origin: Optional[ShotOriginOffset],
    focus_state: FocusState,
) -> None:
    """分发玩家射击行为。"""
    handler: Optional[Callable] = shot_registry.get(shot_cfg.shot_type)
    if handler:
        handler(state, shot_cfg, pos, shot_origin, focus_state)
    else:
        _shot_spread(state, shot_cfg, pos, shot_origin, focus_state)


def dispatch_enhanced_player_shot(
    state: GameState,
    shot_cfg: ShotConfig,
    enhanced_cfg: "EnhancedShotConfig",
    pos,
    shot_origin: Optional[ShotOriginOffset],
    focus_state: FocusState,
) -> None:
    """
    分发增强版玩家射击。
    使用 EnhancedShotConfig 的角度和伤害倍率。
    """
    from .game_state import spawn_player_bullet

    # 选择增强角度
    angles = (
        enhanced_cfg.angles_focus_enhanced
        if focus_state.is_focusing
        else enhanced_cfg.angles_spread_enhanced
    )

    offset = shot_origin.bullet_spawn_offset_y if shot_origin else 16.0
    y = pos.y - offset

    # 计算增强伤害和弹速
    enhanced_damage = int(shot_cfg.damage * enhanced_cfg.damage_multiplier)
    enhanced_speed = shot_cfg.bullet_speed * enhanced_cfg.bullet_speed_multiplier

    for ang in angles:
        spawn_player_bullet(
            state,
            x=pos.x,
            y=y,
            damage=enhanced_damage,
            speed=enhanced_speed,
            angle_deg=ang,
            bullet_kind=PlayerBulletKind.MAIN_ENHANCED,
        )


@shot_registry.register(ShotKind.SPREAD)
def _shot_spread(
    state,
    cfg: ShotConfig,
    pos,
    shot_origin: Optional[ShotOriginOffset],
    focus_state: FocusState,
) -> None:
    """扩散弹射击：根据是否聚焦选择不同角度。"""
    from .game_state import spawn_player_bullet
    angles = cfg.angles_focus if focus_state.is_focusing else cfg.angles_spread
    offset = shot_origin.bullet_spawn_offset_y if shot_origin else 16.0
    y = pos.y - offset
    for ang in angles:
        spawn_player_bullet(
            state,
            x=pos.x,
            y=y,
            damage=cfg.damage,
            speed=cfg.bullet_speed,
            angle_deg=ang,
            bullet_kind=PlayerBulletKind.MAIN_NORMAL,
        )


@shot_registry.register(ShotKind.MISSILE)
def _shot_missile(
    state,
    cfg: ShotConfig,
    pos,
    shot_origin: Optional[ShotOriginOffset],
    focus_state: FocusState,
) -> None:
    """导弹射击：目前与扩散弹相同，以后可扩展。"""
    _shot_spread(state, cfg, pos, shot_origin, focus_state)
