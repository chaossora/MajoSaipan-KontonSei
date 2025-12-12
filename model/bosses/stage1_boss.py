# model/bosses/stage1_boss.py
"""
第一关 Boss 工厂函数。
使用纯组件组合方式定义 Boss（类似 spawn_fairy_small 模式）。
现在支持 pattern_combinators 实现更丰富的弹幕时序。
"""
from __future__ import annotations

from pygame.math import Vector2

from ..actor import Actor
from ..game_state import GameState
from ..components import (
    Position, Velocity, SpriteInfo, Collider, Health,
    CollisionLayer, EnemyTag, EnemyKindTag, EnemyKind,
    EnemyShootingV2,
    PhaseType, BossPhase, BossState, BossMovementState, BossHudData,
)
from ..bullet_patterns import BulletPatternConfig, BulletPatternKind
from ..pattern_combinators import stagger, repeat
from ..systems.stage_system import boss_registry


@boss_registry.register("stage1_boss")
def spawn_stage1_boss(state: GameState, x: float, y: float) -> Actor:
    """
    Stage 1 Boss：妖精大王
    - 2 阶段：1 非符 + 1 符卡
    - 非符：stagger N_WAY（错峰发射）
    - 符卡：repeat SPIRAL（重复+旋转）
    """
    boss = Actor()

    # ====== 基础组件（复用现有） ======
    boss.add(Position(x, y))
    boss.add(Velocity(Vector2(0, 0)))
    boss.add(EnemyTag())
    boss.add(EnemyKindTag(EnemyKind.BOSS))

    # 第一阶段的初始 HP
    first_phase_hp = 500
    boss.add(Health(max_hp=first_phase_hp, hp=first_phase_hp))

    boss.add(Collider(
        radius=28.0,
        layer=CollisionLayer.ENEMY,
        mask=CollisionLayer.PLAYER_BULLET,
    ))

    boss.add(SpriteInfo(
        name="boss_stage1",
        offset_x=-32,
        offset_y=-32,
    ))

    # ====== Boss 专用组件 ======

    # 非符弹幕基础配置
    non_spell_base = BulletPatternConfig(
        kind=BulletPatternKind.N_WAY,
        bullet_speed=180.0,
        damage=1,
        count=7,
        spread_deg=80.0,
    )

    # 符卡弹幕基础配置
    spell_base = BulletPatternConfig(
        kind=BulletPatternKind.SPIRAL,
        bullet_speed=150.0,
        damage=1,
        count=8,
        spin_speed_deg=45.0,
    )

    # 定义阶段列表
    phases = [
        # 非符 1: stagger N_WAY 弹幕（错峰发射，每颗延迟 0.03 秒）
        BossPhase(
            phase_type=PhaseType.NON_SPELL,
            hp=500,
            duration=30.0,
            pattern=stagger(non_spell_base, delay_per_bullet=0.03),
        ),
        # 符卡 1: repeat SPIRAL 弹幕（3 轮，每轮间隔 0.12 秒，每轮旋转 15 度）
        BossPhase(
            phase_type=PhaseType.SPELL_CARD,
            hp=800,
            duration=45.0,
            spell_name="妖符「星屑乱舞」",
            spell_bonus=50000,
            damage_multiplier=0.8,
            pattern=repeat(spell_base, times=3, interval=0.12, rotate=15.0),
        ),
    ]

    boss.add(BossState(
        boss_name="妖精大王",
        phases=phases,
        current_phase_index=0,
        phase_timer=phases[0].duration,
        drop_power=16,
        drop_point=24,
        drop_life=0,
        drop_bomb=0,
    ))

    boss.add(BossMovementState(
        y_min=50.0,
        y_max=180.0,
    ))

    boss.add(BossHudData(
        boss_name="妖精大王",
        hp_ratio=1.0,
        phases_remaining=len(phases),
        timer_seconds=phases[0].duration,
        visible=True,
    ))

    # 使用 EnemyShootingV2（复用现有射击系统）
    first_phase = phases[0]
    if first_phase.pattern:
        boss.add(EnemyShootingV2(
            cooldown=0.6,
            pattern=first_phase.pattern,
        ))

    state.add_actor(boss)
    return boss

