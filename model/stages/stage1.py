# model/stages/stage1.py
"""
Stage 1 script using the Task-based stage system.

This module provides the stage1_script generator function that defines
the timeline for Stage 1 using the new Task/TaskContext system.

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
    Stage 1 main script.
    
    Timeline:
    - Wave 1 (t=5s): 5 small fairies in horizontal line
    - Wave 2 (t=10s): 6 small fairies in vertical column with sine movement
    - Wave 3 (t=15s): 5 large fairies in fan pattern
    - Wave 4 (t=20s): 12 small fairies in spiral pattern with diagonal movement
    - Boss (after enemies cleared): Stage 1 Boss
    
    Requirements: 10.1, 10.2, 10.4, 10.5
    """
    width = ctx.state.width
    height = ctx.state.height
    center_x = width / 2
    top_y = 120
    
    # Initial delay before first wave
    yield 300  # 5 seconds at 60 FPS

    # Wave 1: 5 small fairies in horizontal line (left side)
    for i in range(5):
        ctx.spawn_enemy(
            EnemyKind.FAIRY_SMALL,
            x=80.0 + i * 40.0,
            y=top_y,
            behavior=fairy_behavior_straight,
        )
    
    yield 300  # Wait 5 seconds
    
    # Wave 2: 6 small fairies in vertical column with sine movement
    for i in range(6):
        ctx.spawn_enemy(
            EnemyKind.FAIRY_SMALL,
            x=center_x,
            y=top_y - 40 + i * 24.0,
            behavior=fairy_behavior_sine,
        )
    
    yield 300  # Wait 5 seconds
    
    # Wave 3: 5 large fairies in fan pattern
    base_angle = 90.0  # degrees, pointing down
    angle_step = 15.0
    radius = 80.0
    for i in range(5):
        angle = base_angle + (i - 2) * angle_step  # -30, -15, 0, 15, 30 degrees offset
        rad = math.radians(angle)
        x = center_x + radius * math.cos(rad)
        y = top_y + 40 + radius * math.sin(rad)
        ctx.spawn_enemy(
            EnemyKind.FAIRY_LARGE,
            x=x,
            y=y,
            behavior=fairy_behavior_1,
        )
    
    yield 300  # Wait 5 seconds
    
    # Wave 4: 12 small fairies in spiral pattern with diagonal movement
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

    yield 120  # Wait 2 seconds
    
    # Wait for all enemies to be cleared
    while ctx.enemies_alive() > 0:
        yield 1
    
    yield 60  # Short pause before boss
    
    # Boss spawn (if boss is registered)
    try:
        boss = ctx.spawn_boss(
            "stage1_boss",
            x=center_x,
            y=top_y,
        )
        
        # Wait for boss to be defeated
        from model.components import Health
        while True:
            health = boss.get(Health)
            if health is None or health.hp <= 0:
                break
            yield 1
    except ValueError:
        # Boss not registered yet, skip boss phase
        pass
    
    # Stage complete
    ctx.state.stage.finished = True


def setup_stage1(state: "GameState") -> None:
    """
    Initialize Stage 1 using the Task-based stage system.
    
    This function creates a StageRunner and starts the stage1_script Task.
    
    Args:
        state: The GameState to initialize the stage in
    
    Requirements: 10.1
    """
    from model.stage import StageState
    from model.scripting.stage_runner import StageRunner
    
    # Create stage state
    state.stage = StageState()
    
    # Create and attach stage runner
    stage_runner = StageRunner()
    state.stage_runner = stage_runner
    
    # Start the stage script
    stage_runner.start_stage(state, stage1_script, rng_seed=0)
