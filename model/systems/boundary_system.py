from __future__ import annotations

from ..game_state import GameState
from ..components import Position, Velocity, Collider, PlayerTag, PlayerBulletTag, EnemyBulletTag, BulletBounce
from ..game_config import BoundaryConfig


def boundary_system(state: GameState) -> None:
    """
    边界处理系统：
    1. 玩家限制在屏幕内
    2. 子弹出界后删除（或反弹）

    职责：处理实体与世界边界的交互，从movement_system中分离出来，
    遵循单一职责原则。

    优化：使用反向遍历和 del 删除，避免创建临时列表。
    保持列表顺序以确保确定性（Requirements 13.6）。
    Requirements 14.1: 提供迭代器接口避免创建临时列表
    """
    world_w = state.width
    world_h = state.height
    cfg: BoundaryConfig = state.get_resource(BoundaryConfig)  # type: ignore
    out_buffer = cfg.out_buffer if cfg else 32.0

    # 反向遍历，允许原地删除而不影响遍历顺序
    # 使用 del 保持列表顺序（O(n) 但保证确定性）
    i = len(state.actors) - 1
    while i >= 0:
        actor = state.actors[i]
        pos = actor.get(Position)

        if pos is None:
            i -= 1
            continue

        # 玩家边界限制
        if actor.has(PlayerTag):
            col = actor.get(Collider)
            r = col.radius if col else 0.0
            if world_w > 0:
                pos.x = max(r, min(world_w - r, pos.x))
            if world_h > 0:
                pos.y = max(r, min(world_h - r, pos.y))

        # 子弹边界处理（反弹或删除）
        elif actor.has(PlayerBulletTag) or actor.has(EnemyBulletTag):
            bounce = actor.get(BulletBounce)
            vel = actor.get(Velocity)

            # 检查是否出界
            out_left = pos.x < 0
            out_right = pos.x > world_w
            out_top = pos.y < 0
            out_bottom = pos.y > world_h

            if out_left or out_right or out_top or out_bottom:
                # 如果有反弹组件且还有反弹次数
                if bounce and vel and bounce.bounce_count < bounce.max_bounces:
                    # 水平边界反弹
                    if out_left:
                        pos.x = 0
                        vel.vec.x = abs(vel.vec.x)
                    elif out_right:
                        pos.x = world_w
                        vel.vec.x = -abs(vel.vec.x)

                    # 垂直边界反弹
                    if out_top:
                        pos.y = 0
                        vel.vec.y = abs(vel.vec.y)
                    elif out_bottom:
                        pos.y = world_h
                        vel.vec.y = -abs(vel.vec.y)

                    bounce.bounce_count += 1
                else:
                    # 没有反弹组件或反弹次数用完，检查是否超出缓冲区
                    if (
                        pos.x < -out_buffer
                        or pos.x > world_w + out_buffer
                        or pos.y < -out_buffer
                        or pos.y > world_h + out_buffer
                    ):
                        del state.actors[i]

        i -= 1
