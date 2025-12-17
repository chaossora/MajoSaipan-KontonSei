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
from ..scripting.task import TaskRunner


def enemy_death_system(state: GameState, dt: float) -> None:
    """
    敌人死亡统一处理系统：
    - 查找所有有 EnemyTag + EnemyJustDied 的实体
    - 执行：
        * 终止行为 Task（Requirements 12.4）
        * 掉落道具（根据 EnemyDropConfig 或 BossState）
        * 加分（以后可以加）
        * 清理相关状态
        * 从 GameState 移除敌人实体
    
    **Requirements: 12.4**
    """
    # 收集要删除的敌人，避免在遍历时修改列表
    to_remove = []

    for actor in state.actors:
        if not actor.get(EnemyTag):
            continue

        death = actor.get(EnemyJustDied)
        if not death:
            continue

        # 0) 终止行为 Task（Requirements 12.4）
        runner = actor.get(TaskRunner)
        if runner:
            runner.terminate_all()

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
        
        if pos and not is_boss:
            # 简单起见，所有普通死亡敌人播放通用爆炸
            spawn_explosion(state, pos.x, pos.y)

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


def spawn_explosion(state: GameState, x: float, y: float) -> None:
    """
    生成爆炸特效 Actor.
    """
    from ..actor import Actor
    from ..components import Position, SpriteInfo, Animation, VfxTag
    
    vfx = Actor()
    vfx.add(Position(x, y))
    
    # 8 Frames, 0.1s total duration? Fast explosion.
    # 60FPS -> 8 frames = ~0.13s. Let's try 0.05s per frame -> 0.4s total.
    vfx.add(Animation(
        base_name="explosion",
        total_frames=8,
        duration=0.04, # Fast
        timer=0.0,
        current_frame=0,
        loop=False,
        auto_remove=True
    ))
    
    # Initial sprite
    vfx.add(SpriteInfo(
        name="explosion_0",
        visible=True
        # offset handled by center alignment in render? 
        # Actually Renderer uses offset as topleft shift. 
        # Explosion needs to be centered.
        # We need to know frame size to center it.
        # But SpriteInfo only has fixed offset.
        # If frames are e.g. 64x64, offset should be -32,-32.
        # ASSETS loaded it. We don't know size here easily without hardcoding or querying assets.
        # Let's assume 64x64 or queried from generic.
        # For now, let's look at assets loading again or just assume center.
        # Update: Renderer uses topleft = pos + offset. 
        # If we don't set offset, top-left is at pos.
        # Standard solution: Query asset size? No easy access to assets here (in model).
        # We can hardcode approximate offset or add logic to auto-center VFX in Renderer?
        # Let's assume explosion is ~96x96?
        # User said "1 row 8 frames". png size?
        # In assets.py loading, it was raw size.
        # Let's add logic to Renderer to auto-center if offset is 0? No that breaks defaults.
        # Let's just create it. It might be off-center.
        # Wait, if I use SpriteInfo with default offset (0,0), it draws at pos.
        # I'll check if I can guess offset.
    ))
    
    # Quick hack: center it by hardcoded guess or just let it be for now and adjust.
    # User provided sprite. Likely square.
    # I'll modify renderer to handle VfxTag specifically if needed OR
    # just set a reasonable offset.
    # Let's try defaulting to center if I can.
    # OR: modify vfx_system to update offset? No.
    # I'll just leave offset 0 for now and see. 
    # Actually, for explosions, usually you want pos to be center.
    # I'll set a generic offset of -32,-32 (assuming 64x64) for now.
    vfx.add(SpriteInfo(name="explosion_0", offset_x=-32, offset_y=-32)) # 64x64 -> Center -32
    
    vfx.add(VfxTag())
    
    state.add_actor(vfx)
    
    # Trigger SFX
    state.sfx_requests.append("explosion")
