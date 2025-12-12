from __future__ import annotations

from ..game_state import GameState, spawn_bomb_field
from ..components import (
    PlayerBomb,
    PlayerDamageState,
    Position,
    Item,
    ItemTag,
    BombConfigData,
    InputState,
    ItemCollectState,
)
from ..bomb_handlers import dispatch_bomb, BombType


def _bomb_autocollect_items(state: GameState) -> None:
    """
    将所有道具标记为 PoC 吸附，让 item_autocollect_system 拉取它们。
    炸弹收集道具应获得满分。
    """
    for actor in state.actors:
        if not actor.get(ItemTag):
            continue
        item = actor.get(Item)
        if item:
            item.collect_state = ItemCollectState.POC_COLLECT


def bomb_system(
    state: GameState,
    dt: float,
) -> None:
    """
    炸弹系统：基于组件驱动，不直接依赖 state.player。
    """
    player = state.get_player()
    if not player:
        return

    inp = player.get(InputState)
    if not (inp and inp.bomb_pressed):
        return

    bomb = player.get(PlayerBomb)
    dmg = player.get(PlayerDamageState)
    pos = player.get(Position)
    bomb_cfg = player.get(BombConfigData)

    if not (bomb and dmg and pos):
        return

    if bomb.bombs <= 0:
        return

    # 组件缺失时回退到全局配置
    if bomb_cfg is None:
        from ..game_config import BombConfig
        bomb_defaults: BombConfig = state.get_resource(BombConfig) or BombConfig()  # type: ignore
        bomb_cfg = BombConfigData(
            bomb_type=BombType.CIRCLE,
            duration=bomb_defaults.duration,
            invincible_time=bomb_defaults.invincible_time,
            radius=bomb_defaults.radius,
            effect_sprite="bomb_field",
        )

    # 消耗一个炸弹
    bomb.bombs -= 1

    # 应用无敌时间
    dmg.invincible_timer = max(dmg.invincible_timer, bomb_cfg.invincible_time)

    # 分发炸弹行为
    dispatch_bomb(state, pos, bomb_cfg)

    # 触发自动吸取
    _bomb_autocollect_items(state)
