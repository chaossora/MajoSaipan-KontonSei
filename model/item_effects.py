"""
物品效果系统
提供可扩展的物品拾取效果处理，使用注册表实现开闭原则。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import Registry
from .components import ItemType

if TYPE_CHECKING:
    from .game_state import GameState
    from .actor import Actor
    from .components import PlayerPower, PlayerScore


# 物品效果注册表
# 处理函数签名：(state, player, item_actor, item_value) -> None
item_effect_registry: Registry[ItemType] = Registry("item_effect")


def apply_item_effect(
    state: "GameState",
    player: "Actor",
    item_actor: "Actor",
    item_type: ItemType,
    item_value: int,
) -> None:
    """
    应用物品效果。

    Args:
        state: 游戏状态
        player: 玩家 Actor
        item_actor: 物品 Actor
        item_type: 物品类型
        item_value: 物品数值
    """
    handler = item_effect_registry.get(item_type)
    if handler:
        handler(state, player, item_actor, item_value)


# ========== 物品效果实现 ==========

@item_effect_registry.register(ItemType.POWER)
def _effect_power(
    state: "GameState",
    player: "Actor",
    item_actor: "Actor",
    item_value: int,
) -> None:
    """
    Power 道具效果：
    - 增加火力值
    - 额外加一点基础分
    """
    from .components import PlayerPower, PlayerScore

    p_power = player.get(PlayerPower)
    p_score = player.get(PlayerScore)
    from .game_config import CollectConfig
    cfg = state.get_resource(CollectConfig)  # type: ignore
    if cfg is None:
        return

    if p_power:
        p_power.power = min(
            p_power.max_power,
            p_power.power + item_value * cfg.power_step,
        )

    if p_score:
        p_score.score += cfg.power_score * item_value


@item_effect_registry.register(ItemType.POINT)
def _effect_point(
    state: "GameState",
    player: "Actor",
    item_actor: "Actor",
    item_value: int,
) -> None:
    """
    Point 道具效果：
    - 按高度计算分数（越高分越多）
    - auto_collect 状态直接满分
    """
    from .components import PlayerScore, Position, Item

    p_score = player.get(PlayerScore)
    if not p_score:
        return

    from .game_config import CollectConfig
    cfg = state.get_resource(CollectConfig)  # type: ignore
    if cfg is None:
        return
    score_value = _calc_point_item_score(state, item_actor, cfg)
    p_score.score += score_value * item_value


@item_effect_registry.register(ItemType.BOMB)
def _effect_bomb(
    state: "GameState",
    player: "Actor",
    item_actor: "Actor",
    item_value: int,
) -> None:
    """
    Bomb 道具效果：
    - 增加炸弹数量
    """
    from .components import PlayerBomb

    p_bomb = player.get(PlayerBomb)
    if p_bomb:
        p_bomb.bombs = min(
            p_bomb.max_bombs,
            p_bomb.bombs + item_value,
        )


@item_effect_registry.register(ItemType.LIFE)
def _effect_life(
    state: "GameState",
    player: "Actor",
    item_actor: "Actor",
    item_value: int,
) -> None:
    """
    Life 道具效果：
    - 增加残机数量
    """
    from .components import PlayerLife

    p_life = player.get(PlayerLife)
    if p_life:
        p_life.lives = min(
            p_life.max_lives,
            p_life.lives + item_value,
        )


# ========== 辅助函数 ==========

def _calc_point_item_score(state: "GameState", item_actor: "Actor", cfg) -> int:
    """
    计算 Point 道具分数：
    - POC_COLLECT 状态 -> 满分 (point_score_max)
    - MAGNET_ATTRACT 状态 -> 按高度计分
    - NONE 状态 -> 按高度计分
    """
    from .components import Position, Item, ItemCollectState

    pos = item_actor.get(Position)
    item = item_actor.get(Item)
    if not (pos and item):
        return cfg.point_score_min

    # 只有 PoC 吸附才满分
    if item.collect_state == ItemCollectState.POC_COLLECT:
        return cfg.point_score_max

    # 范围吸附或普通拾取 -> 按高度计分
    h = max(1.0, float(state.height))
    y = pos.y

    poc_y = h * cfg.poc_line_ratio

    if y <= poc_y:
        t = 1.0
    else:
        denom = h - poc_y
        if denom <= 0.0:
            t = 0.0
        else:
            t = (h - y) / denom
            t = max(0.0, min(1.0, t))

    base_min = cfg.point_score_min
    base_max = cfg.point_score_max
    score_value = int(base_min + (base_max - base_min) * t)
    return score_value
