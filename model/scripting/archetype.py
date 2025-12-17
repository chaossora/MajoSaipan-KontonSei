"""
BulletArchetype：弹幕引擎的子弹原型系统。

提供子弹原型注册表，定义不同子弹类型的默认属性
（伤害、精灵、半径、碰撞层/掩码）。

**Feature: danmaku-engine-refactor**
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

from model.components import CollisionLayer


logger = logging.getLogger(__name__)


@dataclass
class BulletArchetype:
    """
    子弹原型定义。
    
    定义某种子弹类型的默认属性。
    生成子弹时，除非被覆盖，否则使用这些属性。
    
    Attributes:
        id: 此原型的唯一标识符
        damage: 命中时造成的伤害
        sprite: 渲染用的精灵名
        radius: 碰撞半径（像素）
        layer: 碰撞层（此子弹属于哪个组）
        mask: 碰撞掩码（此子弹可以与哪些组碰撞）
        lifetime: 默认生命周期（秒）
    """
    id: str
    damage: int = 1
    sprite: str = "bullet_basic"
    radius: float = 4.0
    layer: CollisionLayer = CollisionLayer.ENEMY_BULLET
    mask: CollisionLayer = CollisionLayer.PLAYER | CollisionLayer.PLAYER_BULLET
    lifetime: float = 30.0


# 全局原型注册表
_bullet_archetypes: Dict[str, BulletArchetype] = {}


def register_archetype(archetype: BulletArchetype) -> None:
    """
    在全局注册表中注册子弹原型。
    
    Args:
        archetype: 要注册的 BulletArchetype
    """
    _bullet_archetypes[archetype.id] = archetype


def get_archetype(archetype_id: str) -> BulletArchetype:
    """
    通过 ID 获取子弹原型。
    
    如果未找到原型，返回 "default" 原型并记录警告。
    如果 "default" 也未找到，返回一个后备原型。
    
    Args:
        archetype_id: 要获取的原型 ID
    
    Returns:
        请求的 BulletArchetype，如果未找到则返回默认值
    """
    if archetype_id in _bullet_archetypes:
        return _bullet_archetypes[archetype_id]
    
    logger.warning(f"原型 '{archetype_id}' 未找到，使用默认值")
    
    if "default" in _bullet_archetypes:
        return _bullet_archetypes["default"]
    
    # 如果连 default 都未注册，返回后备值
    return BulletArchetype(
        id="default",
        damage=1,
        sprite="bullet_basic",
        radius=4.0,
        layer=CollisionLayer.ENEMY_BULLET,
        mask=CollisionLayer.PLAYER | CollisionLayer.PLAYER_BULLET,
        lifetime=30.0,
    )


def clear_archetypes() -> None:
    """
    清除所有已注册的原型。
    
    主要用于测试，在测试之间重置状态。
    """
    _bullet_archetypes.clear()


def get_all_archetypes() -> Dict[str, BulletArchetype]:
    """
    获取所有已注册原型的副本。
    
    Returns:
        原型 ID 到 BulletArchetype 实例的字典
    """
    return dict(_bullet_archetypes)


def register_default_archetypes() -> None:
    """
    注册默认的子弹原型。
    
    应在游戏初始化时调用，以确保标准原型可用。
    
    注册的原型：
    - "default": 基础子弹，标准属性
    - "bullet_small": 小型子弹，快速，低伤害
    - "bullet_medium": 中型子弹，平衡属性
    - "bullet_large": 大型子弹，慢速，高伤害
    """
    # 默认原型 - 基础子弹
    register_archetype(BulletArchetype(
        id="default",
        damage=1,
        sprite="bullet_basic",
        radius=4.0,
        layer=CollisionLayer.ENEMY_BULLET,
        mask=CollisionLayer.PLAYER | CollisionLayer.PLAYER_BULLET,
        lifetime=30.0,
    ))
    
    # 小型子弹 - 快速，低伤害
    register_archetype(BulletArchetype(
        id="bullet_small",
        damage=1,
        sprite="bullet_small",
        radius=3.0,
        layer=CollisionLayer.ENEMY_BULLET,
        mask=CollisionLayer.PLAYER | CollisionLayer.PLAYER_BULLET,
        lifetime=30.0,
    ))
    
    # 中型子弹 - 平衡
    register_archetype(BulletArchetype(
        id="bullet_medium",
        damage=2,
        sprite="bullet_medium",
        radius=5.0,
        layer=CollisionLayer.ENEMY_BULLET,
        mask=CollisionLayer.PLAYER | CollisionLayer.PLAYER_BULLET,
        lifetime=30.0,
    ))
    
    # 大型子弹 - 慢速，高伤害
    register_archetype(BulletArchetype(
        id="bullet_large",
        damage=3,
        sprite="bullet_large",
        radius=8.0,
        layer=CollisionLayer.ENEMY_BULLET,
        mask=CollisionLayer.PLAYER | CollisionLayer.PLAYER_BULLET,
        lifetime=30.0,
    ))
    
    # Boss Blue (Small)
    register_archetype(BulletArchetype(
        id="boss_blue",
        damage=1,
        sprite="boss_bullet_blue",
        radius=6.0,
        layer=CollisionLayer.ENEMY_BULLET,
        mask=CollisionLayer.PLAYER | CollisionLayer.PLAYER_BULLET,
        lifetime=30.0,
    ))
    
    # Boss Red (Large)
    register_archetype(BulletArchetype(
        id="boss_red",
        damage=2,
        sprite="boss_bullet_red",
        radius=8.0,
        layer=CollisionLayer.ENEMY_BULLET,
        mask=CollisionLayer.PLAYER | CollisionLayer.PLAYER_BULLET,
        lifetime=30.0,
    ))
