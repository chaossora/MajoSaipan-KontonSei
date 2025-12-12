# model/systems/stage_system.py
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from pygame.math import Vector2

from ..game_state import GameState
from ..stage import StageState, StageEvent, StageEventType, WavePattern
from ..components import EnemyKind, PathFollower
from ..enemies import enemy_registry
from ..registry import Registry

if TYPE_CHECKING:
    from ..actor import Actor

# 波次模式注册表
# 处理函数签名：(state, ev, spawner) -> None
wave_pattern_registry: Registry[WavePattern] = Registry("wave_pattern")

# Boss 工厂注册表
# 处理函数签名：(state, x, y) -> Actor
boss_registry: Registry[str] = Registry("boss")


def stage_system(state: GameState, dt: float) -> None:
    """
    关卡系统：处理关卡时间线和事件触发。
    """
    stage = state.stage
    if not stage or stage.finished:
        return

    stage.time += dt

    events = stage.events
    cursor = stage.cursor
    n = len(events)

    while cursor < n and stage.time >= events[cursor].time:
        ev = events[cursor]
        _execute_stage_event(state, ev)
        cursor += 1

    stage.cursor = cursor
    if cursor >= n:
        stage.finished = True


def _execute_stage_event(state: GameState, ev: StageEvent) -> None:
    """执行关卡事件。"""
    if ev.type == StageEventType.SPAWN_WAVE:
        _spawn_wave(state, ev)
    elif ev.type == StageEventType.SPAWN_BOSS:
        _spawn_boss(state, ev)


def _spawn_wave(state: GameState, ev: StageEvent) -> None:
    """生成一波敌人。"""
    # 安全检查：SPAWN_WAVE 事件必须有 enemy_kind 和 pattern
    if ev.enemy_kind is None or ev.pattern is None:
        return

    spawner = enemy_registry.get(ev.enemy_kind)
    if not spawner:
        return

    # 从注册表获取波次模式处理函数
    handler = wave_pattern_registry.get(ev.pattern)
    if handler:
        handler(state, ev, spawner)


def _spawn_boss(state: GameState, ev: StageEvent) -> None:
    """
    生成 Boss。
    使用 boss_registry 查找对应的 Boss 工厂函数。
    """
    spawner = boss_registry.get(ev.boss_id)
    if not spawner:
        return

    # 在指定位置生成 Boss
    spawner(state, ev.start_x, ev.start_y)


@wave_pattern_registry.register(WavePattern.LINE)
def _spawn_line_wave(state: GameState, ev: StageEvent, spawner) -> None:
    """
    横向一排：
    第一只在 (start_x, start_y)，后面每只 +spacing_x。
    """
    for i in range(ev.count):
        x = ev.start_x + ev.spacing_x * i
        y = ev.start_y
        enemy = spawner(state, x, y)
        _attach_path_if_needed(enemy, ev)


@wave_pattern_registry.register(WavePattern.COLUMN)
def _spawn_column_wave(state: GameState, ev: StageEvent, spawner) -> None:
    """
    纵向一列：
    第一只在 (start_x, start_y)，后面每只 +spacing_y。
    """
    for i in range(ev.count):
        x = ev.start_x
        y = ev.start_y + ev.spacing_y * i
        enemy = spawner(state, x, y)
        _attach_path_if_needed(enemy, ev)


@wave_pattern_registry.register(WavePattern.FAN)
def _spawn_fan_wave(state: GameState, ev: StageEvent, spawner) -> None:
    """
    扇形分布：
    - 以 (start_x, start_y) 为圆心
    - 所有敌人的半径相同 = ev.radius
    - 从 angle_deg 开始，依次每只 +angle_step_deg
    """
    cx = ev.start_x
    cy = ev.start_y

    # 让扇形中心对准 angle_deg，左右对称更美观：
    # 例如 count=5, angle_step=15，则相对偏移为 [-30,-15,0,15,30]
    half = (ev.count - 1) * 0.5

    # 基准向量：从圆心向右，长度等于半径
    base = Vector2(ev.radius, 0)
    for i in range(ev.count):
        angle = ev.angle_deg + (i - half) * ev.angle_step_deg
        offset = base.rotate(angle)
        x = cx + offset.x
        y = cy + offset.y
        enemy = spawner(state, x, y)
        _attach_path_if_needed(enemy, ev)


@wave_pattern_registry.register(WavePattern.SPIRAL)
def _spawn_spiral_wave(state: GameState, ev: StageEvent, spawner) -> None:
    """
    螺旋分布：
    - 以 (start_x, start_y) 为圆心
    - 第 i 只的半径 = radius + radius_step * i
    - 第 i 只的角度 = angle_deg + angle_step_deg * i
    这样越后面的敌人越远、角度也不断旋转，就像一条螺旋线上的点。
    """
    cx = ev.start_x
    cy = ev.start_y

    for i in range(ev.count):
        radius = ev.radius + ev.radius_step * i
        angle = ev.angle_deg + ev.angle_step_deg * i
        offset = Vector2(radius, 0).rotate(angle)
        x = cx + offset.x
        y = cy + offset.y
        enemy = spawner(state, x, y)
        _attach_path_if_needed(enemy, ev)


def _attach_path_if_needed(enemy, ev: StageEvent) -> None:
    """
    如果 StageEvent 指定了 path_name，给敌人挂 PathFollower 组件。
    """
    if ev.path_name:
        enemy.add(PathFollower(path_name=ev.path_name))
