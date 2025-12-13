# model/stage.py
"""
Stage state management.

This module contains the StageState dataclass for tracking stage progress.
The old StageEvent/WavePattern system has been replaced by the Task-based
stage scripting system in model/scripting/stage_runner.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class StageState:
    """
    当前关卡的状态：
    - time: 当前关卡运行时间（秒）
    - finished: 是否已经完成
    
    Note: The old events/cursor fields have been removed.
    Stage scripting is now handled by StageRunner using Tasks.
    """
    time: float = 0.0
    finished: bool = False
