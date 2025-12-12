from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import List, Optional

from pygame.math import Vector2

from .actor import Actor
from .components import (
    Position,
    Velocity,
    MoveStats,
    SpriteInfo,
    Collider,
    CollisionLayer,
    Health,
    Lifetime,
    Bullet,
    BulletGrazeState,
    PlayerTag,
    EnemyTag,
    PlayerBulletTag,
    PlayerBulletKind,
    PlayerBulletKindTag,
    EnemyBulletTag,
    EnemyBulletKind,
    EnemyBulletKindTag,
    FocusState,
    EnemyShootingV2,
    PlayerLife,
    PlayerBomb,
    PlayerDamageState,
    PlayerRespawnState,
    BombFieldTag,
    PlayerPower,
    PlayerScore,
    PlayerGraze,
    GrazeEnergy,
    Gravity,
    ItemType,
    Item,
    ItemTag,
    EnemyDropConfig,
    RenderHint,
    HudData,
    ShotOriginOffset,
    BombConfigData,
    InputState,
    OptionConfig,
    OptionState,
    PlayerShotPattern,
)
from .game_config import (
    CollectConfig,
    GrazeConfig,
    GrazeEnergyConfig,
    PlayerConfig,
    BombConfig,
    BoundaryConfig,
)
from .collision_events import CollisionEvents
from .stage import StageState
from .movement_path import PathLibrary, create_default_path_library
from .bullet_patterns import BulletPatternConfig, BulletPatternKind
from .character import CharacterId, get_character_preset
from .bomb_handlers import BombType


@dataclass
class EntityStats:
    """实体统计信息，用于 HUD / 调试。"""

    total: int = 0
    enemies: int = 0
    enemy_bullets: int = 0
    player_bullets: int = 0
    items: int = 0


@dataclass
class GameState:
    """
    纯逻辑世界：
    - 拥有所有游戏对象
    - 跟踪时间/帧数
    - 存储世界大小、PoC 状态、配置等资源
    """

    actors: List[Actor] = field(default_factory=list)
    player: Optional[Actor] = None

    time: float = 0.0  # 已用游戏时间（秒）
    frame: int = 0  # 帧计数
    collision_events: CollisionEvents = field(default_factory=CollisionEvents)

    # 世界大小（屏幕）
    width: int = 0
    height: int = 0

    # 点收集（Point-of-Collection）激活状态（由 poc_system 设置）
    poc_active: bool = False

    # 全局资源（配置等）
    resources: dict[type, object] = field(default_factory=dict)

    stage: Optional[StageState] = None  # 当前关卡时间线

    # 移动路径库
    path_library: PathLibrary = field(default_factory=create_default_path_library)

    # HUD 和调试用统计
    entity_stats: EntityStats = field(default_factory=EntityStats)

    # 游戏结束标志（玩家残机 <= 0）
    game_over: bool = False

    def __post_init__(self) -> None:
        # 初始化缺少的默认资源
        defaults = [
            CollectConfig(),
            GrazeConfig(),
            GrazeEnergyConfig(),
            PlayerConfig(),
            BombConfig(),
            BoundaryConfig(),
        ]
        for res in defaults:
            self.resources.setdefault(type(res), res)

    def add_actor(self, actor: Actor) -> None:
        self.actors.append(actor)

    def remove_actor(self, actor: Actor) -> None:
        if actor in self.actors:
            self.actors.remove(actor)

    # 便捷辅助方法：玩家查找（预留多人模式支持）
    def get_player(self) -> Optional[Actor]:
        return next((a for a in self.actors if a.get(PlayerTag)), None)

    def get_players(self) -> list[Actor]:
        return [a for a in self.actors if a.get(PlayerTag)]

    # ====== 资源辅助方法 ======
    def set_resource(self, res: object) -> None:
        self.resources[type(res)] = res

    def get_resource(self, res_type: type) -> object | None:
        return self.resources.get(res_type)


# ======= 实体工厂函数 =======

DEFAULT_SHOOT_COOLDOWN = 0.08
DEFAULT_BULLET_SPEED = 520.0


def spawn_player(state: GameState, x: float, y: float, character_id: Optional[CharacterId] = None) -> Actor:
    player = Actor()
    cfg: PlayerConfig = state.get_resource(PlayerConfig)  # type: ignore
    preset = get_character_preset(character_id) if character_id else None

    player.add(Position(x, y))
    player.add(Velocity(Vector2(0, 0)))

    # 移动速度
    speed_normal = preset.speed_normal if preset else (cfg.speed_normal if cfg else 220.0)
    speed_focus = preset.speed_focus if preset else (cfg.speed_focus if cfg else 120.0)
    player.add(MoveStats(speed_normal=speed_normal, speed_focus=speed_focus))

    player.add(PlayerTag())

    # 碰撞体
    collider_radius = preset.collider_radius if preset else 3.0
    player.add(
        Collider(
            radius=collider_radius,
            layer=CollisionLayer.PLAYER,
            mask=(CollisionLayer.ENEMY | CollisionLayer.ENEMY_BULLET | CollisionLayer.ITEM),
        )
    )

    # 生命值（使用残机数）
    initial_lives = preset.initial_lives if preset else 3

    # 精灵图
    sprite_name = preset.sprite_name if preset else "player_default"
    offset_x = preset.sprite_offset_x if preset else -16
    offset_y = preset.sprite_offset_y if preset else -16
    player.add(SpriteInfo(name=sprite_name, offset_x=offset_x, offset_y=offset_y))

    player.add(FocusState(is_focusing=False))

    # 射击配置：使用 PlayerShotPattern
    if preset and hasattr(preset, 'shot_pattern') and preset.shot_pattern:
        player.add(PlayerShotPattern(pattern=copy.deepcopy(preset.shot_pattern)))
    else:
        # 默认配置
        from .player_shot_patterns import PlayerShotPatternConfig, PlayerShotPatternKind
        player.add(PlayerShotPattern(pattern=PlayerShotPatternConfig(
            kind=PlayerShotPatternKind.SPREAD,
            cooldown=DEFAULT_SHOOT_COOLDOWN,
            bullet_speed=DEFAULT_BULLET_SPEED,
            damage=1,
        )))

    spawn_offset_y = preset.bullet_spawn_offset_y if preset else (cfg.bullet_spawn_offset_y if cfg else 16.0)
    player.add(ShotOriginOffset(bullet_spawn_offset_y=spawn_offset_y))

    # 炸弹配置
    if preset:
        bomb_cfg = copy.deepcopy(preset.bomb)
    else:
        bomb_defaults: BombConfig = state.get_resource(BombConfig) or BombConfig()  # type: ignore
        bomb_cfg = BombConfigData(
            bomb_type=BombType.CIRCLE,
            duration=bomb_defaults.duration,
            invincible_time=bomb_defaults.invincible_time,
            radius=bomb_defaults.radius,
            effect_sprite="bomb_field",
        )
    player.add(bomb_cfg)

    # 残机 / 炸弹 / 受伤窗口
    max_lives = preset.max_lives if preset else 8
    max_bombs = preset.max_bombs if preset else 8
    initial_bombs = preset.initial_bombs if preset else 3
    deathbomb_window = preset.deathbomb_window if preset else 0.1

    player.add(PlayerLife(lives=initial_lives, max_lives=max_lives))
    player.add(PlayerBomb(bombs=initial_bombs, max_bombs=max_bombs))
    player.add(PlayerDamageState(deathbomb_window=deathbomb_window))
    player.add(PlayerRespawnState())

    max_power = preset.max_power if preset else (cfg.max_power if cfg else 4.0)
    player.add(PlayerPower(power=0.0, max_power=max_power))
    player.add(PlayerScore(score=0))
    player.add(PlayerGraze())

    # 擦弹能量系统
    energy_cfg: GrazeEnergyConfig = state.get_resource(GrazeEnergyConfig) or GrazeEnergyConfig()  # type: ignore
    player.add(GrazeEnergy(
        energy=0.0,
        max_energy=energy_cfg.max_energy,
        is_enhanced=False,
        decay_timer=0.0,
        last_graze_count=0,
    ))

    # 输入组件
    player.add(InputState())

    # 子机配置和状态
    if preset:
        option_cfg = copy.deepcopy(preset.option)
    else:
        # 默认子机配置（无角色预设时使用）
        option_cfg = OptionConfig(
            max_options=4,
            damage_ratio=0.5,
            option_sprite="option",
            transition_speed=8.0,
            # 动态位置参数
            base_spread_x=40.0,
            focus_spread_x=15.0,
            base_offset_y=-10.0,
            focus_offset_y=-5.0,
            outer_offset_y=10.0,
            # 默认直射
            option_shot_kind=None,
        )
    player.add(option_cfg)
    player.add(OptionState(active_count=0, current_positions=[]))

    # 渲染提示 / HUD
    player.add(RenderHint())
    player.add(HudData())

    state.add_actor(player)
    state.player = player
    return player


def spawn_player_bullet(
    state: GameState,
    x: float,
    y: float,
    damage: int = 1,
    speed: float = 400.0,
    angle_deg: float = 0.0,
    bullet_kind: PlayerBulletKind = PlayerBulletKind.MAIN_NORMAL,
    collider_radius: float = 4.0,
    lifetime: float = 2.0,
) -> Actor:
    bullet = Actor()

    base_dir = Vector2(0, -1)  # 向上
    dir_vec = base_dir.rotate(angle_deg)
    vel_vec = dir_vec * speed

    bullet.add(Position(x, y))
    bullet.add(Velocity(vel_vec))

    bullet.add(PlayerBulletTag())
    bullet.add(PlayerBulletKindTag(kind=bullet_kind))  # View 层根据此类型查表渲染
    bullet.add(Bullet(damage=damage))

    bullet.add(Collider(radius=collider_radius, layer=CollisionLayer.PLAYER_BULLET, mask=CollisionLayer.ENEMY))

    bullet.add(Lifetime(time_left=lifetime))

    state.add_actor(bullet)
    return bullet


def spawn_player_bullet_with_velocity(
    state: GameState,
    x: float,
    y: float,
    velocity: Vector2,
    damage: int = 1,
    bullet_kind: PlayerBulletKind = PlayerBulletKind.MAIN_NORMAL,
    collider_radius: float = 4.0,
    lifetime: float = 2.0,
) -> Actor:
    """使用速度向量生成玩家子弹（新版 PlayerShotPattern 使用）"""
    bullet = Actor()

    bullet.add(Position(x, y))
    bullet.add(Velocity(velocity))

    bullet.add(PlayerBulletTag())
    bullet.add(PlayerBulletKindTag(kind=bullet_kind))
    bullet.add(Bullet(damage=damage))

    bullet.add(Collider(radius=collider_radius, layer=CollisionLayer.PLAYER_BULLET, mask=CollisionLayer.ENEMY))

    bullet.add(Lifetime(time_left=lifetime))

    state.add_actor(bullet)
    return bullet


def spawn_enemy_bullet(
    state: GameState,
    x: float,
    y: float,
    velocity: Vector2,
    damage: int = 1,
    bullet_kind: EnemyBulletKind = EnemyBulletKind.BASIC,
    collider_radius: float = 4.0,
    lifetime: float = 4.0,
) -> Actor:
    bullet = Actor()

    bullet.add(Position(x, y))
    bullet.add(Velocity(velocity))

    bullet.add(EnemyBulletTag())
    bullet.add(EnemyBulletKindTag(bullet_kind))
    bullet.add(Bullet(damage=damage))
    bullet.add(BulletGrazeState())

    bullet.add(
        Collider(
            radius=collider_radius,
            layer=CollisionLayer.ENEMY_BULLET,
            mask=CollisionLayer.PLAYER | CollisionLayer.PLAYER_BULLET,
        )
    )

    bullet.add(Lifetime(time_left=lifetime))

    state.add_actor(bullet)
    return bullet


def spawn_bomb_field(state: GameState, x: float, y: float, radius: float = 96.0, duration: float = 0.8) -> Actor:
    """
    创建炸弹场实体：
    - 圆形碰撞体
    - 生命周期
    - BombFieldTag（碰撞系统会清除子弹/伤害敌人）
    """
    bomb = Actor()

    bomb.add(Position(x, y))
    bomb.add(Collider(radius=radius, layer=CollisionLayer.PLAYER_BULLET, mask=CollisionLayer.ENEMY | CollisionLayer.ENEMY_BULLET))

    bomb.add(BombFieldTag())
    bomb.add(Lifetime(time_left=duration))

    bomb.add(SpriteInfo(name="bomb_field", offset_x=int(-radius), offset_y=int(-radius)))

    state.add_actor(bomb)
    return bomb


def spawn_item(
    state: GameState,
    x: float,
    y: float,
    item_type: ItemType,
    value: int = 1,
    pickup_radius: float = 12.0,
    gravity: float = 200.0,
    max_fall_speed: float = 220.0,
    initial_up_speed: float = 120.0,
    lifetime: float = 8.0,
) -> Actor:
    """
    创建基础道具实体：
    - 初始向上速度
    - 重力和终端速度
    - 生命周期
    """
    item = Actor()

    item.add(Position(x, y))

    # 初始向上速度
    item.add(Velocity(Vector2(0, -initial_up_speed)))

    # 重力组件
    item.add(Gravity(g=gravity, max_fall_speed=max_fall_speed))

    item.add(Item(type=item_type, value=value))
    item.add(ItemTag())

    if item_type == ItemType.POWER:
        sprite_name = "item_power"
    elif item_type == ItemType.POINT:
        sprite_name = "item_point"
    else:
        sprite_name = "item_power"

    item.add(Collider(radius=pickup_radius, layer=CollisionLayer.ITEM, mask=CollisionLayer.PLAYER))

    item.add(SpriteInfo(name=sprite_name, offset_x=-8, offset_y=-8))

    item.add(Lifetime(time_left=lifetime))

    state.add_actor(item)
    return item
