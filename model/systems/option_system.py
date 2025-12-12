# model/systems/option_system.py
"""
子机系统 - 东方风格子机管理。

根据火力等级更新子机数量，使用动态对称分布平滑插值子机位置。

火力到子机数量映射：
- 火力 0-1: 0 个子机
- 火力 1-2: 1 个子机
- 火力 2-3: 2 个子机
- 火力 3-4: 3 个子机
- 火力 4 (满): 4 个子机

动态对称位置分布：
- 1 个子机: 中央
- 2 个子机: 左、右
- 3 个子机: 中央、左、右
- 4 个子机: 内层对、外层对
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

from ..components import (
    Position, PlayerTag, PlayerPower, FocusState,
    OptionConfig, OptionState,
)

if TYPE_CHECKING:
    from ..game_state import GameState


def option_system(state: GameState, dt: float) -> None:
    """
    更新玩家子机数量和位置。

    此系统应在 player_move_system（更新 FocusState）之后、
    player_shoot_system 之前运行。
    """
    player = state.get_player()
    if not player:
        return

    pos = player.get(Position)
    power = player.get(PlayerPower)
    focus = player.get(FocusState)
    option_cfg = player.get(OptionConfig)
    option_state = player.get(OptionState)

    if not (pos and power and focus and option_cfg and option_state):
        return

    # 根据火力等级计算激活的子机数量
    # 火力 0-1: 0, 火力 1-2: 1, 火力 2-3: 2, 火力 3-4: 3, 火力 4: 4
    new_count = min(option_cfg.max_options, max(0, int(power.power)))
    old_count = option_state.active_count

    # 处理子机数量变化
    if new_count != old_count:
        _handle_option_count_change(option_state, option_cfg, pos, new_count, focus.is_focusing)

    # 使用平滑插值更新子机位置
    _update_option_positions(
        player_pos=pos,
        option_cfg=option_cfg,
        option_state=option_state,
        is_focusing=focus.is_focusing,
        dt=dt,
    )


def calculate_symmetric_positions(
    count: int,
    spread_x: float,
    offset_y: float,
    outer_y: float,
) -> List[Tuple[float, float]]:
    """
    根据子机数量计算对称位置偏移。

    Args:
        count: 子机数量 (0-4)
        spread_x: X 方向扩散距离
        offset_y: 主要 Y 偏移
        outer_y: 外层子机 Y 偏移（4个时）

    Returns:
        位置偏移列表 [(offset_x, offset_y), ...]
    """
    if count == 0:
        return []

    if count == 1:
        # 1个子机：中央
        return [(0.0, offset_y)]

    if count == 2:
        # 2个子机：左右对称
        return [
            (-spread_x, offset_y),
            (spread_x, offset_y),
        ]

    if count == 3:
        # 3个子机：中央 + 左右
        return [
            (0.0, offset_y),           # 中央
            (-spread_x, offset_y),     # 左
            (spread_x, offset_y),      # 右
        ]

    if count == 4:
        # 4个子机：内层对 + 外层对
        inner_spread = spread_x * 0.6
        return [
            (-inner_spread, offset_y),   # 内左
            (inner_spread, offset_y),    # 内右
            (-spread_x, outer_y),        # 外左
            (spread_x, outer_y),         # 外右
        ]

    # 5个及以上：均匀分布（扩展支持）
    positions = []
    if count % 2 == 1:
        # 奇数：中央 + 两侧对称
        positions.append((0.0, offset_y))
        pairs = count // 2
        for i in range(pairs):
            x = spread_x * (i + 1) / pairs
            positions.append((-x, offset_y))
            positions.append((x, offset_y))
    else:
        # 偶数：两侧对称
        pairs = count // 2
        for i in range(pairs):
            x = spread_x * (i + 0.5) / pairs
            positions.append((-x, offset_y))
            positions.append((x, offset_y))

    return positions


def _handle_option_count_change(
    option_state: OptionState,
    option_cfg: OptionConfig,
    player_pos: Position,
    new_count: int,
    is_focusing: bool,
) -> None:
    """
    处理子机数量变化。
    当数量变化时，重新初始化位置列表。
    """
    option_state.active_count = new_count

    # 选择扩散参数
    spread_x = option_cfg.focus_spread_x if is_focusing else option_cfg.base_spread_x
    offset_y = option_cfg.focus_offset_y if is_focusing else option_cfg.base_offset_y
    outer_y = option_cfg.outer_offset_y

    # 计算新的目标位置偏移
    target_offsets = calculate_symmetric_positions(new_count, spread_x, offset_y, outer_y)

    # 确保位置列表长度正确
    while len(option_state.current_positions) < new_count:
        # 新增子机初始化在玩家位置
        option_state.current_positions.append([player_pos.x, player_pos.y])

    # 截断多余的位置
    if len(option_state.current_positions) > new_count:
        option_state.current_positions = option_state.current_positions[:new_count]


def _update_option_positions(
    player_pos: Position,
    option_cfg: OptionConfig,
    option_state: OptionState,
    is_focusing: bool,
    dt: float,
) -> None:
    """
    使用动态对称分布计算子机位置，并应用平滑插值动画。
    """
    if option_state.active_count == 0:
        return

    # 选择扩散参数
    spread_x = option_cfg.focus_spread_x if is_focusing else option_cfg.base_spread_x
    offset_y = option_cfg.focus_offset_y if is_focusing else option_cfg.base_offset_y
    outer_y = option_cfg.outer_offset_y

    # 计算当前数量的对称位置偏移
    target_offsets = calculate_symmetric_positions(
        option_state.active_count,
        spread_x,
        offset_y,
        outer_y,
    )

    # 对每个子机应用插值
    for i in range(option_state.active_count):
        if i >= len(option_state.current_positions) or i >= len(target_offsets):
            continue

        # 目标位置 = 玩家位置 + 偏移
        target_x = player_pos.x + target_offsets[i][0]
        target_y = player_pos.y + target_offsets[i][1]

        # 当前位置
        curr = option_state.current_positions[i]

        # 平滑插值 (lerp)
        t = min(1.0, option_cfg.transition_speed * dt)
        new_x = curr[0] + (target_x - curr[0]) * t
        new_y = curr[1] + (target_y - curr[1]) * t

        option_state.current_positions[i] = [new_x, new_y]
