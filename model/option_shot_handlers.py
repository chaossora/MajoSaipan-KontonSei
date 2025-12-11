"""
子机射击处理器注册表。
定义不同的子机射击行为，支持 Focus 状态依赖。
支持增强状态的伤害倍率。
"""
from __future__ import annotations

import math
from dataclasses import replace
from enum import Enum, auto
from typing import TYPE_CHECKING, Tuple, Optional, Callable

from .registry import Registry
from .components import PlayerBulletKind

if TYPE_CHECKING:
    from .game_state import GameState
    from .components import OptionConfig, ShotConfig


class OptionShotKind(Enum):
    """子机射击类型枚举"""
    REIMU_STYLE = auto()   # 平时直射，Focus追踪
    MARISA_STYLE = auto()  # 平时扩散，Focus直射
    STRAIGHT = auto()      # 始终直射
    HOMING = auto()        # 始终追踪
    SPREAD = auto()        # 始终扩散


option_shot_registry: Registry[OptionShotKind] = Registry("option_shot")


def dispatch_option_shot(
    state: "GameState",
    option_pos: Tuple[float, float],
    option_index: int,
    option_cfg: "OptionConfig",
    shot_cfg: "ShotConfig",
    is_focusing: bool,
    is_enhanced: bool = False,
    damage_multiplier: float = 1.0,
) -> None:
    """
    分发子机射击到已注册的处理器。

    Args:
        state: 游戏状态
        option_pos: 子机当前位置 (x, y)
        option_index: 子机索引 (0-3)
        option_cfg: 子机配置
        shot_cfg: 玩家射击配置（用于伤害、速度）
        is_focusing: 是否处于 Focus 状态
        is_enhanced: 是否处于增强状态
        damage_multiplier: 伤害倍率（增强时 > 1.0）
    """
    # 应用增强伤害倍率
    if damage_multiplier != 1.0:
        option_cfg = replace(option_cfg, damage_ratio=option_cfg.damage_ratio * damage_multiplier)

    handler: Optional[Callable] = option_shot_registry.get(option_cfg.option_shot_kind)
    if handler:
        handler(state, option_pos, option_index, option_cfg, shot_cfg, is_focusing, is_enhanced)
    else:
        # 回退到直射
        _shot_straight(state, option_pos, option_index, option_cfg, shot_cfg, is_focusing, is_enhanced)


# ========== 基础射击类型 ==========

@option_shot_registry.register(OptionShotKind.STRAIGHT)
def _shot_straight(
    state: "GameState",
    option_pos: Tuple[float, float],
    option_index: int,
    option_cfg: "OptionConfig",
    shot_cfg: "ShotConfig",
    is_focusing: bool,
    is_enhanced: bool = False,
) -> None:
    """直射：始终向上发射。"""
    from .game_state import spawn_player_bullet

    bullet_kind = PlayerBulletKind.OPTION_ENHANCED if is_enhanced else PlayerBulletKind.OPTION_NORMAL
    damage = max(1, int(shot_cfg.damage * option_cfg.damage_ratio))
    spawn_player_bullet(
        state,
        x=option_pos[0],
        y=option_pos[1],
        damage=damage,
        speed=shot_cfg.bullet_speed,
        angle_deg=0.0,
        bullet_kind=bullet_kind,
    )


@option_shot_registry.register(OptionShotKind.HOMING)
def _shot_homing(
    state: "GameState",
    option_pos: Tuple[float, float],
    option_index: int,
    option_cfg: "OptionConfig",
    shot_cfg: "ShotConfig",
    is_focusing: bool,
    is_enhanced: bool = False,
) -> None:
    """追踪：瞄准最近的敌人。"""
    from .game_state import spawn_player_bullet
    from .components import Position, EnemyTag

    bullet_kind = PlayerBulletKind.OPTION_ENHANCED if is_enhanced else PlayerBulletKind.OPTION_NORMAL
    damage = max(1, int(shot_cfg.damage * option_cfg.damage_ratio))

    # 查找最近的敌人
    nearest_enemy = None
    min_dist_sq = float('inf')

    for actor in state.actors:
        if not actor.has(EnemyTag):
            continue
        epos = actor.get(Position)
        if not epos:
            continue
        dx = epos.x - option_pos[0]
        dy = epos.y - option_pos[1]
        dist_sq = dx * dx + dy * dy
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            nearest_enemy = epos

    # 计算角度
    angle = 0.0  # 默认直射向上
    if nearest_enemy:
        dx = nearest_enemy.x - option_pos[0]
        dy = nearest_enemy.y - option_pos[1]
        if dx * dx + dy * dy > 1e-9:
            # atan2 返回从 +X 轴的角度，我们需要从 -Y 轴（向上）的角度
            angle = math.degrees(math.atan2(dx, -dy))

    spawn_player_bullet(
        state,
        x=option_pos[0],
        y=option_pos[1],
        damage=damage,
        speed=shot_cfg.bullet_speed * 0.9,  # 追踪弹稍慢
        angle_deg=angle,
        bullet_kind=bullet_kind,
    )


@option_shot_registry.register(OptionShotKind.SPREAD)
def _shot_spread(
    state: "GameState",
    option_pos: Tuple[float, float],
    option_index: int,
    option_cfg: "OptionConfig",
    shot_cfg: "ShotConfig",
    is_focusing: bool,
    is_enhanced: bool = False,
) -> None:
    """扩散：扇形发射多发子弹。"""
    from .game_state import spawn_player_bullet

    bullet_kind = PlayerBulletKind.OPTION_ENHANCED if is_enhanced else PlayerBulletKind.OPTION_NORMAL
    # 扩散伤害稍低（多发）
    damage = max(1, int(shot_cfg.damage * option_cfg.damage_ratio * 0.6))
    angles = [-15.0, 0.0, 15.0]

    for angle in angles:
        spawn_player_bullet(
            state,
            x=option_pos[0],
            y=option_pos[1],
            damage=damage,
            speed=shot_cfg.bullet_speed,
            angle_deg=angle,
            bullet_kind=bullet_kind,
        )


# ========== 角色专属射击类型 ==========

@option_shot_registry.register(OptionShotKind.REIMU_STYLE)
def _shot_reimu_style(
    state: "GameState",
    option_pos: Tuple[float, float],
    option_index: int,
    option_cfg: "OptionConfig",
    shot_cfg: "ShotConfig",
    is_focusing: bool,
    is_enhanced: bool = False,
) -> None:
    """
    灵梦风格：平时直射，Focus 追踪。
    """
    if is_focusing:
        _shot_homing(state, option_pos, option_index, option_cfg, shot_cfg, is_focusing, is_enhanced)
    else:
        _shot_straight(state, option_pos, option_index, option_cfg, shot_cfg, is_focusing, is_enhanced)


@option_shot_registry.register(OptionShotKind.MARISA_STYLE)
def _shot_marisa_style(
    state: "GameState",
    option_pos: Tuple[float, float],
    option_index: int,
    option_cfg: "OptionConfig",
    shot_cfg: "ShotConfig",
    is_focusing: bool,
    is_enhanced: bool = False,
) -> None:
    """
    魔理沙风格：平时扩散，Focus 直射。
    """
    if is_focusing:
        _shot_straight(state, option_pos, option_index, option_cfg, shot_cfg, is_focusing, is_enhanced)
    else:
        _shot_spread(state, option_pos, option_index, option_cfg, shot_cfg, is_focusing, is_enhanced)


__all__ = [
    "OptionShotKind",
    "option_shot_registry",
    "dispatch_option_shot",
]
