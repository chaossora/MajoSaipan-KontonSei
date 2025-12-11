from __future__ import annotations

from ..game_state import GameState, spawn_enemy_bullet
from ..components import Position, EnemyShootingV2, EnemyTag
from ..bullet_patterns import execute_pattern, BulletPatternConfig, PatternState


def enemy_shoot_system(state: GameState, dt: float) -> None:
    """
    敌弹系统：使用 EnemyShootingV2 + BulletPatternConfig 支持丰富弹幕模式。
    """
    for actor in state.actors:
        if not actor.has(EnemyTag):
            continue

        pos = actor.get(Position)
        if not pos:
            continue

        cfg = actor.get(EnemyShootingV2)
        if not cfg:
            continue

        cfg.timer -= dt
        if cfg.timer > 0.0:
            continue

        cfg.timer = cfg.cooldown

        pattern_cfg: BulletPatternConfig = cfg.pattern
        pattern_state: PatternState | None = cfg.state

        # 执行弹幕模式，获取所有 ShotData
        shots = execute_pattern(state, pos, pattern_cfg, pattern_state)

        # 生成所有子弹
        for shot in shots:
            spawn_enemy_bullet(
                state,
                x=pos.x + shot.offset.x,
                y=pos.y + shot.offset.y,
                velocity=shot.velocity,
                damage=pattern_cfg.damage,
            )
