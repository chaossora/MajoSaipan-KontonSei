# model/systems/boss_hud_system.py
"""
Boss HUD 数据聚合系统（纯脚本驱动模式）。

在纯脚本驱动架构中，大部分 HUD 更新由 TaskContext 原语完成：
- ctx.update_boss_hud(): 更新阶段数、计时器
- ctx.set_spell_card() / ctx.end_spell_card(): 更新符卡状态

此系统仅负责每帧同步 HP 比例和符卡状态。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..components import (
    Health,
    EnemyKind, EnemyKindTag,
    BossState, SpellCardState, BossHudData,
)

if TYPE_CHECKING:
    from ..game_state import GameState


def boss_hud_system(state: GameState, dt: float) -> None:
    """
    Boss HUD 聚合系统：每帧同步 HP 比例和符卡状态。
    
    其他 HUD 字段（phases_remaining, timer_seconds）由脚本通过
    ctx.update_boss_hud() 直接控制。
    """
    for actor in state.actors:
        # 检查是否为 Boss
        kind_tag = actor.get(EnemyKindTag)
        if not kind_tag or kind_tag.kind != EnemyKind.BOSS:
            continue

        hud = actor.get(BossHudData)
        health = actor.get(Health)

        if not hud:
            continue

        # 更新血量百分比
        if health and health.max_hp > 0:
            hud.hp_ratio = health.hp / health.max_hp
        else:
            hud.hp_ratio = 0.0

        # 同步符卡状态（脚本可能已设置，这里确保一致性）
        spell_state = actor.get(SpellCardState)
        if spell_state:
            hud.is_spell_card = True
            hud.spell_name = spell_state.spell_name
            hud.spell_bonus = spell_state.spell_bonus_value
            hud.spell_bonus_available = spell_state.spell_bonus_available
        else:
            hud.is_spell_card = False
            hud.spell_name = ""
            hud.spell_bonus = 0
            hud.spell_bonus_available = True
