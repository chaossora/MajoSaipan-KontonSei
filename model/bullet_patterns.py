"""
弹幕模式系统
提供可扩展的敌弹发射模式，使用注册表实现开闭原则。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Callable

from pygame.math import Vector2

from .registry import Registry


# ========== 通用射击数据结构 ==========
# 三个射击系统（敌人弹幕、玩家主机、子机）统一使用

@dataclass
class ShotData:
    """
    射击数据：描述单发子弹的物理属性。
    
    Attributes:
        velocity: 速度向量
        offset: 相对发射点的位置偏移，默认 (0, 0)
        delay: 延迟发射秒数，默认 0（立即发射）
        motion_phases: 运动阶段序列（可选），用于子弹运动状态机
    """
    velocity: Vector2
    offset: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    delay: float = 0.0
    motion_phases: List[object] | None = None  # List[LinearPhase | WaypointPhase | HoverPhase]

if TYPE_CHECKING:
    from .game_state import GameState
    from .components import Position


class BulletPatternKind(Enum):
    """弹幕模式类型"""
    AIM_PLAYER = auto()      # 自机狙
    STRAIGHT_DOWN = auto()   # 直下
    N_WAY = auto()           # N-Way 扇形弹
    RING = auto()            # 全方位环形弹
    SPIRAL = auto()          # 螺旋弹


@dataclass
class BulletPatternConfig:
    """
    弹幕模式配置

    Attributes:
        kind: 弹幕类型
        bullet_speed: 子弹速度
        damage: 伤害值
        count: 子弹数量（用于 N_WAY, RING 等）
        spread_deg: 扇形展开角度（用于 N_WAY）
        start_angle_deg: 起始角度（用于 RING, SPIRAL）
        spin_speed_deg: 每秒旋转角度（用于 SPIRAL）
    """
    kind: BulletPatternKind = BulletPatternKind.AIM_PLAYER
    bullet_speed: float = 260.0
    damage: int = 1
    count: int = 1
    spread_deg: float = 30.0
    start_angle_deg: float = 0.0
    spin_speed_deg: float = 60.0


@dataclass
class PatternState:
    """
    弹幕模式运行时状态（挂在敌人身上）
    """
    current_angle: float = 0.0  # 当前旋转角度（用于 SPIRAL）


# 弹幕模式注册表
# 返回值类型：List[ShotData] 统一的射击数据
bullet_pattern_registry: Registry[BulletPatternKind] = Registry("bullet_pattern")


def execute_pattern(
    state: "GameState",
    shooter_pos: "Position",
    config: BulletPatternConfig,
    pattern_state: PatternState | None = None,
) -> List[ShotData]:
    """
    执行弹幕模式，返回射击数据列表。

    Args:
        state: 游戏状态
        shooter_pos: 发射者位置
        config: 弹幕配置
        pattern_state: 可选的运行时状态

    Returns:
        ShotData 列表（velocity + offset + delay）
    """
    handler = bullet_pattern_registry.get(config.kind)
    if not handler:
        # 默认向下
        return [ShotData(velocity=Vector2(0, config.bullet_speed))]

    return handler(state, shooter_pos, config, pattern_state)


# ========== 弹幕模式实现 ==========

@bullet_pattern_registry.register(BulletPatternKind.AIM_PLAYER)
def _pattern_aim_player(
    state: "GameState",
    shooter_pos: "Position",
    config: BulletPatternConfig,
    pattern_state: PatternState | None,
) -> List[ShotData]:
    """自机狙：朝向玩家发射"""
    from .components import Position as Pos

    if not state.player:
        return [ShotData(velocity=Vector2(0, config.bullet_speed))]

    player_pos = state.player.get(Pos)
    if not player_pos:
        return [ShotData(velocity=Vector2(0, config.bullet_speed))]

    dir_vec = Vector2(player_pos.x - shooter_pos.x, player_pos.y - shooter_pos.y)
    if dir_vec.length_squared() < 1e-9:
        return [ShotData(velocity=Vector2(0, config.bullet_speed))]

    dir_vec = dir_vec.normalize() * config.bullet_speed
    return [ShotData(velocity=dir_vec)]


@bullet_pattern_registry.register(BulletPatternKind.STRAIGHT_DOWN)
def _pattern_straight_down(
    state: "GameState",
    shooter_pos: "Position",
    config: BulletPatternConfig,
    pattern_state: PatternState | None,
) -> List[ShotData]:
    """直下：向下发射"""
    return [ShotData(velocity=Vector2(0, config.bullet_speed))]


@bullet_pattern_registry.register(BulletPatternKind.N_WAY)
def _pattern_n_way(
    state: "GameState",
    shooter_pos: "Position",
    config: BulletPatternConfig,
    pattern_state: PatternState | None,
) -> List[ShotData]:
    """
    N-Way 扇形弹：
    - 以自机狙方向为中心
    - 展开 spread_deg 角度
    - 发射 count 颗子弹
    """
    from .components import Position as Pos

    # 计算基准方向（朝向玩家或向下）
    base_dir = Vector2(0, 1)  # 默认向下
    if state.player:
        player_pos = state.player.get(Pos)
        if player_pos:
            to_player = Vector2(player_pos.x - shooter_pos.x, player_pos.y - shooter_pos.y)
            if to_player.length_squared() > 1e-9:
                base_dir = to_player.normalize()

    results: List[ShotData] = []
    count = max(1, config.count)

    if count == 1:
        results.append(ShotData(velocity=base_dir * config.bullet_speed))
    else:
        half_spread = config.spread_deg / 2.0
        for i in range(count):
            t = i / (count - 1)  # 0.0 ~ 1.0
            angle_offset = -half_spread + config.spread_deg * t
            vel = base_dir.rotate(angle_offset) * config.bullet_speed
            results.append(ShotData(velocity=vel))

    return results


@bullet_pattern_registry.register(BulletPatternKind.RING)
def _pattern_ring(
    state: "GameState",
    shooter_pos: "Position",
    config: BulletPatternConfig,
    pattern_state: PatternState | None,
) -> List[ShotData]:
    """
    环形弹：
    - 从 start_angle_deg 开始
    - 均匀分布 count 颗子弹（360度）
    """
    results: List[ShotData] = []
    count = max(1, config.count)
    angle_step = 360.0 / count

    # 基准向量（向右），旋转后发射
    base = Vector2(config.bullet_speed, 0)
    for i in range(count):
        angle = config.start_angle_deg + angle_step * i
        results.append(ShotData(velocity=base.rotate(angle)))

    return results


@bullet_pattern_registry.register(BulletPatternKind.SPIRAL)
def _pattern_spiral(
    state: "GameState",
    shooter_pos: "Position",
    config: BulletPatternConfig,
    pattern_state: PatternState | None,
) -> List[ShotData]:
    """
    螺旋弹：
    - 每次发射 count 颗环形弹
    - 每次发射后角度递增 spin_speed_deg（需要 PatternState）
    """
    results: List[ShotData] = []
    count = max(1, config.count)
    angle_step = 360.0 / count

    # 获取当前累积旋转角度
    current = config.start_angle_deg
    if pattern_state:
        current = pattern_state.current_angle

    base = Vector2(config.bullet_speed, 0)
    for i in range(count):
        angle = current + angle_step * i
        results.append(ShotData(velocity=base.rotate(angle)))

    # 更新旋转状态（如果有）
    if pattern_state:
        pattern_state.current_angle += config.spin_speed_deg

    return results
