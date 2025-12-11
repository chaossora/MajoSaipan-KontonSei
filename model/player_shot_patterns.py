"""
玩家射击模式系统
提供可扩展的玩家弹发射模式，使用注册表实现开闭原则。
模式参照敌人弹幕系统 (bullet_patterns.py)。

注册表函数只返回数据（偏移+速度），spawn 在 system 层统一处理。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List

from pygame.math import Vector2

from .registry import Registry


class PlayerShotPatternKind(Enum):
    """玩家射击模式类型"""
    SPREAD = auto()      # 扩散弹（角度偏移）
    STRAIGHT = auto()    # 直射弹（水平位置偏移）
    HOMING = auto()      # 追踪弹（预留）


@dataclass
class PlayerShotPatternConfig:
    """
    玩家射击模式配置
    """
    kind: PlayerShotPatternKind = PlayerShotPatternKind.SPREAD
    cooldown: float = 0.08
    bullet_speed: float = 520.0
    damage: int = 1
    
    # 扩散模式参数（SPREAD）- 角度列表
    angles_spread: List[float] = field(default_factory=lambda: [-10.0, 0.0, 10.0])
    angles_focus: List[float] = field(default_factory=lambda: [-3.0, 0.0, 3.0])
    
    # 直射模式参数（STRAIGHT）- 水平偏移列表
    offsets_spread: List[float] = field(default_factory=lambda: [-16.0, -8.0, 0.0, 8.0, 16.0])
    offsets_focus: List[float] = field(default_factory=lambda: [-8.0, 0.0, 8.0])
    
    # 增强模式参数
    enhanced_damage_multiplier: float = 1.5
    enhanced_speed_multiplier: float = 1.2
    angles_spread_enhanced: List[float] = field(default_factory=lambda: [-15.0, -7.5, 0.0, 7.5, 15.0])
    angles_focus_enhanced: List[float] = field(default_factory=lambda: [-4.0, -2.0, 0.0, 2.0, 4.0])
    offsets_spread_enhanced: List[float] = field(default_factory=lambda: [-24.0, -12.0, 0.0, 12.0, 24.0])
    offsets_focus_enhanced: List[float] = field(default_factory=lambda: [-12.0, -6.0, 0.0, 6.0, 12.0])


@dataclass
class ShotResult:
    """射击结果：单发子弹的数据"""
    x_offset: float      # 相对发射点的 X 偏移
    velocity: Vector2    # 速度向量


# 玩家射击模式注册表
# 签名: (config, is_focusing, is_enhanced) -> List[ShotResult]
player_shot_pattern_registry: Registry[PlayerShotPatternKind] = Registry("player_shot_pattern")


def execute_player_shot(
    config: PlayerShotPatternConfig,
    is_focusing: bool = False,
    is_enhanced: bool = False,
) -> List[ShotResult]:
    """
    执行玩家射击模式，返回子弹数据列表。
    spawn 由 system 层处理。
    """
    handler = player_shot_pattern_registry.get(config.kind)
    if handler:
        return handler(config, is_focusing, is_enhanced)
    return _pattern_spread(config, is_focusing, is_enhanced)


# ========== 射击模式实现 ==========

@player_shot_pattern_registry.register(PlayerShotPatternKind.SPREAD)
def _pattern_spread(
    config: PlayerShotPatternConfig,
    is_focusing: bool,
    is_enhanced: bool,
) -> List[ShotResult]:
    """扩散弹：根据角度列表生成"""
    if is_enhanced:
        angles = config.angles_focus_enhanced if is_focusing else config.angles_spread_enhanced
        speed = config.bullet_speed * config.enhanced_speed_multiplier
    else:
        angles = config.angles_focus if is_focusing else config.angles_spread
        speed = config.bullet_speed
    
    results = []
    for angle_deg in angles:
        rad = math.radians(angle_deg - 90)
        vel = Vector2(math.cos(rad) * speed, math.sin(rad) * speed)
        results.append(ShotResult(x_offset=0.0, velocity=vel))
    return results


@player_shot_pattern_registry.register(PlayerShotPatternKind.STRAIGHT)
def _pattern_straight(
    config: PlayerShotPatternConfig,
    is_focusing: bool,
    is_enhanced: bool,
) -> List[ShotResult]:
    """直射弹：根据水平偏移列表生成"""
    if is_enhanced:
        offsets = config.offsets_focus_enhanced if is_focusing else config.offsets_spread_enhanced
        speed = config.bullet_speed * config.enhanced_speed_multiplier
    else:
        offsets = config.offsets_focus if is_focusing else config.offsets_spread
        speed = config.bullet_speed
    
    vel = Vector2(0, -speed)
    return [ShotResult(x_offset=off, velocity=vel) for off in offsets]


@player_shot_pattern_registry.register(PlayerShotPatternKind.HOMING)
def _pattern_homing(
    config: PlayerShotPatternConfig,
    is_focusing: bool,
    is_enhanced: bool,
) -> List[ShotResult]:
    """追踪弹：预留（追踪逻辑需在 system 层处理）"""
    return _pattern_spread(config, is_focusing, is_enhanced)
