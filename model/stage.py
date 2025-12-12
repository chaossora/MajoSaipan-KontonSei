# model/stage.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

from .components import EnemyKind


class StageEventType(Enum):
    """
    关卡事件大类：
    - SPAWN_WAVE: 生成敌人波次
    - SPAWN_BOSS: 生成 Boss
    """
    SPAWN_WAVE = auto()
    SPAWN_BOSS = auto()


class WavePattern(Enum):
    """
    敌人波次的几何分布模式：
    - LINE: 横向一排
    - COLUMN: 纵向一列
    - FAN: 以一个中心点为圆心，扇形展开
    - SPIRAL: 以中心点为圆心，螺旋分布
    以后可以继续加 CIRCLE、GRID、CUSTOM_PATH 等。
    """
    LINE = auto()
    COLUMN = auto()
    FAN = auto()
    SPIRAL = auto()


@dataclass
class StageEvent:
    """
    纯数据的关卡事件：
    目前只描述"刷一组敌人波次"的参数。

    time: 触发时间（秒）
    type: 事件类别（现在只能是 SPAWN_WAVE）
    enemy_kind: 敌人类型
    pattern: 波次几何模式

    下列参数由 pattern 决定如何解释：

    LINE:
        - count: 敌人数
        - start_x, start_y: 第一只的位置
        - spacing_x: 相邻两只的水平间距

    COLUMN:
        - count
        - start_x, start_y
        - spacing_y: 相邻两只的竖直间距

    FAN:
        - count
        - center_x, center_y: 用 start_x, start_y 作为中心
        - radius: 敌人到中心的距离
        - angle_deg: 中心角（度）
        - angle_step_deg: 每只之间的角度间隔（度）

    SPIRAL:
        - count
        - center_x, center_y: 用 start_x, start_y 作为中心
        - radius: 起始半径
        - radius_step: 每只半径增量
        - angle_deg: 起始角度
        - angle_step_deg: 每只之间的角度增量
    """
    time: float
    type: StageEventType

    # SPAWN_WAVE 事件专用字段（SPAWN_BOSS 可选）
    enemy_kind: Optional[EnemyKind] = None
    pattern: Optional[WavePattern] = None
    count: int = 0

    start_x: float = 0.0
    start_y: float = 0.0

    spacing_x: float = 0.0
    spacing_y: float = 0.0

    radius: float = 0.0
    radius_step: float = 0.0

    angle_deg: float = 0.0
    angle_step_deg: float = 0.0

    path_name: str = ""   # 这波敌人使用哪条移动路径（可选）

    # SPAWN_BOSS 事件专用字段
    boss_id: str = ""     # Boss 工厂函数名（用于 boss_registry 查找）

    description: str = ""


@dataclass
class StageState:
    """
    当前关卡的时间线：
    - time: 当前关卡运行时间（秒）
    - events: 所有关卡事件，按 time 升序排
    - cursor: 下一个待执行事件索引
    - finished: 是否已经没有事件可以执行
    """
    time: float = 0.0
    events: List[StageEvent] = field(default_factory=list)
    cursor: int = 0
    finished: bool = False
