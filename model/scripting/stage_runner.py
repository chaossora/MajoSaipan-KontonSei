"""
StageRunner：管理关卡主 Task 的关卡脚本执行器。

StageRunner 负责：
- 启动和管理关卡主 Task
- 为关卡脚本提供 TaskContext
- 跟踪关卡完成状态

Requirements: 10.1
"""
from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import TYPE_CHECKING, Callable, Generator, Optional

from .task import Task, TaskRunner
from .context import TaskContext

if TYPE_CHECKING:
    from model.game_state import GameState
    from model.actor import Actor


@dataclass
class StageRunner:
    """
    管理关卡主 Task 的关卡脚本执行器。
    
    StageRunner 封装了 TaskRunner，并提供关卡特定的功能，
    如跟踪完成状态和提供关卡上下文。
    
    Attributes:
        task_runner: 用于执行 Task 的底层 TaskRunner
        stage_task: 关卡主 Task（如果已启动）
        ctx: 关卡脚本的 TaskContext
        finished: 关卡脚本是否已完成
        rng_seed: 用于确定性回放的 RNG 种子
    
    Requirements: 10.1
    """
    task_runner: TaskRunner = field(default_factory=TaskRunner)
    stage_task: Optional[Task] = None
    ctx: Optional[TaskContext] = None
    finished: bool = False
    rng_seed: int = 0
    
    def start_stage(
        self,
        state: "GameState",
        stage_script: Callable[[TaskContext], Generator[int, None, None]],
        rng_seed: int = 0,
    ) -> Task:
        """
        启动关卡主 Task。
        
        Args:
            state: GameState 引用
            stage_script: 定义关卡时间线的生成器函数
            rng_seed: 确定性 RNG 的种子（默认 0）
        
        Returns:
            创建的关卡 Task
        
        Requirements: 10.1
        """
        self.rng_seed = rng_seed
        
        # 为关卡创建确定性 RNG
        rng = Random(rng_seed)
        
        # 创建关卡上下文（关卡级脚本的 owner 为 None）
        self.ctx = TaskContext(
            state=state,
            owner=None,
            rng=rng,
        )
        
        # 启动关卡 Task
        self.stage_task = self.task_runner.start_task(stage_script, self.ctx)
        self.finished = False
        
        return self.stage_task
    
    def tick(self) -> None:
        """
        推进关卡 Task 一帧。
        
        当关卡 Task 完成时更新 finished 标志。
        
        Requirements: 10.1, 10.5
        """
        self.task_runner.tick()
        
        # 检查关卡主 Task 是否已完成
        if self.stage_task is not None and self.stage_task.finished:
            self.finished = True
    
    def is_running(self) -> bool:
        """
        检查关卡是否正在运行。
        
        Returns:
            如果关卡 Task 处于活跃状态且未完成则返回 True
        """
        return self.stage_task is not None and not self.finished
    
    def terminate(self) -> None:
        """
        终止关卡 Task 及所有子任务。
        """
        self.task_runner.terminate_all()
        self.finished = True
