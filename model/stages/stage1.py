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
    
    yield 60  # Boss 出场前短暂停顿
    
    yield 60  # Boss 出场前短暂停顿
    
    # 生成 Boss（如果已注册）
    try:
        boss = ctx.spawn_boss(
            "stage1_boss",
            x=center_x,
            y=top_y,
        )
        
        # 等待 Boss 被击败
        from model.components import Health
        while True:
            health = boss.get(Health)
            if health is None or health.hp <= 0:
                break
            yield 1
    except ValueError:
        # Boss 尚未注册，跳过 Boss 阶段
        pass
    
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
