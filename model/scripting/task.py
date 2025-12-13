"""
Task 和 TaskRunner 组件：协程式脚本系统。

Task 是单个协程任务，TaskRunner 是任务执行器组件。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Generator, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """
    单个协程任务。
    
    Attributes:
        generator: 脚本生成器（yield int 表示等待帧数）
        wait_frames: 剩余等待帧数
        finished: 任务是否已完成
        ctx: 执行上下文（TaskContext）
    """
    generator: Generator[int, None, None]
    wait_frames: int = 0
    finished: bool = False
    ctx: Optional[Any] = None


@dataclass
class TaskRunner:
    """
    任务执行器组件，可挂载到任意 Actor（Boss/Enemy/Stage）。
    
    Attributes:
        tasks: 活跃任务列表
    """
    tasks: List[Task] = field(default_factory=list)
    
    def start_task(
        self, 
        gen_func: Callable[..., Generator[int, None, None]], 
        ctx: Any,
        *args: Any,
        **kwargs: Any
    ) -> Task:
        """
        启动新任务。
        
        Args:
            gen_func: 生成器函数（脚本）
            ctx: 执行上下文
            *args, **kwargs: 传递给生成器函数的额外参数
        
        Returns:
            创建的 Task 对象
        """
        generator = gen_func(ctx, *args, **kwargs)
        task = Task(generator=generator, ctx=ctx)
        self.tasks.append(task)
        return task
    
    def tick(self) -> None:
        """
        推进所有任务一帧。
        
        **Requirements 13.7**: 任务按添加顺序处理（稳定遍历顺序）。
        tasks 列表是 Python list，保持插入顺序。
        """
        # 按稳定顺序遍历（list 保持插入顺序）
        for task in self.tasks:
            if task.finished:
                continue
            
            # 还在等待中？减 1 帧，跳过
            if task.wait_frames > 0:
                task.wait_frames -= 1
                continue
            
            # 推进协程一步
            try:
                wait = next(task.generator)
                task.wait_frames = wait if isinstance(wait, int) and wait > 0 else 0
            except StopIteration:
                # 协程结束
                task.finished = True
            except Exception as e:
                # 异常处理：记录错误并终止任务
                logger.error(f"Task 执行错误: {e}")
                task.finished = True
        
        # 清理已完成的任务
        self.tasks = [t for t in self.tasks if not t.finished]
    
    def terminate_all(self) -> None:
        """终止所有任务。"""
        for task in self.tasks:
            task.finished = True
        self.tasks.clear()
    
    def has_active_tasks(self) -> bool:
        """检查是否有活跃任务。"""
        return any(not t.finished for t in self.tasks)
