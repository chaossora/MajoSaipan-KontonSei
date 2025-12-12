from __future__ import annotations

from ..game_state import GameState
from ..components import Position, Collider, PlayerTag, PlayerBulletTag, EnemyBulletTag
from ..game_config import BoundaryConfig


def boundary_system(state: GameState) -> None:
    """
    边界处理系统：
    1. 玩家限制在屏幕内
    2. 子弹出界后删除

    职责：处理实体与世界边界的交互，从movement_system中分离出来，
    遵循单一职责原则。
    """
    world_w = state.width
    world_h = state.height
    cfg: BoundaryConfig = state.get_resource(BoundaryConfig)  # type: ignore
    out_buffer = cfg.out_buffer if cfg else 32.0

    to_remove = []

    for actor in state.actors:
        pos = actor.get(Position)
        if not pos:
            continue

        # 玩家边界限制
        if actor.has(PlayerTag):
            col = actor.get(Collider)
            r = col.radius if col else 0.0
            if world_w > 0:
                pos.x = max(r, min(world_w - r, pos.x))
            if world_h > 0:
                pos.y = max(r, min(world_h - r, pos.y))

        # 子弹出界清理
        elif actor.has(PlayerBulletTag) or actor.has(EnemyBulletTag):
            if (
                pos.x < -out_buffer
                or pos.x > world_w + out_buffer
                or pos.y < -out_buffer
                or pos.y > world_h + out_buffer
            ):
                to_remove.append(actor)

    # 统一删除出界子弹，避免在遍历中修改列表
    for actor in to_remove:
        state.remove_actor(actor)
