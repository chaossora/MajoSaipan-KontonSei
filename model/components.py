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
    damage: int = 9999  # 每帧伤害（对普通敌人相当于秒杀）


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


# ====== Boss 组件 ======

class PhaseType(Enum):
    """Boss 阶段类型"""
    NON_SPELL = auto()    # 非符卡（通常弹幕）
    SPELL_CARD = auto()   # 符卡（有名称、奖励）
    SURVIVAL = auto()     # 生存符卡（Boss 无敌，玩家需存活）


@dataclass
class BossPhase:
    """
    单个 Boss 阶段定义（纯数据）。
    存储在 BossState.phases 列表中。
    """
    phase_type: PhaseType
    hp: int                                # 该阶段血量
    duration: float                        # 该阶段时限（秒）
    spell_name: str = ""                   # 符卡名（非符为空）
    spell_bonus: int = 0                   # 符卡奖励分数
    damage_multiplier: float = 1.0         # 伤害倍率（<1 表示减伤）
    pattern: object = None                 # BulletPatternConfig（延迟绑定）


@dataclass
class BossState:
    """
    Boss 核心状态组件（运行时状态）：
    - 存储所有阶段定义
    - 跟踪当前阶段和计时器
    - HP 由现有 Health 组件管理
    """
    boss_name: str
    phases: List[BossPhase] = field(default_factory=list)
    current_phase_index: int = 0
    phase_timer: float = 0.0               # 当前阶段剩余时间
    phase_transitioning: bool = False      # 正在阶段转换
    transition_timer: float = 0.0

    # 掉落配置
    drop_power: int = 16
    drop_point: int = 24
    drop_life: int = 0
    drop_bomb: int = 0

    # Bomb 抗性配置（东方风格）
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
class BossMovementState:
    """
    Boss 移动控制组件。
    实现东方风格的间隔滑动移动（状态机模式）。
    """
    # 活动范围
    y_min: float = 50.0                    # Y 轴活动上限
    y_max: float = 180.0                   # Y 轴活动下限

    # 状态机
    is_moving: bool = False                # 是否正在滑动
    move_timer: float = 1.0                # 下次移动倒计时（初始 1 秒后开始移动）
    move_progress: float = 0.0             # 当前移动进度 (0-1)
    move_duration: float = 0.6             # 单次移动持续时间

    # 移动目标（运行时状态）
    start_x: float = 0.0
    start_y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0

    # 配置参数
    idle_time_min: float = 1.5             # 静止等待时间下限
    idle_time_max: float = 3.0             # 静止等待时间上限
    move_duration_min: float = 0.4         # 滑动时间下限
    move_duration_max: float = 0.8         # 滑动时间上限
    target_offset_range: float = 50.0      # X 目标随机偏移范围
    y_variation: float = 30.0              # Y 方向波动范围


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
