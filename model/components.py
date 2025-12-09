from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntFlag, Enum, auto
from typing import List

from pygame.math import Vector2


# ====== 核心物理组件 ======

class CollisionLayer(IntFlag):
    NONE = 0
    PLAYER = auto()
    ENEMY = auto()
    PLAYER_BULLET = auto()
    ENEMY_BULLET = auto()
    ITEM = auto()


@dataclass
class Position:
    x: float
    y: float


@dataclass
class Velocity:
    """速度向量，使用 pygame.math.Vector2 存储。"""
    vec: Vector2


@dataclass
class Gravity:
    """简单的垂直重力。"""
    g: float = 0.0
    max_fall_speed: float = 9999.0


@dataclass
class MoveStats:
    speed_normal: float
    speed_focus: float


@dataclass
class SpriteInfo:
    name: str
    offset_x: int = 0
    offset_y: int = 0
    visible: bool = True


@dataclass
class Collider:
    radius: float
    layer: CollisionLayer
    mask: CollisionLayer


@dataclass
class Health:
    max_hp: int
    hp: int


@dataclass
class Lifetime:
    time_left: float


@dataclass
class Bullet:
    damage: int


@dataclass
class BulletGrazeState:
    """敌弹是否已被擦过一次。"""
    grazed: bool = False


# ====== 玩家射击组件 ======

@dataclass
class FocusState:
    """玩家是否按住低速键（Shift）。"""
    is_focusing: bool = False


@dataclass
class Shooting:
    """运行时射击状态：仅包含冷却计时器。"""
    cooldown: float
    timer: float = 0.0


@dataclass
class ShotOriginOffset:
    """子弹生成位置相对于玩家位置的偏移。"""
    bullet_spawn_offset_y: float = 16.0


@dataclass
class ShotConfig:
    """
    玩家射击配置（组件）。
    shot_type: 用于从注册表中选择处理函数（延迟绑定）。
    angles_*: 角度；0 表示正上方。
    """
    shot_type: object = None  # ShotKind (late import to avoid cycle)
    cooldown: float = 0.08
    bullet_speed: float = 520.0
    damage: int = 1
    angles_spread: List[float] = field(default_factory=lambda: [-10.0, 0.0, 10.0])
    angles_focus: List[float] = field(default_factory=lambda: [-3.0, 0.0, 3.0])
    bullet_sprite: str = "player_bullet_basic"


@dataclass
class BombConfigData:
    """玩家炸弹配置（组件）。"""
    bomb_type: object = None  # BombType（延迟导入）
    duration: float = 0.8
    invincible_time: float = 2.0
    radius: float = 96.0
    beam_width: float = 64.0
    beam_length: float = 600.0
    effect_sprite: str = "bomb_field"


# ====== 敌人射击组件 ======

@dataclass
class EnemyShootingV2:
    """
    敌人射击配置，使用 BulletPatternConfig。
    pattern/state 类型延迟绑定以避免循环导入。
    """
    cooldown: float
    pattern: object  # BulletPatternConfig 弹幕配置
    timer: float = 0.0
    state: object | None = None  # PatternState 弹幕状态


# ====== 玩家状态组件 ======

@dataclass
class PlayerPower:
    power: float
    max_power: float


@dataclass
class PlayerScore:
    score: int = 0


@dataclass
class PlayerGraze:
    count: int = 0


@dataclass
class PlayerLife:
    lives: int
    max_lives: int


@dataclass
class PlayerBomb:
    bombs: int
    max_bombs: int


@dataclass
class PlayerDamageState:
    invincible_timer: float = 0.0
    deathbomb_timer: float = 0.0
    deathbomb_window: float = 0.1
    pending_death: bool = False


# ====== 道具组件 ======

class ItemType(Enum):
    POWER = auto()
    POINT = auto()
    BOMB = auto()
    LIFE = auto()


@dataclass
class Item:
    type: ItemType
    value: int = 1
    auto_collect: bool = False


# ====== 敌人组件 ======

@dataclass
class EnemyJustDied:
    by_player_bullet: bool = False
    by_bomb: bool = False


@dataclass
class EnemyDropConfig:
    power_count: int = 0
    point_count: int = 0
    scatter_radius: float = 12.0


class EnemyKind(Enum):
    FAIRY_SMALL = auto()
    FAIRY_LARGE = auto()
    MIDBOSS = auto()
    BOSS = auto()


@dataclass
class EnemyKindTag:
    kind: EnemyKind


@dataclass
class PathFollower:
    path_name: str
    t: float = 0.0
    origin_x: float = 0.0
    origin_y: float = 0.0
    initialized: bool = False


# ====== 标签组件 ======

@dataclass
class PlayerTag:
    pass


@dataclass
class EnemyTag:
    pass


@dataclass
class PlayerBulletTag:
    pass


@dataclass
class EnemyBulletTag:
    pass


@dataclass
class BombFieldTag:
    pass


@dataclass
class ItemTag:
    pass


# ====== 渲染提示 / HUD 组件 ======

@dataclass
class RenderHint:
    show_hitbox: bool = False
    show_graze_field: bool = False
    graze_field_radius: float = 0.0


@dataclass
class HudData:
    score: int = 0
    lives: int = 0
    max_lives: int = 0
    bombs: int = 0
    max_bombs: int = 0
    power: float = 0.0
    max_power: float = 0.0
    graze_count: int = 0


# ====== 输入组件 ======

@dataclass
class InputState:
    left: bool = False
    right: bool = False
    up: bool = False
    down: bool = False
    focus: bool = False
    shoot: bool = False
    shoot_pressed: bool = False
    bomb: bool = False           # 当前帧是否按住
    bomb_pressed: bool = False   # 边缘检测：本帧是否按下


@dataclass
class PlayerRespawnState:
    """玩家重生状态，用于闪烁效果控制"""
    respawning: bool = False
    blink_timer: float = 0.0
    blink_interval: float = 0.1
