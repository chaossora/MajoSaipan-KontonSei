"""
擦弹能量系统：
- 监听擦弹事件，累积能量
- 能量满时自动激活增强状态
- 增强时能量持续消耗
- 非增强时能量会衰减
"""
from __future__ import annotations

from ..game_state import GameState
from ..components import (
    PlayerGraze,
    GrazeEnergy,
)
from ..game_config import GrazeEnergyConfig


def graze_energy_system(state: GameState, dt: float) -> None:
    """
    擦弹能量系统：
    - 根据擦弹计数增量累积能量
    - 能量满时自动激活增强状态
    - 增强状态时能量持续消耗（drain_rate）
    - 非增强时，停止擦弹后能量衰减（decay_rate）
    """
    player = state.get_player()
    if not player:
        return

    graze_energy = player.get(GrazeEnergy)
    p_graze = player.get(PlayerGraze)
    if not (graze_energy and p_graze):
        return

    # 获取配置
    cfg: GrazeEnergyConfig = state.get_resource(GrazeEnergyConfig)  # type: ignore
    if not cfg:
        cfg = GrazeEnergyConfig()

    # 1. 计算本帧擦弹增量
    current_count = p_graze.count
    graze_delta = current_count - graze_energy.last_graze_count
    graze_energy.last_graze_count = current_count

    # 2. 增强状态处理
    if graze_energy.is_enhanced:
        # 增强状态：能量持续消耗
        graze_energy.energy -= cfg.drain_rate * dt

        # 能量耗尽，结束增强状态
        if graze_energy.energy <= 0:
            graze_energy.energy = 0.0
            graze_energy.is_enhanced = False
    else:
        # 非增强状态

        # 3. 处理擦弹能量增加
        if graze_delta > 0:
            graze_energy.energy = min(
                graze_energy.max_energy,
                graze_energy.energy + cfg.energy_per_graze * graze_delta
            )
            # 重置衰减计时器
            graze_energy.decay_timer = cfg.decay_delay

        # 4. 检测能量满，自动激活增强状态
        if graze_energy.energy >= graze_energy.max_energy:
            graze_energy.is_enhanced = True
            # 能量从满开始消耗
            graze_energy.energy = graze_energy.max_energy

        # 5. 处理能量衰减（仅在非增强状态且无擦弹时）
        elif graze_delta == 0 and graze_energy.energy > 0:
            if graze_energy.decay_timer > 0:
                # 衰减延迟倒计时
                graze_energy.decay_timer -= dt
            else:
                # 开始衰减
                graze_energy.energy = max(
                    0.0,
                    graze_energy.energy - cfg.decay_rate * dt
                )
