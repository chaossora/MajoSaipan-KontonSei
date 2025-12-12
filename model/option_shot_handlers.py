"""
子机射击处理器注册表。
定义不同的子机射击行为，支持 Focus 状态依赖。
统一使用 ShotData（来自 bullet_patterns）作为返回类型。

注册表函数只返回 ShotData 列表，spawn 在 system 层统一处理。
"""
from __future__ import annotations

from enum import Enum, auto
from typing import List, Optional

from pygame.math import Vector2

from .registry import Registry
from .bullet_patterns import ShotData


class OptionShotKind(Enum):
    """子机射击类型枚举"""
    REIMU_STYLE = auto()   # 平时直射，Focus追踪
    MARISA_STYLE = auto()  # 平时扩散，Focus直射
    STRAIGHT = auto()      # 始终直射
    HOMING = auto()        # 始终追踪
    SPREAD = auto()        # 始终扩散


# 子机射击模式注册表
# 签名：(speed, is_focusing, target_angle) -> List[ShotData]
# target_angle：追踪目标角度（由系统层计算）
option_shot_registry: Registry[OptionShotKind] = Registry("option_shot")


def execute_option_shot(
    kind: OptionShotKind,
    speed: float,
    is_focusing: bool,
    target_angle: Optional[float] = None,
) -> List[ShotData]:
    """
    执行子机射击模式，返回 ShotData 列表。
    spawn 由 system 层处理。

    Args:
        kind: 射击类型
        speed: 子弹速度
        is_focusing: 是否聚焦状态
        target_angle: 追踪目标角度（度），None 则直射
    """
    handler = option_shot_registry.get(kind)
    if handler:
        return handler(speed, is_focusing, target_angle)
    return _shot_straight(speed, is_focusing, target_angle)


# ========== 基础射击类型 ==========

@option_shot_registry.register(OptionShotKind.STRAIGHT)
def _shot_straight(
    speed: float,
    is_focusing: bool,
    target_angle: Optional[float],
) -> List[ShotData]:
    """直射：始终向上"""
    return [ShotData(velocity=Vector2(0, -speed))]


@option_shot_registry.register(OptionShotKind.HOMING)
def _shot_homing(
    speed: float,
    is_focusing: bool,
    target_angle: Optional[float],
) -> List[ShotData]:
    """追踪：朝目标角度发射（稍慢）"""
    angle = target_angle if target_angle is not None else 0.0
    homing_speed = speed * 0.9
    # 基准向量向上，旋转到目标角度
    vel = Vector2(0, -homing_speed).rotate(angle)
    return [ShotData(velocity=vel)]


@option_shot_registry.register(OptionShotKind.SPREAD)
def _shot_spread(
    speed: float,
    is_focusing: bool,
    target_angle: Optional[float],
) -> List[ShotData]:
    """扩散：扇形发射"""
    angles = [-15.0, 0.0, 15.0]
    base = Vector2(0, -speed)
    return [ShotData(velocity=base.rotate(a)) for a in angles]


# ========== 角色专属射击类型 ==========

@option_shot_registry.register(OptionShotKind.REIMU_STYLE)
def _shot_reimu_style(
    speed: float,
    is_focusing: bool,
    target_angle: Optional[float],
) -> List[ShotData]:
    """灵梦风格：平时直射，Focus 追踪"""
    if is_focusing:
        return _shot_homing(speed, is_focusing, target_angle)
    return _shot_straight(speed, is_focusing, target_angle)


@option_shot_registry.register(OptionShotKind.MARISA_STYLE)
def _shot_marisa_style(
    speed: float,
    is_focusing: bool,
    target_angle: Optional[float],
) -> List[ShotData]:
    """魔理沙风格：平时扩散，Focus 直射"""
    if is_focusing:
        return _shot_straight(speed, is_focusing, target_angle)
    return _shot_spread(speed, is_focusing, target_angle)


__all__ = [
    "OptionShotKind",
    "option_shot_registry",
    "execute_option_shot",
]
