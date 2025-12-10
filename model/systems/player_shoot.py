from __future__ import annotations

from ..game_state import GameState
from ..actor import Actor
from ..components import (
    Position,
    Shooting,
    FocusState,
    ShotConfig,
    ShotOriginOffset,
    InputState,
    OptionConfig,
    OptionState,
    GrazeEnergy,
)
from ..game_config import PlayerConfig
from ..shot_handlers import dispatch_player_shot, dispatch_enhanced_player_shot
from ..option_shot_handlers import dispatch_option_shot
from ..character import EnhancedShotConfig


def player_shoot_system(state: GameState, dt: float) -> None:
    """
    玩家射击系统：读取 ShotConfig / ShotOriginOffset / Shooting。
    包含主机和子机的射击逻辑，支持增强状态。
    """
    player = state.get_player()
    if not player:
        return

    pos = player.get(Position)
    shooting = player.get(Shooting)
    focus_state = player.get(FocusState)
    shot_cfg = player.get(ShotConfig)
    shot_origin = player.get(ShotOriginOffset)
    graze_energy = player.get(GrazeEnergy)
    enhanced_shot_cfg = player.get(EnhancedShotConfig)

    inp = player.get(InputState)

    if not (pos and shooting and focus_state and shot_cfg and inp):
        return

    # 冷却计时
    shooting.timer = max(0.0, shooting.timer - dt)
    if not inp.shoot or shooting.timer > 0.0:
        return

    # 判断是否处于增强状态
    is_enhanced = graze_energy is not None and graze_energy.is_enhanced

    # 主机射击
    if is_enhanced and enhanced_shot_cfg:
        dispatch_enhanced_player_shot(state, shot_cfg, enhanced_shot_cfg, pos, shot_origin, focus_state)
    else:
        dispatch_player_shot(state, shot_cfg, pos, shot_origin, focus_state)

    # 子机射击
    _fire_options(state, player, shot_cfg, focus_state, is_enhanced, enhanced_shot_cfg)

    shooting.timer = shot_cfg.cooldown


def _fire_options(
    state: GameState,
    player: Actor,
    shot_cfg: ShotConfig,
    focus_state: FocusState,
    is_enhanced: bool = False,
    enhanced_shot_cfg: EnhancedShotConfig = None,
) -> None:
    """
    子机射击：遍历激活的子机，通过注册表分发射击行为。
    支持不同角色不同的射击类型，以及 Focus 状态依赖行为。
    """
    option_state = player.get(OptionState)
    option_cfg = player.get(OptionConfig)

    if not (option_state and option_cfg):
        return

    is_focusing = focus_state.is_focusing if focus_state else False

    # 计算增强伤害倍率（用于子机）
    damage_multiplier = 1.0
    if is_enhanced and enhanced_shot_cfg:
        damage_multiplier = enhanced_shot_cfg.option_damage_multiplier

    # 为每个激活的子机分发射击
    for i in range(option_state.active_count):
        if i >= len(option_state.current_positions):
            continue

        pos = option_state.current_positions[i]
        dispatch_option_shot(
            state=state,
            option_pos=(pos[0], pos[1]),
            option_index=i,
            option_cfg=option_cfg,
            shot_cfg=shot_cfg,
            is_focusing=is_focusing,
            is_enhanced=is_enhanced,
            damage_multiplier=damage_multiplier,
        )
