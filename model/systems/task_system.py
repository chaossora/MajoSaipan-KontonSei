"""
TaskSystem：每帧推进所有 TaskRunner。

这是引擎层的第一个系统，负责推进所有协程脚本。
脚本可能会发射子弹/生成敌人，所以必须在 MotionSystem 之前执行。

**Requirements: 5.2, 8.1**
"""
from __future__ import annotations

from ..game_state import GameState
from ..scripting.task import TaskRunner


def task_system(state: GameState, dt: float) -> None:
    """
    Task 系统：推进所有挂载在 Actor 上的 TaskRunner 和 StageRunner。
    
    执行流程：
    1. 先推进 StageRunner（关卡脚本）
    2. 遍历所有带 TaskRunner 的 Actor（Boss、敌人等）
    3. 调用 tick() 推进每个 TaskRunner 的所有任务
    
    此系统必须在更新顺序中第一个执行（在 MotionSystem 之前）。
    
    **Requirements 13.6, 13.7**: 遍历顺序稳定：
    - actors 列表按添加顺序遍历（list 保持插入顺序）
    - TaskRunner.tasks 按添加顺序遍历（list 保持插入顺序）
    """
    # 1. 先推进关卡脚本
    # Requirements 10.1: 关卡脚本由 StageRunner 管理
    if state.stage_runner is not None:
        state.stage_runner.tick()
    
    # 用于追踪需要检查的 Actor
    actors_to_check = []
    
    # 2. 按稳定顺序遍历所有 Actor（list 保持插入顺序）
    # Requirements 13.6: actors 列表按添加顺序遍历
    for actor in state.actors:
        runner = actor.get(TaskRunner)
        if runner is None:
            continue
        
        # 推进该 Actor 的所有任务
        runner.tick()
        actors_to_check.append((actor, runner))
    
    # 注意：Actor 销毁由其他系统处理（enemy_death 等）
    # 销毁时应调用 TaskRunner.terminate_all() 终止关联任务
