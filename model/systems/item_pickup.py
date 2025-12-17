from __future__ import annotations

from typing import Set

from ..game_state import GameState
from ..components import ItemTag, Item
from ..collision_events import CollisionEvents
from ..item_effects import apply_item_effect


def item_pickup_system(state: GameState, dt: float) -> None:
    """
    基于 CollisionEvents 的道具拾取系统；避免距离检测。
    """
    player = state.get_player()
    if not player:
        return

    events: CollisionEvents = state.collision_events
    consumed_items: Set[object] = set()

    for ev in events.player_pickup_item:
        item_actor = ev.item
        if item_actor in consumed_items:
            continue
        consumed_items.add(item_actor)

        if not item_actor.has(ItemTag):
            continue

        item = item_actor.get(Item)
        if not item:
            continue

        apply_item_effect(
            state,
            player,
            item_actor,
            item.type,
            item.value,
        )

    for item_actor in consumed_items:
        state.remove_actor(item_actor)

    if consumed_items:
         if "item_get" not in state.sfx_requests:
            state.sfx_requests.append("item_get")
