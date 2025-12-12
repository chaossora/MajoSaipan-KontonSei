from __future__ import annotations

from pygame.math import Vector2

from .actor import Actor
from .game_state import GameState
from .registry import Registry
from .components import (
    Position, Velocity, Collider,
    CollisionLayer, Health,
    EnemyTag, EnemyShootingV2,
    EnemyDropConfig, EnemyKind, EnemyKindTag,
)
from .bullet_patterns import BulletPatternConfig, BulletPatternKind, PatternState

# 敌人工厂注册表：使用装饰器自动注册 EnemyKind → spawn 函数
enemy_registry: Registry[EnemyKind] = Registry("enemy")


@enemy_registry.register(EnemyKind.FAIRY_SMALL)
def spawn_fairy_small(state: GameState, x: float, y: float, hp: int = 5) -> Actor:
    """
    小妖精：少量 HP，低掉落
    """
    enemy = Actor()

    enemy.add(Position(x, y))
    enemy.add(Velocity(Vector2(0, 0)))
    enemy.add(EnemyTag())
    enemy.add(EnemyKindTag(EnemyKind.FAIRY_SMALL))
    enemy.add(Health(max_hp=hp, hp=hp))

    enemy.add(Collider(
        radius=10.0,
        layer=CollisionLayer.ENEMY,
        mask=CollisionLayer.PLAYER_BULLET,
    ))

    enemy.add(EnemyShootingV2(
        cooldown=1.2,
        pattern=BulletPatternConfig(
            kind=BulletPatternKind.AIM_PLAYER,
            bullet_speed=220.0,
            damage=1,
        ),
    ))

    # 小妖精：通常只掉 1 个 Power
    enemy.add(EnemyDropConfig(
        power_count=1,
        point_count=0,
        scatter_radius=12.0,
    ))

    state.add_actor(enemy)
    return enemy


@enemy_registry.register(EnemyKind.FAIRY_LARGE)
def spawn_fairy_large(state: GameState, x: float, y: float, hp: int = 15) -> Actor:
    """
    大妖精 / 强杂鱼：更多 HP + 更多掉落
    """
    enemy = Actor()

    enemy.add(Position(x, y))
    enemy.add(Velocity(Vector2(0, 0)))
    enemy.add(EnemyTag())
    enemy.add(EnemyKindTag(EnemyKind.FAIRY_LARGE))
    enemy.add(Health(max_hp=hp, hp=hp))

    enemy.add(Collider(
        radius=14.0,
        layer=CollisionLayer.ENEMY,
        mask=CollisionLayer.PLAYER_BULLET,
    ))

    enemy.add(EnemyShootingV2(
        cooldown=0.8,
        pattern=BulletPatternConfig(
            kind=BulletPatternKind.AIM_PLAYER,
            bullet_speed=260.0,
            damage=1,
        ),
    ))

    # 大妖精：掉落更多 Power 和 Point
    enemy.add(EnemyDropConfig(
        power_count=3,
        point_count=2,
        scatter_radius=18.0,
    ))

    state.add_actor(enemy)
    return enemy


@enemy_registry.register(EnemyKind.MIDBOSS)
def spawn_midboss(state: GameState, x: float, y: float, hp: int = 80) -> Actor:
    """
    小 Boss 模板：高 HP + 大掉落
    """
    enemy = Actor()

    enemy.add(Position(x, y))
    enemy.add(Velocity(Vector2(0, 0)))
    enemy.add(EnemyTag())
    enemy.add(EnemyKindTag(EnemyKind.MIDBOSS))
    enemy.add(Health(max_hp=hp, hp=hp))

    enemy.add(Collider(
        radius=24.0,
        layer=CollisionLayer.ENEMY,
        mask=CollisionLayer.PLAYER_BULLET,
    ))

    # 可以不添加 EnemyShooting，改用专门的脚本系统控制弹幕

    enemy.add(EnemyDropConfig(
        power_count=8,
        point_count=6,
        scatter_radius=32.0,
    ))

    state.add_actor(enemy)
    return enemy
