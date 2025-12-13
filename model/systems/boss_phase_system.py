# model/systems/boss_phase_system.py
"""
Boss 阶段管理系统：
- 检测 HP 耗尽或计时器到期
- 触发阶段转换（清屏、初始化下一阶段）
- 最终阶段结束时标记 Boss 死亡
- 启动和终止阶段 Task（Requirements 11.1, 11.2, 11.3, 11.4）
"""
from __future__ import annotations

from random import Random
from typing import TYPE_CHECKING

from ..components import (
    EnemyKind, EnemyKindTag, Health, EnemyShootingV2,
    BossState, SpellCardState, BossHudData,
    EnemyJustDied, EnemyBulletTag, PhaseType, PlayerScore,
    PlayerTag,
)
from ..scripting.task import TaskRunner
from ..scripting.context import TaskContext

if TYPE_CHECKING:
    from ..game_state import GameState
    from ..actor import Actor


# 阶段转换持续时间（秒）
TRANSITION_DURATION = 1.0


def boss_phase_system(state: GameState, dt: float) -> None:
    """
    Boss 阶段系统：处理阶段计时、转换和死亡。
    
    Requirements:
    - 11.1: WHEN Boss 进入新阶段 THEN 系统 SHALL 启动该阶段的 Task 脚本
    - 11.2: WHEN 符卡 Task 执行弹幕脚本 THEN 系统 SHALL 按脚本生成子弹
    - 11.3: WHEN Boss 血量耗尽或超时 THEN 系统 SHALL 终止当前阶段 Task 并切换到下一阶段
    - 11.4: WHEN 所有阶段完成 THEN 系统 SHALL 标记 Boss 被击败
    """
    for actor in state.actors:
        # 检查是否为 Boss
        kind_tag = actor.get(EnemyKindTag)
        if not kind_tag or kind_tag.kind != EnemyKind.BOSS:
            continue

        boss_state = actor.get(BossState)
        health = actor.get(Health)
        if not (boss_state and health):
            continue

        # 正在阶段转换期间
        if boss_state.phase_transitioning:
            _handle_transition(state, actor, boss_state, health, dt)
            continue
        
        # Check if current phase needs initialization (Task not started yet)
        if not boss_state.phase_initialized and len(boss_state.phases) > 0:
            _init_current_phase(state, actor, boss_state, health)
            continue

        # 更新阶段计时器
        boss_state.phase_timer -= dt

        # 检查阶段结束条件
        timeout = boss_state.phase_timer <= 0
        hp_depleted = health.hp <= 0

        if timeout or hp_depleted:
            _advance_phase(state, actor, boss_state, health, timeout)


def _handle_transition(
    state: GameState,
    actor: Actor,
    boss_state: BossState,
    health: Health,
    dt: float
) -> None:
    """处理阶段转换期间的逻辑。"""
    boss_state.transition_timer -= dt

    if boss_state.transition_timer <= 0:
        # 转换结束，初始化新阶段
        boss_state.phase_transitioning = False
        _init_current_phase(state, actor, boss_state, health)


def _advance_phase(
    state: GameState,
    actor: Actor,
    boss_state: BossState,
    health: Health,
    was_timeout: bool
) -> None:
    """
    推进到下一阶段，或标记 Boss 死亡。
    
    Requirements:
    - 11.3: WHEN Boss 血量耗尽或超时 THEN 系统 SHALL 终止当前阶段 Task 并切换到下一阶段
    - 11.4: WHEN 所有阶段完成 THEN 系统 SHALL 标记 Boss 被击败
    """
    current_phase = boss_state.phases[boss_state.current_phase_index]

    # Terminate the current phase Task (Requirements 11.3)
    _terminate_current_phase_task(actor, boss_state)

    # 处理符卡奖励
    spell_state = actor.get(SpellCardState)
    if spell_state and not was_timeout and spell_state.spell_bonus_available:
        # 击破符卡且未被击中/未 Bomb：获得奖励
        _award_spell_bonus(state, spell_state.spell_bonus_value)

    # 移除符卡状态组件（如果存在）
    if spell_state:
        actor._components.pop(SpellCardState, None)

    # 清除场上所有敌弹
    _clear_enemy_bullets(state)

    # 检查是否为最终阶段
    boss_state.current_phase_index += 1
    if boss_state.current_phase_index >= len(boss_state.phases):
        # Boss 被击破 (Requirements 11.4)
        actor.add(EnemyJustDied(by_player_bullet=True))
        return

    # 进入阶段转换
    boss_state.phase_transitioning = True
    boss_state.transition_timer = TRANSITION_DURATION
    boss_state.phase_initialized = False  # Reset for next phase


def _init_current_phase(
    state: GameState,
    actor: Actor,
    boss_state: BossState,
    health: Health
) -> None:
    """
    初始化当前阶段：更新 HP、计时器、符卡状态，启动阶段 Task。
    
    Requirements:
    - 11.1: WHEN Boss 进入新阶段 THEN 系统 SHALL 启动该阶段的 Task 脚本
    - 11.2: WHEN 符卡 Task 执行弹幕脚本 THEN 系统 SHALL 按脚本生成子弹
    """
    phase = boss_state.phases[boss_state.current_phase_index]

    # 更新 Health 组件
    health.max_hp = phase.hp
    health.hp = phase.hp

    # 更新阶段计时器
    boss_state.phase_timer = phase.duration

    # 如果是符卡阶段，添加 SpellCardState
    if phase.phase_type in (PhaseType.SPELL_CARD, PhaseType.SURVIVAL):
        actor.add(SpellCardState(
            spell_name=phase.spell_name,
            spell_bonus_available=True,
            spell_bonus_value=phase.spell_bonus,
            damage_multiplier=phase.damage_multiplier,
            invulnerable=(phase.phase_type == PhaseType.SURVIVAL),
        ))

    # 更新射击模式（如果阶段有定义 pattern）
    if phase.pattern:
        shooting = actor.get(EnemyShootingV2)
        if shooting:
            shooting.pattern = phase.pattern
            shooting.timer = 0.0  # 重置射击计时器
    
    # Start the phase Task if defined (Requirements 11.1, 11.2)
    _start_phase_task(state, actor, boss_state, phase)
    
    # Mark phase as initialized
    boss_state.phase_initialized = True


def _start_phase_task(
    state: GameState,
    actor: Actor,
    boss_state: BossState,
    phase: "BossPhase"
) -> None:
    """
    Start the phase Task if the phase has a task defined.
    
    Requirements:
    - 11.1: WHEN Boss 进入新阶段 THEN 系统 SHALL 启动该阶段的 Task 脚本
    - 11.2: WHEN 符卡 Task 执行弹幕脚本 THEN 系统 SHALL 按脚本生成子弹
    """
    from ..components import BossPhase
    
    if phase.task is None:
        boss_state.current_phase_task = None
        return
    
    # Ensure the Boss has a TaskRunner
    runner = actor.get(TaskRunner)
    if runner is None:
        runner = TaskRunner()
        actor.add(runner)
    
    # Create a TaskContext for the Boss
    # Use a deterministic RNG seeded from the game state's frame counter
    # This ensures reproducibility for replays
    rng = Random(state.frame)
    ctx = TaskContext(
        state=state,
        owner=actor,
        rng=rng,
    )
    
    # Start the phase Task
    task = runner.start_task(phase.task, ctx)
    boss_state.current_phase_task = task


def _terminate_current_phase_task(
    actor: Actor,
    boss_state: BossState
) -> None:
    """
    Terminate the current phase Task.
    
    Requirements:
    - 11.3: WHEN Boss 血量耗尽或超时 THEN 系统 SHALL 终止当前阶段 Task
    """
    if boss_state.current_phase_task is not None:
        # Mark the task as finished so it will be removed by TaskRunner.tick()
        boss_state.current_phase_task.finished = True
        boss_state.current_phase_task = None


def _clear_enemy_bullets(state: GameState) -> None:
    """清除场上所有敌弹。"""
    to_remove = []
    for actor in state.actors:
        if actor.get(EnemyBulletTag):
            to_remove.append(actor)

    for actor in to_remove:
        state.actors.remove(actor)


def _award_spell_bonus(state: GameState, bonus: int) -> None:
    """给玩家增加符卡奖励分数。"""
    for actor in state.actors:
        if actor.get(PlayerTag):
            score = actor.get(PlayerScore)
            if score:
                score.score += bonus
            break
