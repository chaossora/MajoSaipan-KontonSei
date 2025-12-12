# model/game_config.py
from dataclasses import dataclass


@dataclass
class CollectConfig:
    """
    道具相关的玩法参数配置
    """
    poc_line_ratio: float = 0.25       # PoC 线高度占画面高度比例
    pickup_radius: float = 28.0        # 捡道具判定半径

    # 点收集线吸附配置
    poc_magnet_speed: float = 500.0    # PoC 吸附速度（原 magnet_speed）

    # 范围吸附配置（新增）
    attract_radius: float = 64.0       # 范围吸附触发半径
    attract_speed: float = 300.0       # 范围吸附速度

    power_step: float = 0.05           # 每个 Power 道具加多少火力
    power_score: int = 100             # 每个 Power 道具额外给多少分

    # 点数道具的高度区间得分
    # 底部附近 = point_score_min
    # 点收集线及以上 = point_score_max
    # 中间线性插值
    point_score_min: int = 1000
    point_score_max: int = 1500        # 1500 ≈ 1000 * 1.5，模仿 EoSD 线上 150k vs 线下 100k 的比例


@dataclass
class GrazeConfig:
    """
    擦弹相关的全局调参：
    - extra_radius: 擦弹圈比实际判定再多出来多少像素
    - score_per_graze: 每次擦弹加多少分
    """
    extra_radius: float = 24.0         # 自机判定外扩一圈
    score_per_graze: int = 500         # 对齐 EoSD，每次擦弹 +500 分


@dataclass
class GrazeEnergyConfig:
    """
    擦弹能量系统配置参数。
    能量满时自动激活增强状态，增强时能量持续消耗。
    """
    energy_per_graze: float = 5.0      # 每次擦弹获得的能量（20次擦弹充满）
    max_energy: float = 100.0          # 最大能量值

    # 增强状态时的能量消耗
    drain_rate: float = 20.0           # 增强时能量消耗速率（/秒），100/20=5秒

    # 能量衰减配置（非增强时）
    decay_delay: float = 2.0           # 停止擦弹后多久开始衰减
    decay_rate: float = 8.0            # 非增强时能量衰减速率（/秒）


@dataclass
class PlayerConfig:
    """玩家相关配置"""
    # 出生位置
    spawn_offset_y: float = 80.0           # 距底部的出生位置
    bullet_spawn_offset_y: float = 16.0    # 子弹出生点相对玩家的Y偏移

    # 移动速度
    speed_normal: float = 220.0            # 普通移动速度
    speed_focus: float = 120.0             # 低速（Focus）移动速度

    # 火力
    max_power: float = 4.0                 # 最大火力值


@dataclass
class BombConfig:
    """炸弹相关配置"""
    radius: float = 96.0                   # 炸弹场半径
    duration: float = 0.8                  # 炸弹持续时间
    invincible_time: float = 2.0           # 使用炸弹后的无敌时间


@dataclass
class BoundaryConfig:
    """边界系统配置"""
    out_buffer: float = 32.0               # 子弹出界缓冲区

