# model/stages/stage1.py
"""
第一关脚本，使用 Task 协程系统。

本模块提供 stage1_script 生成器函数，使用 Task/TaskContext 系统
定义第一关的时间线。

Requirements: 10.1, 10.2, 10.4, 10.5
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Generator

from model.components import EnemyKind
from model.scripting.behaviors import (
    fairy_behavior_1,
    fairy_behavior_sine,
    fairy_behavior_straight,
    fairy_behavior_diagonal,
)

if TYPE_CHECKING:
    from model.scripting.context import TaskContext
    from model.game_state import GameState


def stage1_script(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    第一关主脚本。
    
    时间线：
    - 第 1 波 (t=5s): 5 只小妖精横排
    - 第 2 波 (t=10s): 6 只小妖精纵队，正弦摇摆
    - 第 3 波 (t=15s): 5 只大妖精扇形排列
    - 第 4 波 (t=20s): 12 只小妖精螺旋排列，斜向移动
    - Boss (敌人清空后): 第一关 Boss
    
    Requirements: 10.1, 10.2, 10.4, 10.5
    """
    width = ctx.state.width
    height = ctx.state.height
    center_x = width / 2
    top_y = 120
    
    # 开场延迟
    yield 300  # 5 秒 (60 FPS)

    # 第 1 波：5 只小妖精横排（左侧）
    for i in range(5):
        ctx.spawn_enemy(
            EnemyKind.FAIRY_SMALL,
            x=80.0 + i * 40.0,
            y=top_y,
            behavior=fairy_behavior_straight,
        )
    
    yield 300  # 等待 5 秒
    
    # 第 2 波：6 只小妖精纵队，正弦摇摆
    for i in range(6):
        ctx.spawn_enemy(
            EnemyKind.FAIRY_SMALL,
            x=center_x,
            y=top_y - 40 + i * 24.0,
            behavior=fairy_behavior_sine,
        )
    
    yield 300  # 等待 5 秒
    
    # 第 3 波：5 只大妖精扇形排列
    base_angle = 90.0  # 度，朝下
    angle_step = 15.0
    radius = 80.0
    for i in range(5):
        angle = base_angle + (i - 2) * angle_step  # -30, -15, 0, 15, 30 度偏移
        rad = math.radians(angle)
        x = center_x + radius * math.cos(rad)
        y = top_y + 40 + radius * math.sin(rad)
        ctx.spawn_enemy(
            EnemyKind.FAIRY_LARGE,
            x=x,
            y=y,
            behavior=fairy_behavior_1,
        )
    
    yield 300  # 等待 5 秒
    
    # 第 4 波：12 只小妖精螺旋排列，斜向移动
    spiral_radius = 40.0
    radius_step = 6.0
    angle_deg = 0.0
    angle_step_deg = 30.0
    for i in range(12):
        r = spiral_radius + i * radius_step
        rad = math.radians(angle_deg + i * angle_step_deg)
        x = center_x + r * math.cos(rad)
        y = top_y + 80 + r * math.sin(rad)
        ctx.spawn_enemy(
            EnemyKind.FAIRY_SMALL,
            x=x,
            y=y,
            behavior=fairy_behavior_diagonal,
        )

    yield 120  # 等待 2 秒
    
    # 等待所有敌人被清空
    while ctx.enemies_alive() > 0:
        yield 1
    
    # Timeline 03: Boss Spawn
    # ==========================
    
    # Dialogue
    yield from ctx.wait(3.0)
    yield from run_dialogue(ctx)

    # Boss Cut-in (Disabled)
    # ctx.state.cutin.start(name="boss_cutin", control_bgm=True)
    # yield from ctx.wait(2.5)

    # Boss Battle
    try:
        boss = ctx.spawn_boss(
            "stage1_boss",
            x=center_x,
            y=top_y,
        )
        
        # 等待 Boss 脚本执行完毕 (即所有阶段完成)
        # 注意: 即使 HP<=0，只要脚本还在运行(如转阶段)，就继续等待
        from model.scripting.task import TaskRunner
        runner = boss.get(TaskRunner)
        while runner and runner.has_active_tasks():
            yield 1
    except ValueError:
        # Boss 尚未注册，跳过 Boss 阶段
        pass
    
    # Wait a bit before dialogue
    yield from ctx.wait(1.0)
    
    # Post Battle Dialogue
    yield from run_post_battle_dialogue(ctx)
    
    # Remove boss & Spawn Items
    if 'boss' in locals() and boss:
        # Get boss position
        from model.components import Position
        pos = boss.get(Position)
        bx, by = (pos.x, pos.y) if pos else (center_x, top_y)
        
        ctx.state.remove_actor(boss)
        spawn_stage_clear_items(ctx, bx, by)
        
        # Explosion SFX
        ctx.play_sound("explosion")

    
    # 关卡完成
    ctx.state.stage.finished = True


def setup_stage1(state: "GameState") -> None:
    """
    使用 Task 协程系统初始化第一关。
    
    此函数创建 StageRunner 并启动 stage1_script Task。
    
    Args:
        state: 要初始化关卡的 GameState
    
    Requirements: 10.1
    """
    from model.stage import StageState
    from model.scripting.stage_runner import StageRunner
    
    # 创建关卡状态
    state.stage = StageState()
    
    # 创建并附加关卡执行器
    stage_runner = StageRunner()
    state.stage_runner = stage_runner
    
    # 启动关卡脚本
    stage_runner.start_stage(state, stage1_script, rng_seed=0)


def run_dialogue(ctx):
    """Run the boss pre-fight dialogue."""
    from model.components import DialogueLine
    
    dialogue = ctx.state.dialogue
    
    # Setup Lines
    dialogue.lines = [
        DialogueLine(speaker="player", name="Ema", text="小雪！！"),
        DialogueLine(speaker="boss", name="Yuki", text="......"),
        DialogueLine(speaker="player", name="Ema", text="为什么...", variant="2"),
        DialogueLine(speaker="boss", name="Yuki", text="那么就...开始吧。", variant="2"),
    ]
    dialogue.current_index = 0
    dialogue.active = True
    dialogue.finished = False
    
       # Wait for dialogue to finish (TaskRunner pauses during dialogue)
    while ctx.state.dialogue.active or ctx.state.dialogue.closing:
        yield 1


def run_post_battle_dialogue(ctx):
    """Run the boss post-fight dialogue."""
    from model.components import DialogueLine
    
    dialogue = ctx.state.dialogue
    
    # Setup Lines
    dialogue.lines = [
        DialogueLine(speaker="boss", name="Yuki", text="......", variant="3", layout="center"),
        DialogueLine(speaker="boss", name="Yuki", text="谢谢你，艾玛。", variant="4", layout="center"),
    ]
    dialogue.current_index = 0
    dialogue.active = True
    dialogue.finished = False
    
    # Wait for dialogue
    while ctx.state.dialogue.active or ctx.state.dialogue.closing:
        yield 1


def spawn_stage_clear_items(ctx, x: float, y: float):
    """Spawn XP items after boss defeat."""
    from model.actor import Actor
    from model.components import (
        Position, Velocity, SpriteInfo, Collider, CollisionLayer, 
        Item, ItemType, ItemCollectState
    )
    from pygame.math import Vector2
    import random
    
    for _ in range(20):
        item = Actor()
        item.add(Position(x, y))
        
        # Random velocity
        angle = random.uniform(0, 360)
        speed = random.uniform(100, 300)
        vx = speed * random.uniform(-1, 1) # simple scatter
        vy = speed * random.uniform(-1, 1)
        
        item.add(Velocity(Vector2(vx, vy)))
        item.add(SpriteInfo("item_exp_large"))
        item.add(Collider(12.0, CollisionLayer.ITEM, CollisionLayer.PLAYER))
        item.add(Item(ItemType.POINT, 1000)) # Using POINT as generic XP/Score for now
        item.add(ItemCollectState.NONE)
        
        ctx.state.add_actor(item)
