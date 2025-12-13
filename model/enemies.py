from __future__ import annotations

from random import Random
from typing import Callable, Generator, Optional

from pygame.math import Vector2

from .actor import Actor
from .game_state import GameState
from .registry import Registry
from .components import (
    Position, Velocity, Collider,
    CollisionLayer, Health,
    EnemyTag,
    EnemyDropConfig, EnemyKind, EnemyKindTag,
)

# 敌人工厂注册表：使用装饰器自动注册 EnemyKind → spawn 函数
enemy_registry: Registry[EnemyKind] = Registry("enemy")


def _attach_behavior(
    state: GameState,
    enemy: Actor,
    behavior: Callable[..., Generator[int, None, None]],
    rng: Optional[Random] = None,
) -> None:
    """
    Attach a behavior Task to an enemy.
    
    This helper function adds a TaskRunner to the enemy and starts
    the behavior Task.
    
    Args:
        state: GameState reference
        enemy: The enemy Actor to attach behavior to
        behavior: Task generator function for enemy behavior
        rng: Optional RNG for determinism (creates new one if None)
    
    **Requirements: 12.1**
    """
    from model.scripting.task import TaskRunner
    from model.scripting.context import TaskContext
    
    # Add TaskRunner component if not present
    runner = enemy.get(TaskRunner)
    if runner is None:
        runner = TaskRunner()
        enemy.add(runner)
    
    # Create context for the enemy's behavior
    enemy_ctx = TaskContext(
        state=state,
        owner=enemy,
        rng=rng if rng is not None else Random(),
    )
    
    # Start the behavior task
    runner.start_task(behavior, enemy_ctx)


@enemy_registry.register(EnemyKind.FAIRY_SMALL)
def spawn_fairy_small(
    state: GameState,
    x: float,
    y: float,
    hp: int = 5,
    behavior: Optional[Callable[..., Generator[int, None, None]]] = None,
    rng: Optional[Random] = None,
) -> Actor:
    """
    小妖精：少量 HP，低掉落
    
    Args:
        state: GameState reference
        x: X position to spawn
        y: Y position to spawn
        hp: Hit points (default 5)
        behavior: Optional Task generator function for enemy behavior
        rng: Optional RNG for determinism
    
    Returns:
        The created enemy Actor
    
    **Requirements: 12.1**
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

    # 小妖精：通常只掉 1 个 Power
    enemy.add(EnemyDropConfig(
        power_count=1,
        point_count=0,
        scatter_radius=12.0,
    ))

    state.add_actor(enemy)
    
    # Attach behavior Task if provided
    if behavior is not None:
        _attach_behavior(state, enemy, behavior, rng)
    
    return enemy


@enemy_registry.register(EnemyKind.FAIRY_LARGE)
def spawn_fairy_large(
    state: GameState,
    x: float,
    y: float,
    hp: int = 15,
    behavior: Optional[Callable[..., Generator[int, None, None]]] = None,
    rng: Optional[Random] = None,
) -> Actor:
    """
    大妖精 / 强杂鱼：更多 HP + 更多掉落
    
    Args:
        state: GameState reference
        x: X position to spawn
        y: Y position to spawn
        hp: Hit points (default 15)
        behavior: Optional Task generator function for enemy behavior
        rng: Optional RNG for determinism
    
    Returns:
        The created enemy Actor
    
    **Requirements: 12.1**
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

    # 大妖精：掉落更多 Power 和 Point
    enemy.add(EnemyDropConfig(
        power_count=3,
        point_count=2,
        scatter_radius=18.0,
    ))

    state.add_actor(enemy)
    
    # Attach behavior Task if provided
    if behavior is not None:
        _attach_behavior(state, enemy, behavior, rng)
    
    return enemy


@enemy_registry.register(EnemyKind.MIDBOSS)
def spawn_midboss(
    state: GameState,
    x: float,
    y: float,
    hp: int = 80,
    behavior: Optional[Callable[..., Generator[int, None, None]]] = None,
    rng: Optional[Random] = None,
) -> Actor:
    """
    小 Boss 模板：高 HP + 大掉落
    
    Args:
        state: GameState reference
        x: X position to spawn
        y: Y position to spawn
        hp: Hit points (default 80)
        behavior: Optional Task generator function for enemy behavior
        rng: Optional RNG for determinism
    
    Returns:
        The created enemy Actor
    
    **Requirements: 12.1**
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
    
    # Attach behavior Task if provided
    if behavior is not None:
        _attach_behavior(state, enemy, behavior, rng)
    
    return enemy
