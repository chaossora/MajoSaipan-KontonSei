from __future__ import annotations

from ..game_state import GameState
from ..actor import Actor
from ..components import (
    EnemyBulletTag,
    EnemyTag,
    EnemyKindTag,
    EnemyKind,
    EnemyJustDied,
    Position,
    PlayerDamageState,
    PlayerRespawnState,
    SpriteInfo,
)


def clear_enemy_bullets(state: GameState) -> None:
    """清除所有敌弹"""
    to_remove = [a for a in state.actors if a.has(EnemyBulletTag)]
    for actor in to_remove:
        state.remove_actor(actor)


def clear_non_boss_enemies(state: GameState) -> None:
    """清除所有非 BOSS 敌人，正常掉落道具（通过 EnemyJustDied 标记）"""
    for actor in state.actors:
        if not actor.has(EnemyTag):
            continue
        kind_tag = actor.get(EnemyKindTag)
        # 只保留 Boss
        if kind_tag and kind_tag.kind == EnemyKind.BOSS:
            continue
        # 标记死亡，由 enemy_death_system 处理掉落
        if not actor.get(EnemyJustDied):
            actor.add(EnemyJustDied(by_player_bullet=False, by_bomb=False))


def respawn_player(state: GameState, player: Actor) -> None:
    """将玩家重置到底部中央"""
    pos = player.get(Position)
    if pos:
        pos.x = state.width / 2
        pos.y = state.height - 64


def apply_death_effect(state: GameState, player: Actor) -> None:
    """玩家死亡时调用：清弹、清敌、重生"""
    clear_enemy_bullets(state)
    clear_non_boss_enemies(state)
    respawn_player(state, player)

    # 启动重生闪烁效果
    respawn = player.get(PlayerRespawnState)
    if respawn:
        respawn.respawning = True
        respawn.blink_timer = 0.0


def player_respawn_visual_system(state: GameState, dt: float) -> None:
    """处理玩家重生时的闪烁效果，更新 SpriteInfo.visible"""
    player = state.get_player()
    if not player:
        return

    dmg = player.get(PlayerDamageState)
    respawn = player.get(PlayerRespawnState)
    sprite = player.get(SpriteInfo)
    if not (dmg and respawn and sprite):
        return

    # 无敌时间结束时停止闪烁效果
    if dmg.invincible_timer <= 0.0:
        respawn.respawning = False
        sprite.visible = True
        return

    if respawn.respawning:
        respawn.blink_timer += dt
        if respawn.blink_timer >= respawn.blink_interval:
            respawn.blink_timer = 0.0
            sprite.visible = not sprite.visible
