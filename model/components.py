from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntFlag, Enum, auto
from typing import List, Optional, Callable, Generator, Any

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
class HomingBullet:
    """追踪子弹组件（ECS纯数据）：子弹会持续追踪最近的敌人。"""
    turn_rate: float = 360.0  # 每秒转向角度（度）
    speed: float = 400.0      # 追踪速度（会覆盖原速度大小）


@dataclass
class BulletGrazeState:
    """敌弹是否已被擦过一次。"""
    grazed: bool = False


@dataclass
class BulletBounce:
    """子弹边界反弹组件。"""
    max_bounces: int = 1      # 最大反弹次数
    bounce_count: int = 0     # 已反弹次数


class PlayerBulletKind(Enum):
    """
    玩家子弹类型（Model 层只标记类型，View 层根据类型查表渲染）。
    """
    MAIN_NORMAL = auto()      # 主机普通弹
    MAIN_ENHANCED = auto()    # 主机增强弹
    OPTION_NORMAL = auto()    # 子机普通弹（非追踪）
    OPTION_ENHANCED = auto()  # 子机增强弹（非追踪）
    OPTION_TRACKING = auto()  # 子机追踪弹（Focus模式）


@dataclass
class PlayerBulletKindTag:
    """玩家子弹类型标记组件。"""
    kind: PlayerBulletKind = PlayerBulletKind.MAIN_NORMAL


# ====== 玩家射击组件 ======

@dataclass
class FocusState:
    """玩家是否按住低速键（Shift）。"""
    is_focusing: bool = False


@dataclass
class ShotOriginOffset:
    """子弹生成位置相对于玩家位置的偏移。"""
    bullet_spawn_offset_y: float = 16.0


@dataclass
class PlayerShotPattern:
    """
    玩家射击模式组件。
    pattern: PlayerShotPatternConfig 配置（延迟导入避免循环）。
    """
    pattern: object  # PlayerShotPatternConfig
    timer: float = 0.0


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
    damage: int = 9999  # 每帧伤害（对普通敌人相当于秒杀）
    # CONVERT 炸弹专用配置
    convert_speed: float = 350.0       # 转换后子弹追踪速度
    convert_turn_rate: float = 360.0   # 转换后子弹转向速率（度/秒）
    convert_damage: int = 5            # 转换后子弹伤害
    convert_lifetime: float = 10.0      # 转换后子弹生命周期


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
class GrazeEnergy:
    """
    擦弹能量状态组件（附加到玩家 Actor）。
    追踪当前能量值和增强状态。
    """
    energy: float = 0.0           # 当前能量值
    max_energy: float = 100.0     # 最大能量值
    is_enhanced: bool = False     # 是否处于增强状态
    decay_timer: float = 0.0      # 衰减延迟计时器（停止擦弹后多久开始衰减）
    last_graze_count: int = 0     # 上一帧的擦弹总数（用于计算增量）


@dataclass
class PlayerLife:
    lives: int
    max_lives: int


@dataclass
class PlayerBomb:
    bombs: int
    max_bombs: int
    active: bool = False  # 炸弹是否正在持续中


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


class ItemCollectState(Enum):
    """道具收集状态"""
    NONE = auto()           # 自由下落
    MAGNET_ATTRACT = auto() # 范围吸附（按高度计分）
    POC_COLLECT = auto()    # PoC吸附（满分）


@dataclass
class Item:
    """道具数据组件"""
    type: ItemType
    value: int = 1
    collect_state: ItemCollectState = field(default=ItemCollectState.NONE)

    @property
    def auto_collect(self) -> bool:
        """向后兼容属性：任何吸附状态都返回 True"""
        return self.collect_state != ItemCollectState.NONE


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


class EnemyBulletKind(Enum):
    """敌人子弹种类 - View 层根据此枚举查表获取精灵"""
    BASIC = auto()
    # 未来可扩展更多类型，如 LARGE, AIMED, LASER 等


@dataclass
class EnemyBulletKindTag:
    """敌人子弹种类标签 - Model 层只标记类型，View 层负责查表获取精灵"""
    kind: EnemyBulletKind


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
    # 擦弹能量系统
    graze_energy: float = 0.0
    max_graze_energy: float = 100.0
    is_enhanced: bool = False


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


# ====== Boss 组件 ======

class PhaseType(Enum):
    """Boss 阶段类型"""
    NON_SPELL = auto()    # 非符卡（通常弹幕）
    SPELL_CARD = auto()   # 符卡（有名称、奖励）
    SURVIVAL = auto()     # 生存符卡（Boss 无敌，玩家需存活）


@dataclass
class BossState:
    """
    Boss 核心状态组件（纯脚本驱动模式）。
    
    阶段管理完全由 Task 脚本控制，此组件只存储：
    - Boss 名称（用于 HUD）
    - 掉落配置
    - Bomb 抗性配置
    
    HP 由 Health 组件管理，符卡状态由 SpellCardState 组件管理。
    """
    boss_name: str

    # 掉落配置
    drop_power: int = 16
    drop_point: int = 24
    drop_life: int = 0
    drop_bomb: int = 0

    # Bomb 抗性配置（东方风格机制）
    bomb_damage_cap: int = 1              # 每帧最大 Bomb 伤害
    bomb_spell_immune: bool = False        # 符卡期间是否完全免疫 Bomb


@dataclass
class SpellCardState:
    """
    符卡状态组件（仅在符卡阶段添加）。
    用于跟踪符卡奖励资格和伤害倍率。
    """
    spell_name: str = ""
    spell_bonus_available: bool = True     # 未被击中、未 Bomb 则 True
    spell_bonus_value: int = 0
    damage_multiplier: float = 1.0
    invulnerable: bool = False             # 生存符卡时 True


@dataclass
class BossHudData:
    """
    Boss HUD 聚合数据（供渲染器使用）。
    由 boss_hud_system 每帧更新。
    """
    boss_name: str = ""
    hp_ratio: float = 1.0                  # 当前血量百分比
    phases_remaining: int = 0              # 剩余阶段数（星星显示）
    is_spell_card: bool = False
    spell_name: str = ""
    spell_bonus: int = 0
    spell_bonus_available: bool = True
    timer_seconds: float = 60.0
    visible: bool = True


# ====== 子机（Option）组件 ======

@dataclass
class OptionConfig:
    """
    子机配置（角色预设中使用）。
    定义子机的数量、位置、伤害等参数。
    使用动态对称位置计算，不再使用固定槽位。
    """
    max_options: int = 4                   # 最大子机数量
    damage_ratio: float = 0.5              # 子机伤害倍率（相对于主机）
    option_sprite: str = "option"          # 子机精灵名称
    transition_speed: float = 8.0          # 展开/收拢动画速度

    # 动态对称位置参数
    base_spread_x: float = 40.0            # 高速模式 X 扩散距离
    focus_spread_x: float = 15.0           # 低速模式 X 扩散距离
    base_offset_y: float = -10.0           # 高速模式 Y 偏移
    focus_offset_y: float = -5.0           # 低速模式 Y 偏移
    outer_offset_y: float = 10.0           # 外层子机 Y 偏移（4个时）

    # 射击类型（OptionShotKind，延迟导入避免循环）
    option_shot_kind: object = None

    # 子机射击参数（独立于主机）
    base_damage: int = 1                   # 子机基础伤害
    bullet_speed: float = 520.0            # 子机子弹速度


@dataclass
class OptionState:
    """
    子机运行时状态（附加到玩家 Actor）。
    跟踪当前激活的子机数量和位置。
    """
    active_count: int = 0                  # 当前激活子机数量（由 Power 决定）
    # 当前位置列表 [[x, y], ...]，用于平滑动画
    current_positions: List[List[float]] = field(default_factory=list)


@dataclass
class OptionTag:
    """子机实体标记（预留，用于独立子机实体）。"""
    slot_index: int = 0                    # 槽位索引 (0-3)


# ====== 激光组件 ======

class LaserType(Enum):
    """激光类型"""
    STRAIGHT = auto()      # 直线激光
    SINE_WAVE = auto()     # 正弦波激光


@dataclass
class LaserState:
    """
    激光状态组件。

    直线激光：使用 origin + angle + length 定义
    正弦波激光：沿主轴采样形成多线段

    判定逻辑：点到线段距离 <= laser_width/2 + player_hitbox_radius
    """
    laser_type: LaserType = LaserType.STRAIGHT

    # 几何参数
    width: float = 8.0              # 激光判定宽度
    length: float = 400.0           # 激光长度
    angle: float = 90.0             # 激光角度（度，90=向下）

    # 正弦波参数
    sine_amplitude: float = 50.0    # 波峰振幅（像素）
    sine_wavelength: float = 100.0  # 波长（像素）
    sine_phase: float = 0.0         # 相位（度）

    # 反射参数
    can_reflect: bool = False       # 是否支持边界反射
    reflect_count: int = 0          # 已反射次数
    max_reflects: int = 3           # 最大反射次数

    # 激光状态
    active: bool = True             # 是否激活（有判定）
    warmup_frames: int = 0          # 预热帧数（预警线显示期间无判定）
    warmup_timer: int = 0           # 预热计时器

    # 旋转参数
    angular_velocity: float = 0.0   # 角速度（度/帧）


@dataclass
class LaserTag:
    """激光实体标签"""
    pass



