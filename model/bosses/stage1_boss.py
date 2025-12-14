# model/bosses/stage1_boss.py
"""
Stage 1 Boss: 小妖精头目

A simple boss with 3 phases:
- Phase 1 (Non-spell): 双螺旋环形弹幕
- Phase 2 (Spell Card): 星星形状弹幕
- Phase 3 (Spell Card): 螺旋追踪弹 + 环形弹幕组合

Requirements: 11.1, 11.2, 11.3, 11.4
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Generator

from model.actor import Actor
from model.boss_registry import boss_registry
from model.components import (
    Position, Velocity, Health, Collider, SpriteInfo,
    CollisionLayer, EnemyTag, EnemyKind, EnemyKindTag,
    BossState, BossHudData,
)
from model.scripting.task import TaskRunner
from model.scripting.patterns import fire_ring, fire_fan
from model.scripting.motion import MotionBuilder

if TYPE_CHECKING:
    from model.game_state import GameState
    from model.scripting.context import TaskContext


# ============ 弹幕工具函数 ============

def fire_pentagram(
    ctx: "TaskContext",
    cx: float,
    cy: float,
    radius: float,
    bullets_per_edge: int,
    move_speed: float,
    move_angle: float,
    hold_frames: int,
    scatter_speed: float,
    scatter_frames: int,
    archetype: str = "default",
    rotation: float = 0.0,
) -> None:
    """
    发射 {5/2} 五角星弹幕（pentagram）。
    
    五角星构造：在圆上取 5 个顶点，每隔一个点连线（0→2→4→1→3→0）。
    
    效果：
    1. 子弹直接在五角星轮廓位置生成
    2. 整个五角星向 move_angle 方向移动 hold_frames 帧
    3. 五条边各自向边的垂直方向（向外）散开
    
    Args:
        ctx: TaskContext
        cx, cy: 五角星中心位置
        radius: 外接圆半径
        bullets_per_edge: 每条边的子弹数
        move_speed: 整体移动速度
        move_angle: 整体移动方向（度）
        hold_frames: 保持形状移动的帧数
        scatter_speed: 散开时的速度
        scatter_frames: 散开加速的帧数
        archetype: 子弹原型
        rotation: 旋转角度（度），0 度时第一个顶点朝上
    """
    # 计算 5 个顶点位置（圆上均匀分布）
    vertices = []
    for k in range(5):
        angle_deg = rotation + k * 72 - 90  # -90 让第一个顶点朝上
        angle_rad = math.radians(angle_deg)
        vx = radius * math.cos(angle_rad)
        vy = radius * math.sin(angle_rad)
        vertices.append((vx, vy))
    
    # 五角星的边连接顺序：0→2→4→1→3→0
    edge_indices = [(0, 2), (2, 4), (4, 1), (1, 3), (3, 0)]
    
    for edge_idx, (start_idx, end_idx) in enumerate(edge_indices):
        start_vx, start_vy = vertices[start_idx]
        end_vx, end_vy = vertices[end_idx]
        
        # 计算边的方向向量
        edge_dx = end_vx - start_vx
        edge_dy = end_vy - start_vy
        
        # 计算边的中点（用于确定散开方向）
        mid_x = (start_vx + end_vx) / 2
        mid_y = (start_vy + end_vy) / 2
        
        # 散开方向：从中心指向边中点的方向（向外散开）
        scatter_angle = math.degrees(math.atan2(mid_y, mid_x))
        
        # 沿着边生成子弹
        for j in range(bullets_per_edge):
            t = j / max(bullets_per_edge - 1, 1)
            # 子弹在边上的相对位置
            rel_x = start_vx + t * edge_dx
            rel_y = start_vy + t * edge_dy
            
            # 子弹的绝对位置
            bullet_x = cx + rel_x
            bullet_y = cy + rel_y
            
            # 创建运动程序：
            # 1. 向 move_angle 方向移动（保持星星形状）
            # 2. 转向散开方向并加速
            motion = (MotionBuilder(speed=move_speed, angle=move_angle)
                .wait(hold_frames)  # 保持形状移动
                .set_angle(scatter_angle)  # 转向散开方向
                .accelerate_to(scatter_speed, scatter_frames)  # 加速散开
                .build())
            
            ctx.fire(bullet_x, bullet_y, move_speed, move_angle, archetype, motion=motion)


def fire_pentagram_radial(
    ctx: "TaskContext",
    cx: float,
    cy: float,
    radius: float,
    bullets_per_edge: int,
    expand_speed: float,
    hold_frames: int,
    scatter_speed: float,
    scatter_frames: int,
    archetype: str = "default",
    rotation: float = 0.0,
) -> None:
    """
    发射从中心向外扩散的 {5/2} 五角星弹幕。
    
    效果：
    1. 子弹从中心出发，向外扩散形成五角星
    2. 到达轮廓位置后保持形状继续向外移动
    3. 五条边各自向边的垂直方向散开
    
    Args:
        ctx: TaskContext
        cx, cy: 中心位置
        radius: 外接圆半径
        bullets_per_edge: 每条边的子弹数
        expand_speed: 扩散速度
        hold_frames: 保持形状的帧数
        scatter_speed: 散开时的速度
        scatter_frames: 散开加速的帧数
        archetype: 子弹原型
        rotation: 旋转角度（度）
    """
    # 计算 5 个顶点位置
    vertices = []
    for k in range(5):
        angle_deg = rotation + k * 72 - 90
        angle_rad = math.radians(angle_deg)
        vx = radius * math.cos(angle_rad)
        vy = radius * math.sin(angle_rad)
        vertices.append((vx, vy))
    
    # 五角星的边连接顺序
    edge_indices = [(0, 2), (2, 4), (4, 1), (1, 3), (3, 0)]
    
    for start_idx, end_idx in edge_indices:
        start_vx, start_vy = vertices[start_idx]
        end_vx, end_vy = vertices[end_idx]
        
        edge_dx = end_vx - start_vx
        edge_dy = end_vy - start_vy
        
        mid_x = (start_vx + end_vx) / 2
        mid_y = (start_vy + end_vy) / 2
        scatter_angle = math.degrees(math.atan2(mid_y, mid_x))
        
        for j in range(bullets_per_edge):
            t = j / max(bullets_per_edge - 1, 1)
            rel_x = start_vx + t * edge_dx
            rel_y = start_vy + t * edge_dy
            
            # 从中心到这个点的方向
            dist = math.sqrt(rel_x * rel_x + rel_y * rel_y)
            angle_to_point = math.degrees(math.atan2(rel_y, rel_x))
            
            # 到达轮廓位置需要的帧数
            travel_frames = int(dist / expand_speed * 60) if expand_speed > 0 else 30
            
            # 运动程序：扩散 → 保持 → 散开
            motion = (MotionBuilder(speed=expand_speed, angle=angle_to_point)
                .wait(travel_frames)  # 到达轮廓
                .wait(hold_frames)    # 保持形状
                .set_angle(scatter_angle)
                .accelerate_to(scatter_speed, scatter_frames)
                .build())
            
            ctx.fire(cx, cy, expand_speed, angle_to_point, archetype, motion=motion)


# ============ 高级弹幕工具函数 ============

def fire_rose_curve(
    ctx: "TaskContext",
    cx: float,
    cy: float,
    petals: int,
    radius: float,
    bullet_count: int,
    speed: float,
    archetype: str = "bullet_small",
    rotation: float = 0.0,
    expand_first: bool = True,
    hold_frames: int = 40,
) -> None:
    """
    发射玫瑰曲线弹幕 (Rose Curve / Rhodonea)
    
    玫瑰曲线方程: r = radius * cos(petals * theta)
    当 petals 为奇数时有 petals 个花瓣，偶数时有 2*petals 个花瓣
    """
    for i in range(bullet_count):
        theta = (2 * math.pi * i / bullet_count) + math.radians(rotation)
        r = radius * abs(math.cos(petals * theta))
        
        # 玫瑰曲线上的点
        rel_x = r * math.cos(theta)
        rel_y = r * math.sin(theta)
        
        # 从中心向外的方向
        angle_out = math.degrees(math.atan2(rel_y, rel_x))
        dist = math.sqrt(rel_x * rel_x + rel_y * rel_y)
        
        if expand_first and dist > 0:
            # 从中心扩散到玫瑰曲线位置，然后继续向外
            travel_frames = int(dist / speed * 60) if speed > 0 else 30
            motion = (MotionBuilder(speed=speed, angle=angle_out)
                .wait(travel_frames)
                .wait(hold_frames)
                .accelerate_to(speed * 1.5, 20)
                .build())
            ctx.fire(cx, cy, speed, angle_out, archetype, motion=motion)
        else:
            # 直接在位置生成，向外飞
            ctx.fire(cx + rel_x, cy + rel_y, speed, angle_out, archetype)


def fire_spiral_galaxy(
    ctx: "TaskContext",
    cx: float,
    cy: float,
    arms: int,
    bullets_per_arm: int,
    base_radius: float,
    spiral_tightness: float,
    speed: float,
    archetype: str = "bullet_small",
    rotation: float = 0.0,
    clockwise: bool = True,
) -> None:
    """
    发射螺旋星系弹幕
    
    多条螺旋臂从中心向外延伸，像银河系一样
    """
    direction = 1 if clockwise else -1
    
    for arm in range(arms):
        arm_base_angle = rotation + arm * (360 / arms)
        
        for i in range(bullets_per_arm):
            t = i / max(bullets_per_arm - 1, 1)
            # 螺旋方程：r 随角度增加而增加
            r = base_radius * (0.2 + t * 0.8)
            theta = math.radians(arm_base_angle + direction * t * spiral_tightness)
            
            rel_x = r * math.cos(theta)
            rel_y = r * math.sin(theta)
            
            # 切线方向（沿螺旋运动）
            tangent_angle = math.degrees(theta) + 90 * direction
            
            # 延迟发射，形成波浪效果
            delay = int(i * 2)
            
            motion = (MotionBuilder(speed=0, angle=tangent_angle)
                .wait(delay)
                .set_speed(speed * (0.5 + t * 0.5))
                .wait(30)
                .turn_to(tangent_angle + direction * 45, 40)
                .build())
            
            ctx.fire(cx + rel_x, cy + rel_y, 0, tangent_angle, archetype, motion=motion)


def fire_butterfly(
    ctx: "TaskContext",
    cx: float,
    cy: float,
    bullet_count: int,
    scale: float,
    speed: float,
    archetype: str = "bullet_small",
    rotation: float = 0.0,
) -> None:
    """
    发射蝴蝶曲线弹幕
    
    蝴蝶曲线是一种美丽的极坐标曲线
    r = e^sin(θ) - 2*cos(4θ) + sin^5((2θ-π)/24)
    """
    for i in range(bullet_count):
        theta = (2 * math.pi * i / bullet_count) + math.radians(rotation)
        
        # 简化的蝴蝶曲线
        r = scale * (math.exp(math.sin(theta)) - 2 * math.cos(4 * theta) + 
                     math.sin((2 * theta - math.pi) / 24) ** 5)
        r = abs(r) * 0.3  # 缩放
        
        rel_x = r * math.cos(theta)
        rel_y = r * math.sin(theta)
        
        angle_out = math.degrees(math.atan2(rel_y, rel_x))
        
        ctx.fire(cx + rel_x, cy + rel_y, speed, angle_out, archetype)


# ============ Boss Phase Tasks ============

def _draw_ten_pentagrams(
    ctx: "TaskContext",
    cx: float,
    cy: float,
    star_radius: float,
    orbit_radius: float,
    bullets_per_edge: int,
    draw_interval: int,
    hold_frames: int,
    scatter_speed: float,
    fly_frames: int,
    hover_frames: int,
    edge_scatter_speed: float,
    archetype: str = "bullet_small",
    base_rotation: float = 0.0,
) -> Generator[int, None, None]:
    """
    同时画出10个五角星，向外散开飞行，悬停，然后每条边各自散开。
    
    Args:
        ctx: TaskContext
        cx, cy: Boss中心位置
        star_radius: 每个五角星的半径
        orbit_radius: 10个五角星分布的轨道半径（以boss为圆心）
        bullets_per_edge: 每条边的子弹数
        draw_interval: 每颗子弹之间的间隔帧数
        hold_frames: 画完后保持形状的帧数
        scatter_speed: 整体散开时的速度
        fly_frames: 整体散开飞行的帧数
        hover_frames: 第二次悬停的帧数
        edge_scatter_speed: 每条边散开的速度
        archetype: 子弹原型
        base_rotation: 整体旋转角度
    """
    num_stars = 10
    total_bullets_per_star = 5 * bullets_per_edge
    frame_gap = draw_interval + 1  # yield N 的实际帧间隔是 N+1
    
    # 预计算所有五角星的顶点
    star_centers = []
    star_vertices_list = []  # 每个星星的5个顶点
    star_scatter_angles = []  # 每个星星的整体散开方向
    
    for s in range(num_stars):
        # 星星中心位置（在轨道上均匀分布）
        orbit_angle_deg = base_rotation + s * (360 / num_stars)
        orbit_angle_rad = math.radians(orbit_angle_deg)
        star_cx = cx + orbit_radius * math.cos(orbit_angle_rad)
        star_cy = cy + orbit_radius * math.sin(orbit_angle_rad)
        star_centers.append((star_cx, star_cy))
        
        # 整体散开方向：从boss中心指向星星中心
        star_scatter_angles.append(orbit_angle_deg)
        
        # 计算这个星星的5个顶点（相对于星星中心）
        vertices = []
        for k in range(5):
            angle_deg = k * 72 - 90  # -90让第一个顶点朝上
            angle_rad = math.radians(angle_deg)
            vx = star_radius * math.cos(angle_rad)
            vy = star_radius * math.sin(angle_rad)
            vertices.append((vx, vy))
        star_vertices_list.append(vertices)
    
    # 五角星的边连接顺序：0→2→4→1→3→0
    edge_indices = [(0, 2), (2, 4), (4, 1), (1, 3), (3, 0)]
    
    # 逐颗画子弹（所有星星同时画）
    bullet_idx = 0
    for edge_idx, (start_idx, end_idx) in enumerate(edge_indices):
        for j in range(bullets_per_edge):
            t = j / max(bullets_per_edge - 1, 1)
            
            # 为所有10个星星的这一颗子弹创建
            for s in range(num_stars):
                star_cx, star_cy = star_centers[s]
                vertices = star_vertices_list[s]
                star_angle = star_scatter_angles[s]
                
                start_vx, start_vy = vertices[start_idx]
                end_vx, end_vy = vertices[end_idx]
                edge_dx = end_vx - start_vx
                edge_dy = end_vy - start_vy
                
                # 子弹在边上的相对位置
                rel_x = start_vx + t * edge_dx
                rel_y = start_vy + t * edge_dy
                
                # 子弹的绝对位置
                bullet_x = star_cx + rel_x
                bullet_y = star_cy + rel_y
                
                # 计算边的散开方向：从五角星中心指向边中点
                mid_x = (start_vx + end_vx) / 2
                mid_y = (start_vy + end_vy) / 2
                base_edge_angle = math.degrees(math.atan2(mid_y, mid_x))
                
                # 引入梯度：角度和速度根据子弹在边上的位置(t)变化
                # 角度梯度：从-25度到+25度的扇形展开
                angle_spread = 50  # 总角度范围
                edge_scatter_angle = base_edge_angle + (t - 0.5) * angle_spread
                
                # 速度梯度：从0.7x到1.3x的速度变化，形成倾斜弹幕墙
                speed_factor = 0.7 + t * 0.6  # t=0时0.7倍，t=1时1.3倍
                final_edge_speed = edge_scatter_speed * speed_factor
                
                # 同步等待：早期子弹等待更久
                wait_for_sync = (total_bullets_per_star - 1 - bullet_idx) * frame_gap + 1
                
                # 平滑运动参数计算
                # 目标：保持总飞行距离近似不变，但加入加减速过程
                accel_frames = 20
                decel_frames = 20
                
                # 原飞行距离 ≈ speed * fly_frames
                # 新飞行距离 = 0.5 * speed * accel + speed * cruise + 0.5 * speed * decel
                # cruise = fly - 0.5*(accel + decel)
                cruise_frames = int(fly_frames - 0.5 * (accel_frames + decel_frames))
                if cruise_frames < 0:
                    # 如果预设飞行时间太短，缩短加减速时间
                    cruise_frames = 0
                    accel_frames = fly_frames // 2
                    decel_frames = fly_frames - accel_frames

                # 运动程序：
                # 1. 等待画完 → 2. 保持形状 → 3. 整体向外散开飞行 (平滑加减速)
                # → 4. 悬停 → 5. 每条边各自散开（带角度和速度梯度，平滑加速）
                motion = (MotionBuilder(speed=0, angle=star_angle)
                    .wait(wait_for_sync)      # 等待所有子弹画完
                    .wait(hold_frames)        # 保持形状
                    
                    # 平滑加速散开
                    .accelerate_to(scatter_speed, accel_frames) 
                    .wait(cruise_frames)      # 巡航飞行
                    # 平滑减速悬停
                    .accelerate_to(0, decel_frames)             
                    
                    .wait(hover_frames)       # 悬停时间
                    .set_angle(edge_scatter_angle)  # 转向边的散开方向（带角度梯度）
                    
                    # 平滑加速边缘散开
                    .accelerate_to(final_edge_speed, 20)    # 每条边散开（带速度梯度）
                    .build())
                
                ctx.fire(bullet_x, bullet_y, 0, star_angle, archetype, motion=motion)
            
            bullet_idx += 1
            
            # 逐颗画：每颗子弹之间间隔
            if bullet_idx < total_bullets_per_star:
                yield draw_interval


def phase1_nonspell(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    Phase 1: 非符 - 「十星绽放」
    
    Boss入场后，以自己为圆心画出10个五角星：
    - 10个五角星同时画出（有画星星的过程）
    - 画完后向四周散开
    - 循环发射
    """
    wave = 0
    
    while True:
        x, y = ctx.owner_pos()
        
        # 画出10个五角星并散开
        yield from _draw_ten_pentagrams(
            ctx, x, y,
            star_radius=80,           # 每个五角星的大小
            orbit_radius=60,          # 星星分布的轨道半径
            bullets_per_edge=10,       # 每条边10颗子弹
            draw_interval=2,          # 每颗子弹间隔2帧
            hold_frames=40,           # 画完后保持40帧
            scatter_speed=160,         # 整体散开速度
            fly_frames=40,            # 整体飞行40帧
            hover_frames=30,          # 第二次悬停30帧
            edge_scatter_speed=100,   # 每条边散开速度
            archetype="bullet_small",
            base_rotation=wave * 18,  # 每波旋转18度
        )
        
        wave += 1
        yield 60  # 波次间隔


def phase2_spellcard(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    Phase 2: 奇迹「摩西开海」
    
    左右两边的波浪屏障由长度不同的直激光拼成：
    - 激光源分布在屏幕左右边缘，向中间发射。
    - 激光长度随时间波动，形成波浪形的通道。
    - 激光从屏幕底部升起入场。
    - 中间有密集的米粒弹幕流。
    """
    from model.components import LaserState, Position

    screen_w = ctx.state.width
    screen_h = ctx.state.height
    center_x = screen_w / 2
    
    # 1. Boss移动到上方中央
    yield from ctx.move_to(center_x, 80, frames=60)
    
    # 2. 创建激光墙（初始在屏幕左右两侧外）
    lasers_left = []
    lasers_right = []
    
    num_lasers = 40  # 增加激光数量，使屏障更密集
    step_y = screen_h / num_lasers
    
    # 初始偏移，让激光在屏幕外
    # 左侧激光：初始 X = -entry_offset_x
    # 右侧激光：初始 X = screen_w + entry_offset_x
    entry_offset_x = 200.0
    
    # 初始化激光
    for i in range(num_lasers):
        y_pos = i * step_y + 10
        
        # 左侧激光（从左边缘向右发射）
        l1 = ctx.fire_laser(
            x=-entry_offset_x,
            y=y_pos,
            angle=0,  # 向右
            length=100, # 初始长度
            width=12.0,
            laser_type="straight", 
            warmup_frames=0, # 无预热
            duration_frames=6000, # 持续很久
            can_reflect=False
        )
        lasers_left.append((l1, y_pos))
        
        # 右侧激光（从右边缘向左发射）
        l2 = ctx.fire_laser(
            x=screen_w + entry_offset_x,
            y=y_pos,
            angle=180, # 向左
            length=100,
            width=12.0,
            laser_type="straight",
            warmup_frames=0, # 无预热
            duration_frames=6000,
            can_reflect=False
        )
        lasers_right.append((l2, y_pos))

    # 不需要等待预热了，直接开始进场和波动
    
    try:
        # 3. 循环更新激光长度、位置并发射弹幕
        time_counter = 0
        
        # 入场动画状态
        current_entry_offset = entry_offset_x
        entry_speed = 3.0 # 水平滑入速度
        
        # 活跃的蓝色弹幕流列表
        # 每个元素: {'x': float, 'y': float, 'angle': float, 'remaining': int, 'interval': int, 'timer': int}
        active_blue_streams = []
        
        while True:
            # 更新入场偏移（逐渐减小到0）
            if current_entry_offset > 0:
                current_entry_offset -= entry_speed
                if current_entry_offset < 0:
                    current_entry_offset = 0
            
            # 波浪参数
            base_channel_width = 160
            amplitude = 40.0
            t_speed = 0.05
            y_freq = 0.02
            
            # 更新左侧激光
            for laser, base_y in lasers_left:
                pos = laser.get(Position)
                ls = laser.get(LaserState)
                if ls and pos:
                    # 更新位置（从左侧滑入）
                    # 目标 X = 0, 当前 X = -current_entry_offset
                    pos.x = -current_entry_offset
                    
                    # 波浪偏移
                    offset = math.sin(time_counter * t_speed + base_y * y_freq) * amplitude
                    
                    # 目标长度 = 固定基准长度 + 波浪
                    # 基准长度是从屏幕左缘(0)到通道左缘(center_x - base_channel_width/2)的距离
                    base_len = (center_x - base_channel_width / 2)
                    ls.length = max(10.0, base_len + offset)
            
            # 更新右侧激光
            for laser, base_y in lasers_right:
                pos = laser.get(Position)
                ls = laser.get(LaserState)
                if ls and pos:
                    # 更新位置（从右侧滑入）
                    # 目标 X = screen_w, 当前 X = screen_w + current_entry_offset
                    pos.x = screen_w + current_entry_offset
                    
                    # 右侧波浪偏移
                    offset = math.sin(time_counter * t_speed + base_y * y_freq) * amplitude
                    
                    # 目标长度 = 固定基准长度 + 波浪
                    # 基准长度是从通道右缘到屏幕右缘的距离
                    # 即 screen_w - (center_x + base_channel_width/2)
                    base_len = screen_w - (center_x + base_channel_width / 2)
                    # 注意：对于向左发射的激光，长度也是正值
                    ls.length = max(10.0, base_len - offset)  # 右侧波浪方向相反以匹配视觉？
                    # 之前的逻辑：target_endpoint_x = (center_x + base_channel_width / 2 + offset)
                    # length = pos.x - target_endpoint_x
                    # pos.x = screen_w (at end)
                    # length = screen_w - (center + width/2 + offset) = (screen_w - center - width/2) - offset
                    # 所以是 base_len - offset
            
            # 处理活跃的蓝色弹幕流
            for stream in active_blue_streams[:]:
                stream['timer'] -= 1
                if stream['timer'] <= 0:
                    # 发射子弹
                    ctx.fire(stream['x'], stream['y'], 250, stream['angle'], "bullet_small")
                    stream['remaining'] -= 1
                    stream['timer'] = stream['interval']
                    
                    if stream['remaining'] <= 0:
                        active_blue_streams.remove(stream)

            # 发射弹幕（仅当滑入一部分后开始）
            if current_entry_offset < 50:
                # 1. 蓝色竖直扇形弹幕 (3条直线流)
                # 每 90 帧发射一波
                if time_counter % 90 == 0:
                    # 在通道范围内随机选1个发射中心点
                    safe_width = 140
                    fire_y = 100 
                    
                    center_fire_x = center_x + ctx.random_range(-safe_width/2, safe_width/2)
                    
                    # 定义3条流的角度，从同一点发射，形成扇形
                    # 角度：80, 90, 100
                    streams_config = [
                        {'angle': 75}, 
                        {'angle': 90},
                        {'angle': 105},
                    ]
                    
                    for cfg in streams_config:
                        active_blue_streams.append({
                            'x': center_fire_x, # 相同起点
                            'y': fire_y,
                            'angle': cfg['angle'],
                            'remaining': 15,     # 增加连射数量
                            'interval': 3,       # 提高射速
                            'timer': 0
                        })

                # 2. 红色自机狙流
                # 每 120 帧发射一轮
                aim_interval = 120
                aim_duration = 30 # 持续发射30帧
                aim_cycle = time_counter % aim_interval
                
                if aim_cycle < aim_duration and aim_cycle % 3 == 0:
                    bx, by = ctx.owner_pos()
                    speed = 250
                    ctx.fire_aimed(bx, by, speed, "bullet_medium")
            
            time_counter += 1
            yield 1
    finally:
        # 符卡结束或中断时，清理所有激光
        for laser, _ in lasers_left:
            ctx.state.remove_actor(laser)
        for laser, _ in lasers_right:
            ctx.state.remove_actor(laser)


def _draw_meteor_star(
    ctx: "TaskContext",
    start_x: float,
    start_y: float,
    radius: float,
    rotation: float,
    meteor_angle: float,
) -> Generator[int, None, None]:
    """
    辅助函数：一颗一颗画出流星五角星
    
    时序分析：
    - yield N → 等待 N+1 帧后执行下一步（frame_gap = N+1）
    - WAIT(M) → M 次 tick 后完成
    - 子弹创建的同一帧就会被 motion_program_system tick
    
    同步策略：
    - bullet_i 在 frame i*frame_gap 创建
    - 创建帧就被 tick，所以实际等待 = WAIT值
    - 所有子弹应在 frame (total-1)*frame_gap 同时开始移动
    - bullet_i 需要 WAIT((total-1-i)*frame_gap)
    """
    bullets_per_edge = 5
    draw_interval = 2  # yield 的值
    move_speed = 90  # 移动速度
    hold_frames = 120  # 保持形状移动的帧数
    
    # yield N 的实际帧间隔是 N+1
    frame_gap = draw_interval + 1
    
    vertices = []
    for k in range(5):
        angle_deg = rotation + k * 72 - 90
        a_rad = math.radians(angle_deg)
        vx = radius * math.cos(a_rad)
        vy = radius * math.sin(a_rad)
        vertices.append((vx, vy))
    
    edge_indices = [(0, 2), (2, 4), (4, 1), (1, 3), (3, 0)]
    total_bullets = 5 * bullets_per_edge
    
    # 最后一颗子弹（bullet_24）在 frame 24*3=72 创建
    # 它只需要 WAIT(1)（至少1，因为WAIT(0)会立即完成但仍消耗1帧）
    # bullet_i 需要等待 (24-i)*frame_gap + 1 帧
    # 这样所有子弹在 frame 72 + 1 = 73 同时开始移动
    
    bullet_idx = 0
    for start_idx, end_idx in edge_indices:
        start_vx, start_vy = vertices[start_idx]
        end_vx, end_vy = vertices[end_idx]
        edge_dx = end_vx - start_vx
        edge_dy = end_vy - start_vy
        
        mid_x = (start_vx + end_vx) / 2
        mid_y = (start_vy + end_vy) / 2
        base_scatter_angle = math.degrees(math.atan2(mid_y, mid_x))
        
        for j in range(bullets_per_edge):
            t = j / max(bullets_per_edge - 1, 1)
            rel_x = start_vx + t * edge_dx
            rel_y = start_vy + t * edge_dy
            
            # 子弹在固定的五角星位置生成
            bullet_x = start_x + rel_x
            bullet_y = start_y + rel_y
            
            arc_spread = 55
            final_angle = base_scatter_angle + (t - 0.5) * arc_spread
            turn_duration = 25 + int(abs(t - 0.5) * 35)
            
            # 同步等待：早期子弹等待更久，所有子弹同时开始移动
            # bullet_i 在 frame i*frame_gap 创建
            # 所有子弹应在最后一颗创建后开始移动
            # wait = (total_bullets - 1 - bullet_idx) * frame_gap + 1
            wait_for_sync = (total_bullets - 1 - bullet_idx) * frame_gap + 1
            
            motion = (MotionBuilder(speed=0, angle=meteor_angle)
                .wait(wait_for_sync)  # 等待所有子弹画完
                .set_speed(move_speed)  # 同时开始移动
                .wait(hold_frames)  # 保持形状移动
                .turn_to(final_angle, turn_duration)
                .accelerate_to(120, 25)
                .build())
            
            ctx.fire(bullet_x, bullet_y, 0, meteor_angle, "bullet_small", motion=motion)
            bullet_idx += 1
            


def phase3_spellcard(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    Phase 3: 符卡「星辰万象」
    
    终极弹幕 - 多种图案的华丽组合：
    1. 蝴蝶曲线弹幕从中心绽放
    2. 双层反向旋转的玫瑰曲线
    3. 五角星追踪弹
    4. 螺旋臂扫射
    """
    rotation = 0.0
    wave = 0
    
    while True:
        x, y = ctx.owner_pos()
        
        # 主弹幕：根据波次切换不同图案
        pattern = wave % 5
        
        if pattern == 0:
            # 蝴蝶曲线绽放
            fire_butterfly(
                ctx, x, y,
                bullet_count=48,
                scale=50,
                speed=55,
                archetype="bullet_small",
                rotation=rotation,
            )
            # 内圈小玫瑰
            fire_rose_curve(
                ctx, x, y,
                petals=4,
                radius=40,
                bullet_count=16,
                speed=70,
                archetype="bullet_medium",
                rotation=-rotation,
                expand_first=False,
                hold_frames=0,
            )
            
        elif pattern == 1:
            # 双层反向玫瑰
            fire_rose_curve(
                ctx, x, y,
                petals=5,
                radius=70,
                bullet_count=35,
                speed=60,
                archetype="bullet_small",
                rotation=rotation,
                expand_first=True,
                hold_frames=30,
            )
            fire_rose_curve(
                ctx, x, y,
                petals=3,
                radius=50,
                bullet_count=21,
                speed=75,
                archetype="bullet_medium",
                rotation=-rotation + 60,
                expand_first=True,
                hold_frames=20,
            )
            
        elif pattern == 2:
            # 螺旋星系 + 追踪弹
            fire_spiral_galaxy(
                ctx, x, y,
                arms=5,
                bullets_per_arm=10,
                base_radius=70,
                spiral_tightness=200,
                speed=55,
                archetype="bullet_small",
                rotation=rotation,
                clockwise=True,
            )
            # 追踪弹
            for i in range(5):
                angle = rotation + i * 72 + 36
                motion = (MotionBuilder(speed=30, angle=angle)
                    .wait(40)
                    .aim_player()
                    .accelerate_to(150, 25)
                    .build())
                ctx.fire(x, y, 30, angle, "bullet_large", motion=motion)
                
        elif pattern == 3:
            # 扩散五角星 + 环形弹幕
            fire_pentagram_radial(
                ctx, x, y,
                radius=65,
                bullets_per_edge=7,
                expand_speed=70,
                hold_frames=25,
                scatter_speed=110,
                scatter_frames=20,
                archetype="bullet_small",
                rotation=rotation,
            )
            # 双层环形
            fire_ring(ctx, x, y, count=12, speed=85, archetype="bullet_medium", 
                     start_angle=rotation)
            fire_ring(ctx, x, y, count=12, speed=65, archetype="bullet_small", 
                     start_angle=-rotation + 15)
                     
        else:  # pattern == 4
            # 全屏花火 - 多个小玫瑰同时绽放
            offsets = [(0, 0), (-60, -30), (60, -30), (-40, 40), (40, 40)]
            for ox, oy in offsets:
                fire_rose_curve(
                    ctx, x + ox, y + oy,
                    petals=3,
                    radius=35,
                    bullet_count=15,
                    speed=50 + abs(ox) * 0.3,
                    archetype="bullet_small" if ox == 0 else "bullet_medium",
                    rotation=rotation + ox,
                    expand_first=True,
                    hold_frames=20,
                )
        
        rotation += 13
        wave += 1
        yield 50


# ============ Boss 主脚本（纯脚本驱动） ============

def stage1_boss_script(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    Stage 1 Boss 完整脚本（纯脚本驱动模式）。
    
    控制 Boss 的整个战斗流程：
    - 入场动画
    - Phase 1: 非符「万华镜」
    - Phase 2: 符卡「银河涡流」
    - Phase 3: 符卡「星辰万象」
    - 结束处理
    """
    # 入场：移动到战斗位置
    ctx.update_boss_hud(phases_remaining=3, timer=30.0)
    yield from ctx.move_to(ctx.state.width / 2, 120, frames=180)
    
    # 移动参数（匹配原 BossMovementState）
    # idle_time: 1.5-2.5s = 90-150 帧
    # move_duration: 0.5-0.8s = 30-48 帧
    # y 范围: y_center=110, y_variation=30 → 80-140
    move_params = dict(
        move_interval=(90, 150),
        move_duration=(30, 48),
        move_range_x=60.0,
        move_range_y=(80.0, 140.0),
    )
    
    # === Phase 1: 非符「万华镜」 ===
    ctx.update_boss_hud(phases_remaining=3)
    yield from ctx.run_phase(
        pattern=phase1_nonspell,
        timeout_seconds=30.0,
        hp=800,
        **move_params,
    )
    
    # 阶段转换
    yield from ctx.phase_transition(frames=60)
    yield from ctx.move_to(ctx.state.width / 2, 100, frames=30)
    
    # === Phase 2: 奇迹「摩西开海」 ===
    ctx.update_boss_hud(phases_remaining=2)
    yield from ctx.run_spell_card(
        name="奇迹「摩西开海」",
        bonus=100000,
        pattern=phase2_spellcard,
        timeout_seconds=45.0,
        hp=1000,
        **move_params,
    )
    
    # 阶段转换
    yield from ctx.phase_transition(frames=60)
    yield from ctx.move_to(ctx.state.width / 2, 100, frames=30)
    
    # === Phase 3: 符卡「星辰万象」 ===
    ctx.update_boss_hud(phases_remaining=1)
    yield from ctx.run_spell_card(
        name="幻符「星辰万象」",
        bonus=150000,
        pattern=phase3_spellcard,
        timeout_seconds=60.0,
        hp=1200,
        **move_params,
    )
    
    # Boss 战结束
    ctx.kill_boss()


# ============ Boss Factory ============

@boss_registry.register("stage1_boss")
def spawn_stage1_boss(state: "GameState", x: float, y: float) -> Actor:
    """
    Spawn the Stage 1 Boss（纯脚本驱动模式）。
    
    创建 Boss Actor 并启动主脚本。
    所有阶段逻辑由 stage1_boss_script 控制。
    
    Args:
        state: GameState to spawn the boss in
        x: X position
        y: Y position
    
    Returns:
        The created Boss Actor
    """
    from pygame.math import Vector2
    from random import Random
    from model.scripting.context import TaskContext
    
    boss = Actor()
    
    # Position and velocity
    boss.add(Position(x, y))
    boss.add(Velocity(Vector2(0, 0)))
    
    # Tags
    boss.add(EnemyTag())
    boss.add(EnemyKindTag(EnemyKind.BOSS))
    
    # Sprite
    boss.add(SpriteInfo(name="ema"))  # 使用现有的 ema 精灵
    
    # Collision
    boss.add(Collider(
        radius=24.0,
        layer=CollisionLayer.ENEMY,
        mask=CollisionLayer.PLAYER_BULLET,
    ))
    
    # Boss state（简化版，无阶段列表）
    boss.add(BossState(
        boss_name="小妖精头目",
        drop_power=16,
        drop_point=24,
    ))
    
    # Initial health（由脚本在每个阶段开始时设置）
    boss.add(Health(max_hp=800, hp=800))
    
    # HUD data
    boss.add(BossHudData(
        boss_name="小妖精头目",
        phases_remaining=3,
        visible=True,
    ))
    
    # TaskRunner for boss script
    runner = TaskRunner()
    boss.add(runner)
    
    # Add to game state
    state.add_actor(boss)
    
    # 创建上下文并启动 Boss 主脚本
    ctx = TaskContext(
        state=state,
        owner=boss,
        rng=Random(42),  # 确定性 RNG
    )
    runner.start_task(stage1_boss_script, ctx)
    
    return boss
