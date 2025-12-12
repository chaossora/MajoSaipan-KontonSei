# model/systems/movement.py
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pygame.math import Vector2

from ..game_state import GameState
from ..components import Position, Velocity, PathFollower
from ..movement_path import PathConfig, PathKind
from ..registry import Registry

if TYPE_CHECKING:
    pass

# 路径处理器注册表
# 处理函数签名：(cfg, pf, pos, vel) -> None
path_handler_registry: Registry[PathKind] = Registry("path_handler")


def movement_system(state: GameState, dt: float) -> None:
    """
    通用移动系统：所有有 Position + Velocity 的实体按速度移动。
    如果实体有 PathFollower，先根据路径配置更新速度。

    职责：只负责路径跟随 + 位置更新。
    边界限制和出界清理由 boundary_system 处理。
    """
    path_lib = state.path_library

    for actor in state.actors:
        pos = actor.get(Position)
        vel = actor.get(Velocity)
        if not (pos and vel):
            continue

        path_follower = actor.get(PathFollower)

        if path_follower:
            _update_velocity_by_path(path_follower, pos, vel, path_lib, dt)

        # 按速度更新位置
        pos.x += vel.vec.x * dt
        pos.y += vel.vec.y * dt


def _update_velocity_by_path(
    pf: PathFollower,
    pos: Position,
    vel: Velocity,
    path_lib,
    dt: float,
) -> None:
    """根据路径配置更新速度。"""
    cfg: PathConfig | None = path_lib.configs.get(pf.path_name)
    if not cfg:
        return

    # 首次初始化原点（记录出生位置）
    if not pf.initialized:
        pf.origin_x = pos.x
        pf.origin_y = pos.y
        pf.initialized = True

    pf.t += dt

    # 从注册表获取路径处理函数
    handler = path_handler_registry.get(cfg.kind)
    if handler:
        handler(cfg, pf, pos, vel)


@path_handler_registry.register(PathKind.STRAIGHT)
def _path_straight(cfg: PathConfig, pf: PathFollower, pos: Position, vel: Velocity) -> None:
    """
    直线路径：把 dir_x, dir_y 归一化再乘 speed
    """
    dir_vec = Vector2(cfg.dir_x, cfg.dir_y)
    if dir_vec.length_squared() < 1e-9:
        vel.vec.update(0, 0)
        return
    dir_vec = dir_vec.normalize()
    vel.vec = dir_vec * cfg.speed


@path_handler_registry.register(PathKind.SINE_H)
def _path_sine_h(cfg: PathConfig, pf: PathFollower, pos: Position, vel: Velocity) -> None:
    """
    左右 SINE 摇摆 + 向下：
    - Y 方向匀速向下
    - X = origin_x + amplitude * sin(2π f t)
    """
    # 下落速度（只影响 Y 分量）
    vel.vec.y = cfg.speed

    # 计算目标 X 位置（不修改原点）
    offset_x = cfg.amplitude * math.sin(2.0 * math.pi * cfg.frequency * pf.t)
    target_x = pf.origin_x + offset_x

    # 直接将 X 位置设为目标值（不通过速度）
    pos.x = target_x

    # X 方向速度设为 0，因为 X 位置已被直接覆盖
    vel.vec.x = 0.0
