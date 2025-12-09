# model/systems/boss_hud_system.py
"""
Boss HUD 数据聚合系统：
- 收集 Boss 血量、阶段、符卡名、计时器
- 写入 BossHudData 供渲染器使用
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
    Boss HUD 聚合系统：每帧更新 BossHudData 组件。
    """
    for actor in state.actors:
        # 检查是否为 Boss
        kind_tag = actor.get(EnemyKindTag)
        if not kind_tag or kind_tag.kind != EnemyKind.BOSS:
            continue

        hud = actor.get(BossHudData)
        boss_state = actor.get(BossState)
        health = actor.get(Health)

        if not (hud and boss_state and health):
            continue

        # 更新血量百分比
        if health.max_hp > 0:
            hud.hp_ratio = health.hp / health.max_hp
        else:
            hud.hp_ratio = 0.0

        # 更新剩余阶段数（用于显示星星）
        hud.phases_remaining = len(boss_state.phases) - boss_state.current_phase_index

        # 更新计时器
        hud.timer_seconds = max(0.0, boss_state.phase_timer)

        # 更新符卡状态
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

        # 阶段转换期间隐藏 HUD（可选）
        hud.visible = not boss_state.phase_transitioning
