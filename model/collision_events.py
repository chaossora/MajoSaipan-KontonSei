# 碰撞事件定义
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .actor import Actor


# --- 基础事件类型 ---

@dataclass
class PlayerBulletHitEnemy:
    """玩家子弹命中敌人"""
    bullet: Actor
    enemy: Actor


@dataclass
class EnemyBulletHitPlayer:
    """敌弹命中玩家"""
    bullet: Actor
    player: Actor


@dataclass
class BombHitEnemy:
    """炸弹命中敌人"""
    bomb: Actor
    enemy: Actor


@dataclass
class BombClearedEnemyBullet:
    """炸弹清除敌弹"""
    bomb: Actor
    bullet: Actor


@dataclass
class PlayerPickupItem:
    """玩家拾取道具"""
    player: Actor
    item: Actor


@dataclass
class PlayerGrazeEnemyBullet:
    """
    玩家擦弹事件：记录玩家和子弹
    """
    player: Actor
    bullet: Actor


# 以后可以在这里继续添加其他事件类型：
# @dataclass
# class PlayerEnterTrigger: ...


@dataclass
class CollisionEvents:
    """这一帧内发生的所有碰撞事件，按类型分类存储。"""

    player_bullet_hits_enemy: List[PlayerBulletHitEnemy] = field(default_factory=list)
    enemy_bullet_hits_player: List[EnemyBulletHitPlayer] = field(default_factory=list)
    bomb_hits_enemy: List[BombHitEnemy] = field(default_factory=list)
    bomb_clears_enemy_bullet: List[BombClearedEnemyBullet] = field(default_factory=list)
    player_pickup_item: List[PlayerPickupItem] = field(default_factory=list)
    player_graze_enemy_bullet: List[PlayerGrazeEnemyBullet] = field(default_factory=list)

    def clear(self) -> None:
        self.player_bullet_hits_enemy.clear()
        self.enemy_bullet_hits_player.clear()
        self.bomb_hits_enemy.clear()
        self.bomb_clears_enemy_bullet.clear()
        self.player_pickup_item.clear()
        self.player_graze_enemy_bullet.clear()
