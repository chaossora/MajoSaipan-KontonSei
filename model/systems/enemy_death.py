from __future__ import annotations

import random
from pygame.math import Vector2

from ..game_state import GameState, spawn_item
from ..components import (
    Position,
    EnemyTag,
    EnemyJustDied,
    EnemyDropConfig,
    ItemType,
    EnemyKind, EnemyKindTag, BossState,
)


def enemy_death_system(state: GameState, dt: float) -> None:
    """
    敌人死亡统一处理系统：
    - 查找所有有 EnemyTag + EnemyJustDied 的实体
    - 执行：
        * 掉落道具（根据 EnemyDropConfig 或 BossState）
        * 加分（以后可以加）
        * 清理相关状态
        * 从 GameState 移除敌人实体
    """
    # 收集要删除的敌人，避免在遍历时修改列表
    to_remove = []

    for actor in state.actors:
        if not actor.get(EnemyTag):
            continue

        death = actor.get(EnemyJustDied)
        if not death:
            continue

        pos = actor.get(Position)

        # 检查是否为 Boss
        kind_tag = actor.get(EnemyKindTag)
        is_boss = kind_tag and kind_tag.kind == EnemyKind.BOSS

        # 1) 处理掉落道具
        if pos:
            if is_boss:
                # Boss 使用 BossState 中的掉落配置
                boss_state = actor.get(BossState)
                if boss_state:
                    _spawn_boss_drops(state, pos.x, pos.y, boss_state)
            else:
                # 普通敌人使用 EnemyDropConfig
                drop = actor.get(EnemyDropConfig)
                if drop:
                    _spawn_drops_for_enemy(state, pos.x, pos.y, drop)

        # 2) 预留：给玩家加分、连击、统计等

        # 3) 标记待删除
        to_remove.append(actor)

    # 执行删除
    for actor in to_remove:
        state.remove_actor(actor)


def _spawn_drops_for_enemy(
    state: GameState,
    cx: float,
    cy: float,
    drop: EnemyDropConfig,
) -> None:
    """
    具体的“根据 DropConfig 生成道具”逻辑，完全在系统里，不放 GameState。
    """
    r = drop.scatter_radius

    # 掉落 Power
    for _ in range(drop.power_count):
        offset_x = random.uniform(-r, r)
        offset_y = random.uniform(-r, r)
        spawn_item(
            state,
            x=cx + offset_x,
            y=cy + offset_y,
            item_type=ItemType.POWER,
            value=1,
        )

    # 掉落 Point
    for _ in range(drop.point_count):
        offset_x = random.uniform(-r, r)
        offset_y = random.uniform(-r, r)
        spawn_item(
            state,
            x=cx + offset_x,
            y=cy + offset_y,
            item_type=ItemType.POINT,
            value=1,
        )


def _spawn_boss_drops(
    state: GameState,
    cx: float,
    cy: float,
    boss_state: BossState,
) -> None:
    """
    Boss 击破时的掉落逻辑：
    - Power、Point 大量掉落
    - 可能掉落 Life、Bomb
    """
    r = 48.0  # Boss 掉落物散布半径较大

    # 掉落 Power
    for _ in range(boss_state.drop_power):
        offset_x = random.uniform(-r, r)
        offset_y = random.uniform(-r, r)
        spawn_item(
            state,
            x=cx + offset_x,
            y=cy + offset_y,
            item_type=ItemType.POWER,
            value=1,
        )

    # 掉落 Point
    for _ in range(boss_state.drop_point):
        offset_x = random.uniform(-r, r)
        offset_y = random.uniform(-r, r)
        spawn_item(
            state,
            x=cx + offset_x,
            y=cy + offset_y,
            item_type=ItemType.POINT,
            value=1,
        )

    # 掉落 Life（残机）
    for _ in range(boss_state.drop_life):
        offset_x = random.uniform(-r * 0.5, r * 0.5)
        offset_y = random.uniform(-r * 0.5, r * 0.5)
        spawn_item(
            state,
            x=cx + offset_x,
            y=cy + offset_y,
            item_type=ItemType.LIFE,
            value=1,
        )

    # 掉落 Bomb
    for _ in range(boss_state.drop_bomb):
        offset_x = random.uniform(-r * 0.5, r * 0.5)
        offset_y = random.uniform(-r * 0.5, r * 0.5)
        spawn_item(
            state,
            x=cx + offset_x,
            y=cy + offset_y,
            item_type=ItemType.BOMB,
            value=1,
        )
