from __future__ import annotations

from pygame.math import Vector2

from ..game_state import GameState, spawn_player_bullet_with_velocity
from ..actor import Actor
from ..components import (
    Position,
    FocusState,
    ShotOriginOffset,
    InputState,
    OptionConfig,
    OptionState,
    GrazeEnergy,
    PlayerShotPattern,
    PlayerBulletKind,
    EnemyTag,
)
from ..player_shot_patterns import PlayerShotPatternConfig, execute_player_shot
from ..option_shot_handlers import execute_option_shot


def player_shoot_system(state: GameState, dt: float) -> None:
    """玩家射击系统：使用 PlayerShotPattern 组件"""
    player = state.get_player()
    if not player:
        return

    pos = player.get(Position)
    focus_state = player.get(FocusState)
    shot_origin = player.get(ShotOriginOffset)
    graze_energy = player.get(GrazeEnergy)
    inp = player.get(InputState)
    shot_pattern = player.get(PlayerShotPattern)

    if not (pos and focus_state and inp and shot_pattern):
        return

    is_enhanced = graze_energy is not None and graze_energy.is_enhanced
    is_focusing = focus_state.is_focusing

    _fire_with_pattern(state, player, pos, shot_pattern, shot_origin, is_focusing, is_enhanced, inp, dt)


def _fire_with_pattern(
    state: GameState,
    player: Actor,
    pos: Position,
    shot_pattern: PlayerShotPattern,
    shot_origin: ShotOriginOffset,
    is_focusing: bool,
    is_enhanced: bool,
    inp: InputState,
    dt: float,
) -> None:
    """使用新版 PlayerShotPattern 射击"""
    config: PlayerShotPatternConfig = shot_pattern.pattern

    shot_pattern.timer = max(0.0, shot_pattern.timer - dt)
    if not inp.shoot or shot_pattern.timer > 0.0:
        return

    offset = shot_origin.bullet_spawn_offset_y if shot_origin else 16.0
    spawn_x = pos.x
    spawn_y = pos.y - offset

    # 执行射击模式，只返回数据
    results = execute_player_shot(config, is_focusing, is_enhanced)

    # 计算伤害值和子弹类型
    if is_enhanced:
        damage = int(config.damage * config.enhanced_damage_multiplier)
        kind = PlayerBulletKind.MAIN_ENHANCED
    else:
        damage = config.damage
        kind = PlayerBulletKind.MAIN_NORMAL

    # 在此统一生成主机子弹实体
    for shot in results:
        spawn_player_bullet_with_velocity(
            state,
            spawn_x + shot.offset.x,
            spawn_y + shot.offset.y,
            shot.velocity,
            damage,
            kind,
        )

    # 计算冷却时间（应用强化倍率）
    base_cooldown = config.cooldown
    if is_enhanced:
        base_cooldown *= config.enhanced_cooldown_multiplier
    shot_pattern.timer = base_cooldown

    # 处理子机射击
    _fire_options_new(state, player, config, pos, is_focusing, is_enhanced)


def _fire_options_new(
    state: GameState,
    player: Actor,
    shot_config: PlayerShotPatternConfig,
    player_pos: Position,
    is_focusing: bool,
    is_enhanced: bool,
) -> None:
    """子机射击（新版）"""
    option_state = player.get(OptionState)
    option_cfg = player.get(OptionConfig)

    if not (option_state and option_cfg):
        return

    # 计算伤害
    base_damage = option_cfg.base_damage
    damage_ratio = option_cfg.damage_ratio
    if is_enhanced:
        damage_ratio *= shot_config.enhanced_damage_multiplier
    damage = max(1, int(base_damage * damage_ratio))

    if is_focusing:
        bullet_kind = PlayerBulletKind.OPTION_TRACKING
    else:
        bullet_kind = PlayerBulletKind.OPTION_ENHANCED if is_enhanced else PlayerBulletKind.OPTION_NORMAL

    for i in range(option_state.active_count):
        if i >= len(option_state.current_positions):
            continue

        opt_pos = option_state.current_positions[i]

        # 计算追踪目标角度（查找最近敌人）
        target_angle = _find_nearest_enemy_angle(state, opt_pos[0], opt_pos[1])

        # 计算实际子弹速度（应用强化倍率）
        effective_speed = option_cfg.bullet_speed
        if is_enhanced:
             effective_speed *= shot_config.enhanced_speed_multiplier

        # 执行射击模式 - 只返回数据
        results = execute_option_shot(
            kind=option_cfg.option_shot_kind,
            speed=effective_speed,
            is_focusing=is_focusing,
            target_angle=target_angle,
        )

        # 在此统一生成子机子弹实体
        for shot in results:
            spawn_player_bullet_with_velocity(
                state,
                opt_pos[0] + shot.offset.x,
                opt_pos[1] + shot.offset.y,
                shot.velocity,
                damage,
                bullet_kind,
            )


def _find_nearest_enemy_angle(state: GameState, x: float, y: float) -> float | None:
    """查找最近敌人的角度"""
    nearest_pos = None
    min_dist_sq = float('inf')

    for actor in state.actors:
        if not actor.has(EnemyTag):
            continue
        epos = actor.get(Position)
        if not epos:
            continue
        dx = epos.x - x
        dy = epos.y - y
        dist_sq = dx * dx + dy * dy
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            nearest_pos = epos

    if nearest_pos is None:
        return None

    to_enemy = Vector2(nearest_pos.x - x, nearest_pos.y - y)
    if to_enemy.length_squared() < 1e-9:
        return None

    # as_polar() 返回 (长度, 角度)
    # pygame 角度：向右=0°，向下=90°，向上=-90°
    # 我们需要：向上=0°，向右=90°（给 Vector2(0,-speed).rotate() 用）
    # 转换公式：result = pygame_angle + 90
    _, pygame_angle = to_enemy.as_polar()
    return pygame_angle + 90
