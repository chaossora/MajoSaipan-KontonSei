# model/systems/bomb_hit_system.py
"""
Bomb 命中系统：处理 Bomb 与敌人/敌弹的碰撞。

东方风格 Bomb 机制：
- 普通杂兵：Bomb 命中即死
- Boss 非符卡阶段：每帧伤害上限（bomb_damage_cap）
- Boss 符卡阶段：可配置完全免疫（bomb_spell_immune=True）
- 生存符卡（invulnerable=True）：完全免疫
"""
from __future__ import annotations

from typing import Set, TYPE_CHECKING

from ..actor import Actor
from ..components import (
    Health, EnemyJustDied,
    EnemyKind, EnemyKindTag,
    BossState, SpellCardState,
)
from ..collision_events import (
    CollisionEvents,
    BombHitEnemy,
    BombClearedEnemyBullet,
)

if TYPE_CHECKING:
    from ..game_state import GameState


def bomb_hit_system(state: GameState, dt: float) -> None:
    """
    处理 Bomb 相关碰撞事件：清弹与炸敌。
    """
    events: CollisionEvents = state.collision_events
    to_remove: Set[Actor] = set()

    # 清除敌弹
    for ev in events.bomb_clears_enemy_bullet:
        to_remove.add(ev.bullet)

    # 对敌人造成伤害
    for ev in events.bomb_hits_enemy:
        _apply_bomb_damage(ev.enemy)

    for actor in to_remove:
        state.remove_actor(actor)


def _apply_bomb_damage(enemy: Actor) -> None:
    """
    应用 Bomb 伤害到敌人。

    根据敌人类型决定伤害方式：
    - 普通敌人：直接击杀
    - Boss：应用伤害上限，考虑符卡免疫
    """
    health = enemy.get(Health)
    if not health:
        return

    # 检查是否为 Boss
    kind_tag = enemy.get(EnemyKindTag)
    is_boss = kind_tag and kind_tag.kind == EnemyKind.BOSS

    if is_boss:
        _apply_boss_bomb_damage(enemy, health)
    else:
        _apply_normal_enemy_bomb_damage(enemy, health)


def _apply_normal_enemy_bomb_damage(enemy: Actor, health: Health) -> None:
    """
    普通敌人：Bomb 命中即死。
    """
    health.hp = 0

    if not enemy.get(EnemyJustDied):
        enemy.add(EnemyJustDied(by_player_bullet=False))


def _apply_boss_bomb_damage(enemy: Actor, health: Health) -> None:
    """
    Boss 敌人：应用东方风格的 Bomb 伤害机制。

    1. 生存符卡（invulnerable）：完全免疫
    2. 符卡阶段 + bomb_spell_immune：完全免疫
    3. 其他情况：应用 bomb_damage_cap 伤害
    """
    boss_state = enemy.get(BossState)
    spell_state = enemy.get(SpellCardState)

    # 检查是否免疫 Bomb
    if spell_state:
        # 生存符卡：无敌状态，完全免疫
        if spell_state.invulnerable:
            return

        # 符卡期间 + 配置为免疫 Bomb
        if boss_state and boss_state.bomb_spell_immune:
            return

        # 符卡被 Bomb 命中：失去奖励资格
        spell_state.spell_bonus_available = False

    # 计算实际伤害
    damage = 9999  # 默认高伤害
    if boss_state:
        damage = min(damage, boss_state.bomb_damage_cap)

    # 应用伤害
    health.hp = max(0, health.hp - damage)

    # 注意：Boss 死亡由 boss_phase_system 处理，此处不添加 EnemyJustDied
