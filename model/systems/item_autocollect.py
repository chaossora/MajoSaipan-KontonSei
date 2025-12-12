from __future__ import annotations

from pygame.math import Vector2

from ..game_state import GameState
from ..components import Position, Velocity, ItemTag, Item, ItemCollectState
from ..game_config import CollectConfig


def item_autocollect_system(state: GameState, dt: float) -> None:
    """
    道具吸附系统：
    1. PoC线以上 -> 标记为 POC_COLLECT，速度 poc_magnet_speed (500px/s)
    2. 64px范围内 -> 标记为 MAGNET_ATTRACT，速度 attract_speed (300px/s)
    3. 优先级：POC_COLLECT > MAGNET_ATTRACT > NONE
    4. 状态只能升级，不能降级（一旦被吸附就保持追踪）
    """
    player = state.get_player()
    if not player:
        return

    cfg: CollectConfig = state.get_resource(CollectConfig)  # type: ignore
    if cfg is None:
        cfg = CollectConfig()

    p_pos = player.get(Position)
    if not p_pos:
        return

    poc_active = state.poc_active
    attract_radius_sq = cfg.attract_radius ** 2

    for actor in state.actors:
        if not actor.get(ItemTag):
            continue

        i_pos = actor.get(Position)
        i_vel = actor.get(Velocity)
        item = actor.get(Item)
        if not (i_pos and i_vel and item):
            continue

        # 步骤 1：检测并更新收集状态（只升级不降级）
        if poc_active:
            # PoC 激活时强制升级为 POC_COLLECT
            item.collect_state = ItemCollectState.POC_COLLECT
        elif item.collect_state == ItemCollectState.NONE:
            # 未被吸附时检测范围吸附
            dx = p_pos.x - i_pos.x
            dy = p_pos.y - i_pos.y
            dist_sq = dx * dx + dy * dy
            if dist_sq <= attract_radius_sq:
                item.collect_state = ItemCollectState.MAGNET_ATTRACT

        # 步骤 2：根据状态应用吸附速度
        if item.collect_state == ItemCollectState.NONE:
            continue  # 未被吸附，继续重力下落

        # 选择吸附速度
        if item.collect_state == ItemCollectState.POC_COLLECT:
            speed = cfg.poc_magnet_speed
        else:  # 范围吸附
            speed = cfg.attract_speed

        # 计算方向并应用速度
        to_player = Vector2(p_pos.x - i_pos.x, p_pos.y - i_pos.y)
        if to_player.length_squared() > 0:
            i_vel.vec = to_player.normalize() * speed
