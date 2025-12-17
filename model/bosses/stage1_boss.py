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
    BossState, BossHudData, BossAttackAnimation,
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


# ============ 第五阶段专用弹幕函数 ============

def fire_triple_layer_fan(
    ctx: "TaskContext",
    x: float,
    y: float,
    base_angle: float,
    count: int = 7,
    spread: float = 60.0,
    fly_speeds: tuple = (120, 180, 240),
    final_speeds: tuple = (120, 180, 240),
    archetype: str = "boss_blue",
    fly_frames: int = 30,
    hover_frames: int = 180,
) -> None:
    """
    发射三层扇形弹幕（飞行成形 → 悬停 → 自机狙）。

    子弹发射后先以扇形飞出形成形状（三层速度不同形成厚度），
    然后悬停，最后转向玩家飞行。

    Args:
        ctx: TaskContext
        x, y: 发射位置
        base_angle: 扇形中心角度（度）
        count: 每层子弹数量
        spread: 扇形展开角度（度）
        fly_speeds: 三层飞行成形时的速度 (内层, 中层, 外层)
        final_speeds: 三层自机狙时的最终速度 (内层, 中层, 外层)
        archetype: 子弹原型
        fly_frames: 飞行成形的帧数（约0.5秒）
        hover_frames: 悬停帧数（约1秒）
    """
    from model.scripting.motion import MotionBuilder

    for layer_idx, (fly_speed, final_speed) in enumerate(zip(fly_speeds, final_speeds)):
        for i in range(count):
            if count > 1:
                angle = base_angle - spread / 2 + (spread * i / (count - 1))
            else:
                angle = base_angle

            # 构建运动程序：飞行成形 → 停止 → 悬停 → 自机狙 → 加速
            motion = (MotionBuilder(speed=fly_speed, angle=angle)
                .wait(fly_frames)                    # 飞行成形（三层速度不同，形成厚度）
                .set_speed(0)                        # 停下来
                .wait(hover_frames)                  # 悬停
                .aim_player()                        # 转向玩家
                .accelerate_to(final_speed, 15)     # 平滑加速
                .build())

            ctx.fire(x, y, fly_speed, angle, archetype, motion=motion)


def draw_bouncing_pentagrams(
    ctx: "TaskContext",
    cx: float,
    cy: float,
    num_stars: int = 4,
    radius: float = 60.0,
    bullets_per_edge: int = 8,
    move_speed: float = 100.0,
    hold_frames: int = 60,
    scatter_speed: float = 120.0,
    scatter_frames: int = 30,
    archetype: str = "bullet_medium",
    max_bounces: int = 1,
    angle_spread: float = 50.0,
    draw_interval: int = 1,
) -> "Generator[int, None, None]":
    """
    一颗颗画出可反弹的五角星弹幕。

    在屏幕中心发射多个五角星，子弹碰到边界会反弹指定次数。
    边散开时有角度和速度梯度。

    Args:
        ctx: TaskContext
        cx, cy: 发射中心位置
        num_stars: 五角星数量
        radius: 每个五角星的半径
        bullets_per_edge: 每条边的子弹数
        move_speed: 整体移动速度
        hold_frames: 保持形状的帧数
        scatter_speed: 散开时的基础速度
        scatter_frames: 散开加速的帧数
        archetype: 子弹原型
        max_bounces: 最大反弹次数
        angle_spread: 角度梯度范围（度）
        draw_interval: 每颗子弹之间的间隔帧数
    """
    from model.components import BulletBounce

    # 预计算所有星星的顶点和边
    stars_data = []
    for star_idx in range(num_stars):
        move_angle = star_idx * (360.0 / num_stars)
        rotation = star_idx * (360.0 / num_stars / 2)

        vertices = []
        for k in range(5):
            angle_deg = rotation + k * 72 - 90
            angle_rad = math.radians(angle_deg)
            vx = radius * math.cos(angle_rad)
            vy = radius * math.sin(angle_rad)
            vertices.append((vx, vy))

        stars_data.append((vertices, move_angle))

    edge_indices = [(0, 2), (2, 4), (4, 1), (1, 3), (3, 0)]
    total_bullets_per_star = 5 * bullets_per_edge
    frame_gap = draw_interval + 1

    # 逐颗画子弹（所有星星同时画）
    bullet_idx = 0
    for edge_idx, (start_idx, end_idx) in enumerate(edge_indices):
        for j in range(bullets_per_edge):
            t = j / max(bullets_per_edge - 1, 1)

            # 为所有星星的这一颗子弹创建
            for vertices, move_angle in stars_data:
                start_vx, start_vy = vertices[start_idx]
                end_vx, end_vy = vertices[end_idx]
                edge_dx = end_vx - start_vx
                edge_dy = end_vy - start_vy

                rel_x = start_vx + t * edge_dx
                rel_y = start_vy + t * edge_dy
                bullet_x = cx + rel_x
                bullet_y = cy + rel_y

                mid_x = (start_vx + end_vx) / 2
                mid_y = (start_vy + end_vy) / 2
                base_scatter_angle = math.degrees(math.atan2(mid_y, mid_x))
                final_scatter_angle = base_scatter_angle + (t - 0.5) * angle_spread

                speed_factor = 0.7 + t * 0.6
                final_scatter_speed = scatter_speed * speed_factor

                # 同步等待：让后面的子弹等待更短时间
                wait_for_sync = (total_bullets_per_star - 1 - bullet_idx) * frame_gap + 1

                motion = (MotionBuilder(speed=0, angle=move_angle)
                    .wait(wait_for_sync)
                    .set_speed(move_speed)
                    .wait(hold_frames)
                    .set_angle(final_scatter_angle)
                    .accelerate_to(final_scatter_speed, scatter_frames)
                    .build())

                bullet = ctx.fire(bullet_x, bullet_y, 0, move_angle, archetype, motion=motion)
                bullet.add(BulletBounce(max_bounces=max_bounces, bounce_count=0))

            bullet_idx += 1
            if bullet_idx < total_bullets_per_star:
                yield draw_interval


def _fly_and_fire_phase5(
    ctx: "TaskContext",
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    fly_speed: float = 500.0,
    fire_interval: int = 8,
    fan_count: int = 7,
    fan_spread: float = 60.0,
    layer_speeds: tuple = (120, 180, 240),
) -> "Generator[int, None, None]":
    """
    Boss从起点飞到终点，飞行时发射随机方向的三层扇形弹幕。

    Args:
        ctx: TaskContext
        start_x, start_y: 起点位置
        end_x, end_y: 终点位置
        fly_speed: 飞行速度 (px/s)
        fire_interval: 发射间隔（帧）
        fan_count: 每层子弹数
        fan_spread: 扇形角度
        layer_speeds: 三层速度
    """
    from model.components import Position

    # 获取Boss位置组件
    pos = ctx.owner.get(Position)
    if pos is None:
        return

    # 瞬移到起点
    pos.x = start_x
    pos.y = start_y

    # 计算飞行参数
    dx = end_x - start_x
    dy = end_y - start_y
    distance = math.sqrt(dx * dx + dy * dy)

    # 计算飞行帧数（基于速度，60fps）
    fly_frames = max(1, int(distance / fly_speed * 60))

    step_x = dx / fly_frames
    step_y = dy / fly_frames

    fire_timer = 0

    for _ in range(fly_frames):
        # 更新位置
        pos.x += step_x
        pos.y += step_y

        # 发射弹幕
        fire_timer -= 1
        if fire_timer <= 0:
            # 随机方向
            random_angle = ctx.random_range(0, 360)
            fire_triple_layer_fan(
                ctx, pos.x, pos.y, random_angle,
                count=fan_count,
                spread=fan_spread,
                fly_speeds=layer_speeds,
                final_speeds=layer_speeds,
            )
            fire_timer = fire_interval

        yield 1

    # 确保到达终点
    pos.x = end_x
    pos.y = end_y


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

        # ★ 每波开始时触发攻击动画
        ctx.trigger_attack_animation(cooldown=1.0)

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
            archetype="boss_blue",
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
    
    num_lasers = 64  # 增加数量使波浪更平滑
    step_y = screen_h / num_lasers
    
    # 初始偏移，让激光在屏幕外
    # 左侧激光：初始 X = -entry_offset_x
    # 右侧激光：初始 X = screen_w + entry_offset_x
    entry_offset_x = 200.0
    
    # 初始化激光
    for i in range(num_lasers):
        y_pos = i * step_y + step_y / 2
        
        # 计算颜色梯度：深蓝 -> 青 -> 白 -> 青 -> 深蓝 (模拟水光泽)
        # t: 0 -> 1 -> 0
        t = math.sin((i / num_lasers) * math.pi)
        r = int(20 + 60 * t)
        g = int(50 + 150 * t)
        b = int(180 + 75 * t)
        wave_color = (min(255, r), min(255, g), min(255, b))

        # 左侧激光（从左边缘向右发射）
        l1 = ctx.fire_laser(
            x=-entry_offset_x,
            y=y_pos,
            angle=0,  # 向右
            length=100, # 初始长度
            width=15.0, # 增加宽度以确保重叠
            laser_type="straight", 
            warmup_frames=0, # 无预热
            duration_frames=6000, # 持续很久
            can_reflect=False,
            color=wave_color
        )
        lasers_left.append((l1, y_pos))
        
        # 右侧激光（从右边缘向左发射）
        l2 = ctx.fire_laser(
            x=screen_w + entry_offset_x,
            y=y_pos,
            angle=180, # 向左
            length=100,
            width=15.0,
            laser_type="straight",
            warmup_frames=0, # 无预热
            duration_frames=6000,
            can_reflect=False,
            color=wave_color
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
                    ctx.fire(stream['x'], stream['y'], 250, stream['angle'], "boss_blue")
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

                # ★ 自机狙开始时触发攻击动画
                if aim_cycle == 0:
                    ctx.trigger_attack_animation(cooldown=2.0)

                if aim_cycle < aim_duration and aim_cycle % 3 == 0:
                    bx, by = ctx.owner_pos()
                    speed = 250
                    ctx.fire_aimed(bx, by, speed, "boss_red")
            
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
            


def _draw_double_ring_pentagrams(
    ctx: "TaskContext",
    cx: float,
    cy: float,
    # Large star params
    large_star_radius: float,
    large_orbit_radius: float,
    large_fly_frames: int,
    # Small star params
    small_star_radius: float,
    small_orbit_radius: float,
    small_fly_frames: int,
    # Common params
    bullets_per_edge: int,
    draw_interval: int,
    hold_frames: int,
    scatter_speed: float,
    hover_frames: int,
    edge_scatter_speed: float,
    archetype_large: str = "bullet_medium",
    archetype_small: str = "bullet_small",
    base_rotation: float = 0.0,
) -> Generator[int, None, None]:
    """
    Phase 3 专用：双环五角星
    外圈10个大五角星，内圈10个小五角星（交错），一起飞出但距离不同。
    """
    num_stars_per_ring = 10
    total_bullets_per_star = 5 * bullets_per_edge
    frame_gap = draw_interval + 1
    
    # 预计算所有五角星参数
    stars_data = []
    
    for s in range(num_stars_per_ring):
        # --- 大星星 (外圈) ---
        angle_deg = base_rotation + s * (360 / num_stars_per_ring)
        angle_rad = math.radians(angle_deg)
        cx_large = cx + large_orbit_radius * math.cos(angle_rad)
        cy_large = cy + large_orbit_radius * math.sin(angle_rad)
        
        # 顶点
        vertices_large = []
        for k in range(5):
            v_angle = k * 72 - 90
            v_rad = math.radians(v_angle)
            vx = large_star_radius * math.cos(v_rad)
            vy = large_star_radius * math.sin(v_rad)
            vertices_large.append((vx, vy))
            
        stars_data.append({
            'cx': cx_large, 'cy': cy_large,
            'vertices': vertices_large,
            'scatter_angle': angle_deg,
            'fly_frames': large_fly_frames,
            'archetype': archetype_large
        })
        
        # --- 小星星 (内圈，交错角度) ---
        # 角度偏移 18 度 (360/20)
        angle_small_deg = angle_deg + 18
        angle_small_rad = math.radians(angle_small_deg)
        cx_small = cx + small_orbit_radius * math.cos(angle_small_rad)
        cy_small = cy + small_orbit_radius * math.sin(angle_small_rad)
        
        vertices_small = []
        for k in range(5):
            v_angle = k * 72 - 90
            v_rad = math.radians(v_angle)
            vx = small_star_radius * math.cos(v_rad)
            vy = small_star_radius * math.sin(v_rad)
            vertices_small.append((vx, vy))
            
        stars_data.append({
            'cx': cx_small, 'cy': cy_small,
            'vertices': vertices_small,
            'scatter_angle': angle_small_deg,
            'fly_frames': small_fly_frames,
            'archetype': archetype_small
        })
    
    edge_indices = [(0, 2), (2, 4), (4, 1), (1, 3), (3, 0)]
    
    bullet_idx = 0
    for edge_idx, (start_idx, end_idx) in enumerate(edge_indices):
        for j in range(bullets_per_edge):
            t = j / max(bullets_per_edge - 1, 1)
            
            # 为所有20个星星创建子弹
            for star in stars_data:
                star_cx = star['cx']
                star_cy = star['cy']
                vertices = star['vertices']
                star_angle = star['scatter_angle']
                fly_frames = star['fly_frames']
                archetype = star['archetype']
                
                start_vx, start_vy = vertices[start_idx]
                end_vx, end_vy = vertices[end_idx]
                edge_dx = end_vx - start_vx
                edge_dy = end_vy - start_vy
                
                rel_x = start_vx + t * edge_dx
                rel_y = start_vy + t * edge_dy
                
                bullet_x = star_cx + rel_x
                bullet_y = star_cy + rel_y
                
                # 边散开参数
                mid_x = (start_vx + end_vx) / 2
                mid_y = (start_vy + end_vy) / 2
                base_edge_angle = math.degrees(math.atan2(mid_y, mid_x))
                
                angle_spread = 50
                edge_scatter_angle = base_edge_angle + (t - 0.5) * angle_spread
                
                # 速度梯度：小星星梯度更大（两头速度不一样）
                # 大星星: 0.8~1.3 (scale=0.5)
                # 小星星: 0.6~1.4 (scale=0.8)，梯度更明显
                if archetype == archetype_small:
                    speed_factor = 0.9 + t * 0.6
                else:
                    speed_factor = 0.7 + t * 0.6
                final_edge_speed = edge_scatter_speed * speed_factor
                
                # 同步等待
                wait_for_sync = (total_bullets_per_star - 1 - bullet_idx) * frame_gap + 1
                
                # 平滑运动参数
                accel_frames = 20
                decel_frames = 20
                cruise_frames = int(fly_frames - 0.5 * (accel_frames + decel_frames))
                if cruise_frames < 0:
                    cruise_frames = 0
                    accel_frames = fly_frames // 2
                    decel_frames = fly_frames - accel_frames
                
                motion = (MotionBuilder(speed=0, angle=star_angle)
                    .wait(wait_for_sync)
                    .wait(hold_frames)
                    .accelerate_to(scatter_speed, accel_frames)
                    .wait(cruise_frames)
                    .accelerate_to(0, decel_frames)
                    .wait(hover_frames)
                    .set_angle(edge_scatter_angle)
                    .accelerate_to(final_edge_speed, 20)
                    .build())
                
                ctx.fire(bullet_x, bullet_y, 0, star_angle, archetype, motion=motion)
            
            bullet_idx += 1
            if bullet_idx < total_bullets_per_star:
                yield draw_interval


def _spawn_breathing_spiral(
    ctx: "TaskContext",
    cx: float,
    cy: float,
    arms: int,
    bullets_per_arm: int,
    base_radius: float,
    spiral_tightness: float,
    line_offset_deg: float,
    arrival_frames: int,
    archetype: str,
    rotation: float,
    clockwise: bool,
    draw_interval: int,
    sync_hold_frames: int,
) -> Generator[int, None, None]:
    """
    渐进生成呼吸螺旋弹幕（直线汇聚算法）。

    新算法原理：
    1. 子弹在螺旋位置逐颗出现（从内到外）
    2. 在旋臂前方定义一条径向直线（汇聚线）
    3. 所有子弹同时到达这条直线（速度与距离成正比）
    4. 到达后继续以相同速度移动
    5. 外圈子弹速度快，超越内圈，形成反向旋臂

    参数：
    - line_offset_deg: 汇聚线相对于旋臂起点的角度偏移
    - arrival_frames: 所有子弹同时到达汇聚线的帧数
    """
    direction = 1 if clockwise else -1
    frame_gap = draw_interval + 1
    arrival_time = arrival_frames / 60.0  # 转换为秒

    # 按照从内到外的顺序生成
    for i in range(bullets_per_arm):
        t = i / max(bullets_per_arm - 1, 1)

        # 同步等待：最后一层只等1帧，第一层等最久
        wait_for_sync = (bullets_per_arm - 1 - i) * frame_gap + 1

        for arm in range(arms):
            arm_base_angle = rotation + arm * (360 / arms)

            # 螺旋位置计算
            r = base_radius * (0.3 + t * 0.7)
            bullet_angle_offset = direction * t * spiral_tightness
            theta = math.radians(arm_base_angle + bullet_angle_offset)

            # 子弹在螺旋上的位置
            bullet_x = cx + r * math.cos(theta)
            bullet_y = cy + r * math.sin(theta)

            # ========== 直线汇聚算法 ==========
            # 汇聚线角度（径向直线，在旋臂前方）
            line_angle = arm_base_angle + direction * line_offset_deg

            # 子弹相对于汇聚线的角度差
            # 对于CW螺旋(direction=1)：
            #   - 子弹角度 = arm_base_angle + t * spiral_tightness
            #   - 直线角度 = arm_base_angle + line_offset_deg
            #   - 角度差 = t * spiral_tightness - line_offset_deg
            angle_diff_deg = bullet_angle_offset - direction * line_offset_deg
            angle_diff_rad = math.radians(angle_diff_deg)

            # 子弹到汇聚线的垂直距离
            # 距离 = r * |sin(角度差)|
            distance = r * abs(math.sin(angle_diff_rad))

            # 速度 = 距离 / 时间（所有子弹同时到达）
            speed = distance / arrival_time if arrival_time > 0 else 0

            # 运动方向：所有子弹朝同一方向移动！
            # 对于CW螺旋：子弹朝CCW方向移动（line_angle - 90）
            # 对于CCW螺旋：子弹朝CW方向移动（line_angle + 90）
            # 这样外圈子弹速度快，到达汇聚线后继续超越内圈，形成反向旋臂
            if clockwise:
                movement_angle = line_angle - 90  # CCW方向
            else:
                movement_angle = line_angle + 90  # CW方向

            # 构建运动程序：
            # 1. 等待所有子弹生成完毕
            # 2. 保持形状
            # 3. 直接以计算好的速度移动（无需加速）
            motion = (MotionBuilder(speed=0, angle=movement_angle)
                .wait(wait_for_sync)
                .wait(sync_hold_frames)
                .set_speed(speed)  # 直接设置速度
                .build())

            ctx.fire(bullet_x, bullet_y, 0, movement_angle, archetype, motion=motion)

        # 每层生成完后等待
        if i < bullets_per_arm - 1:
            yield draw_interval


def phase3_spellcard(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    Phase 3: 符卡「双重星环」

    复用第一阶段，但同时画10个大五角星和10个小五角星。
    小五角星在内圈交错，飞出距离较短。
    """
    wave = 0

    # 移动到屏幕中心上方
    yield from ctx.move_to(ctx.state.width / 2, 100, frames=60)

    while True:
        x, y = ctx.owner_pos()

        # ★ 每波开始时触发攻击动画
        ctx.trigger_attack_animation(cooldown=2.0)

        yield from _draw_double_ring_pentagrams(
            ctx, x, y,
            # 大星星参数
            large_star_radius=80,
            large_orbit_radius=80,
            large_fly_frames=60,   # 飞得远
            # 小星星参数
            small_star_radius=50,  # 较小
            small_orbit_radius=50, # 轨道较小
            small_fly_frames=30,   # 飞得近
            # 通用参数
            bullets_per_edge=10,
            draw_interval=2,
            hold_frames=40,
            scatter_speed=160,
            hover_frames=30,
            edge_scatter_speed=100,
            archetype_large="boss_red", # 大星星用 Boss Red
            archetype_small="boss_blue",  # 小星星用 Boss Blue
            base_rotation=wave * 12
        )
        
        wave += 1
        yield 120


def phase4_spellcard(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    Phase 4: 奇迹「六月飞雪」

    "波与粒的界限" 风格弹幕：
    - 基础形状：阿基米德螺线（Boss持续向外发射子弹）
    - 动态效果：发射角度以正弦函数摇摆
    - 在摇摆两端（sin 波峰/波谷）旋转变慢，中间变快
    - 越往后摇摆幅度越大（振幅随时间增加）
    - Boss在中央释放后飞出屏幕，雪花留在中央跟随弹幕节奏旋转
    """
    from model.components import BossAuraState
    
    # 弹幕固定发射位置（屏幕中央）
    center_x = ctx.state.width / 2
    center_y = ctx.state.height / 3  # 屏幕高度的1/3处，约213
    
    # ★ 符卡开始时触发一次攻击动画，设置超长冷却
    ctx.trigger_attack_animation(cooldown=9999.0)

    # 弹幕参数（参考 Lunatic 难度）
    NUM_ARMS = 12                      # 螺旋臂数量
    BULLET_SPEED = 180.0               # 子弹速度 (px/s)
    BASE_AMPLITUDE = 60.0              # 初始摇摆振幅（度）
    AMPLITUDE_GROWTH = 0.05            # 振幅增长速度（度/帧）
    MAX_AMPLITUDE = 120.0              # 最大振幅（度）
    FREQUENCY = 0.10                   # 摇摆频率（每帧）
    BASE_ANGULAR_VELOCITY = 4.0        # 基础旋转速度（度/帧）
    FIRE_INTERVAL = 3                  # 发射间隔（帧）
    
    # Boss飞出配置
    DETACH_FRAME = 60                  # 多少次发射后Boss飞出屏幕（约3秒）
    FLY_OUT_FRAMES = 30                # 飞出动画帧数

    frame = 0
    base_angle = 0.0
    current_amplitude = BASE_AMPLITUDE
    
    # 初始化雪花状态组件
    aura_state = ctx.owner.get(BossAuraState)
    if not aura_state:
        aura_state = BossAuraState()
        ctx.owner.add(aura_state)
    aura_state.detached = False
    aura_state.fixed_x = center_x
    aura_state.fixed_y = center_y
    aura_state.angle = 0.0
    
    # 离开状态标记
    boss_detached = False
    fly_out_generator = None

    while True:
        # 获取Boss当前位置
        boss_x, boss_y = ctx.owner_pos()
        
        # 检查是否到达分离时机
        if frame == DETACH_FRAME and not boss_detached:
            # 记录分离时Boss的位置作为雪花和弹幕的固定位置
            aura_state.fixed_x = boss_x
            aura_state.fixed_y = boss_y
            aura_state.detached = True
            boss_detached = True
            # 开始飞出动画（飞向屏幕上方外）
            fly_out_generator = ctx.move_to(boss_x, -200, frames=FLY_OUT_FRAMES)
        
        # 如果正在飞出，继续飞出动画
        if fly_out_generator is not None:
            try:
                next(fly_out_generator)
            except StopIteration:
                fly_out_generator = None
        
        # 分离前从 Boss 位置发射，分离后从固定位置发射
        if boss_detached:
            fire_x, fire_y = aura_state.fixed_x, aura_state.fixed_y
        else:
            fire_x, fire_y = boss_x, boss_y

        # 1. 计算摇摆角度（正弦函数，振幅逐渐增大）
        swing_angle = current_amplitude * math.sin(FREQUENCY * frame)

        # 2. 计算总发射角度
        total_angle = base_angle + swing_angle
        
        # 3. 同步更新雪花旋转角度（跟随弹幕节奏）
        aura_state.angle = total_angle

        # 4. 发射多条螺旋臂
        for k in range(NUM_ARMS):
            fire_angle = total_angle + k * (360.0 / NUM_ARMS)
            ctx.fire(fire_x, fire_y, BULLET_SPEED, fire_angle, "boss_blue")

        # 5. 更新状态
        base_angle += BASE_ANGULAR_VELOCITY
        # 振幅逐渐增大，但不超过最大值
        current_amplitude = min(current_amplitude + AMPLITUDE_GROWTH, MAX_AMPLITUDE)
        frame += 1

        yield FIRE_INTERVAL


def _fire_pentagrams_at_boss(ctx: "TaskContext") -> "Generator[int, None, None]":
    """
    辅助函数：Boss飞到屏幕中间附近的随机位置并发射反弹五角星。

    1. 计算屏幕中心附近的随机目标位置
    2. Boss平滑移动到该位置
    3. 触发攻击动画并等待蓄力
    4. 发射4个可反弹五角星
    5. 短暂等待
    6. 飞向屏幕外随机一边
    """
    import random

    screen_w = ctx.state.width
    screen_h = ctx.state.height
    MARGIN = 200  # 屏幕外缓冲区

    # 计算屏幕中心附近的随机位置
    # X: 屏幕宽度的 30%~70% 范围内
    # Y: 屏幕高度的 20%~50% 范围内（偏上方，符合Boss战斗区域）
    target_x = screen_w * (0.3 + random.random() * 0.4)
    target_y = screen_h * (0.2 + random.random() * 0.3)

    # Boss移动到目标位置
    yield from ctx.move_to(target_x, target_y, frames=30)

    # 移动完成后的缓冲时间（约 0.5 秒）
    yield 30

    # 触发攻击动画
    ctx.trigger_attack_animation(cooldown=5.0)

    # 一颗颗画出4个可反弹五角星
    yield from draw_bouncing_pentagrams(
        ctx,
        cx=target_x,
        cy=target_y,
        num_stars=4,
        radius=60.0,
        bullets_per_edge=8,
        move_speed=100.0,
        hold_frames=60,
        scatter_speed=120.0,
        scatter_frames=30,
        archetype="boss_red",
        max_bounces=1,
        draw_interval=1,
    )

    # 短暂等待让星星飞出
    yield 30

    # 随机选择一个方向飞出屏幕（上、左、右）
    exit_direction = random.choice(["top", "left", "right"])
    if exit_direction == "top":
        exit_x = target_x
        exit_y = -MARGIN
    elif exit_direction == "left":
        exit_x = -MARGIN
        exit_y = target_y * 0.5  # 偏上方一点
    else:  # right
        exit_x = screen_w + MARGIN
        exit_y = target_y * 0.5

    # 飞出屏幕
    yield from ctx.move_to(exit_x, exit_y, frames=30)


def phase5_spellcard(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    Phase 5: 梦想封印「瞬」

    Boss沿屏幕边缘飞行，飞行时发射方向随机的三层扇形弹幕。
    每完成一次"左→右"+"右→左"的飞行循环，发射4个可反弹五角星。

    移动路径循环执行：
    步骤1: 左侧飞向右上（2条平行线）
    步骤2: 右侧飞向左上（3条平行线）
    → 发射五角星
    步骤3: 左侧飞向右上（3条平行线）
    步骤4: 右侧飞向左上（2条平行线）
    → 发射五角星
    """
    from model.components import BossAuraState
    
    screen_w = ctx.state.width
    screen_h = ctx.state.height
    
    # 检查雪花是否处于分离状态，如果是则让Boss先飞回雪花位置
    aura_state = ctx.owner.get(BossAuraState)
    if aura_state and aura_state.detached:
        # Boss飞回雪花的固定位置
        yield from ctx.move_to(aura_state.fixed_x, aura_state.fixed_y, frames=60)
        # 重新附着雪花
        aura_state.detached = False
        # 等待一小段时间让过渡更自然
        yield 30
        # Boss平滑飞出屏幕左侧，为第五阶段弹幕做准备
        yield from ctx.move_to(-200, screen_h / 2, frames=60)

    # 弹幕参数
    FLY_SPEED = 2520.0          # Boss飞行速度 (px/s)
    FIRE_INTERVAL = 8           # 发射间隔（帧）
    FAN_COUNT = 7               # 每层子弹数
    FAN_SPREAD = 60.0           # 扇形角度
    LAYER_SPEEDS = (120, 180, 240)  # 内/中/外层速度

    # 屏幕外缓冲区（让boss完全消失后再切换路径）
    MARGIN = 200
    LEFT = -MARGIN
    RIGHT = screen_w + MARGIN
    TOP = -MARGIN

    while True:
        # ===== 步骤1: 左侧飞向右上（2条平行线）=====
        yield from _fly_and_fire_phase5(
            ctx,
            start_x=LEFT, start_y=screen_h / 2,
            end_x=RIGHT, end_y=TOP,
            fly_speed=FLY_SPEED, fire_interval=FIRE_INTERVAL,
            fan_count=FAN_COUNT, fan_spread=FAN_SPREAD, layer_speeds=LAYER_SPEEDS,
        )
        yield from _fly_and_fire_phase5(
            ctx,
            start_x=LEFT, start_y=screen_h * 0.8,
            end_x=RIGHT, end_y=screen_h / 2,
            fly_speed=FLY_SPEED, fire_interval=FIRE_INTERVAL,
            fan_count=FAN_COUNT, fan_spread=FAN_SPREAD, layer_speeds=LAYER_SPEEDS,
        )

        # ===== 步骤2: 右侧飞向左上（3条平行线，镜像角度）=====
        yield from _fly_and_fire_phase5(
            ctx,
            start_x=RIGHT, start_y=screen_h / 3,
            end_x=LEFT, end_y=TOP,
            fly_speed=FLY_SPEED, fire_interval=FIRE_INTERVAL,
            fan_count=FAN_COUNT, fan_spread=FAN_SPREAD, layer_speeds=LAYER_SPEEDS,
        )
        yield from _fly_and_fire_phase5(
            ctx,
            start_x=RIGHT, start_y=screen_h * 2 / 3,
            end_x=LEFT, end_y=screen_h / 3,
            fly_speed=FLY_SPEED, fire_interval=FIRE_INTERVAL,
            fan_count=FAN_COUNT, fan_spread=FAN_SPREAD, layer_speeds=LAYER_SPEEDS,
        )
        yield from _fly_and_fire_phase5(
            ctx,
            start_x=RIGHT, start_y=screen_h,
            end_x=LEFT, end_y=screen_h * 2 / 3,
            fly_speed=FLY_SPEED, fire_interval=FIRE_INTERVAL,
            fan_count=FAN_COUNT, fan_spread=FAN_SPREAD, layer_speeds=LAYER_SPEEDS,
        )

        # ★ 完成步骤1(左→右) + 步骤2(右→左)，发射五角星
        yield from _fire_pentagrams_at_boss(ctx)

        # ===== 步骤3: 左侧飞向右上（3条平行线）=====
        yield from _fly_and_fire_phase5(
            ctx,
            start_x=LEFT, start_y=screen_h / 3,
            end_x=RIGHT, end_y=TOP,
            fly_speed=FLY_SPEED, fire_interval=FIRE_INTERVAL,
            fan_count=FAN_COUNT, fan_spread=FAN_SPREAD, layer_speeds=LAYER_SPEEDS,
        )
        yield from _fly_and_fire_phase5(
            ctx,
            start_x=LEFT, start_y=screen_h * 2 / 3,
            end_x=RIGHT, end_y=screen_h / 3,
            fly_speed=FLY_SPEED, fire_interval=FIRE_INTERVAL,
            fan_count=FAN_COUNT, fan_spread=FAN_SPREAD, layer_speeds=LAYER_SPEEDS,
        )
        yield from _fly_and_fire_phase5(
            ctx,
            start_x=LEFT, start_y=screen_h,
            end_x=RIGHT, end_y=screen_h * 2 / 3,
            fly_speed=FLY_SPEED, fire_interval=FIRE_INTERVAL,
            fan_count=FAN_COUNT, fan_spread=FAN_SPREAD, layer_speeds=LAYER_SPEEDS,
        )

        # ===== 步骤4: 右侧飞向左上（2条平行线）=====
        yield from _fly_and_fire_phase5(
            ctx,
            start_x=RIGHT, start_y=screen_h / 2,
            end_x=LEFT, end_y=TOP,
            fly_speed=FLY_SPEED, fire_interval=FIRE_INTERVAL,
            fan_count=FAN_COUNT, fan_spread=FAN_SPREAD, layer_speeds=LAYER_SPEEDS,
        )
        yield from _fly_and_fire_phase5(
            ctx,
            start_x=RIGHT, start_y=screen_h * 0.8,
            end_x=LEFT, end_y=screen_h / 2,
            fly_speed=FLY_SPEED, fire_interval=FIRE_INTERVAL,
            fan_count=FAN_COUNT, fan_spread=FAN_SPREAD, layer_speeds=LAYER_SPEEDS,
        )

        # ★ 完成步骤3(左→右) + 步骤4(右→左)，发射五角星
        yield from _fire_pentagrams_at_boss(ctx)


# ============ Boss 主脚本（纯脚本驱动） ============

def stage1_boss_script(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    Stage 1 Boss 完整脚本（纯脚本驱动模式）。

    控制 Boss 的整个战斗流程：
    - 入场动画
    - Phase 1: 非符「万华镜」
    - Phase 2: 奇迹「摩西开海」
    - Phase 3: 幻符「双重星环」
    - Phase 4: 奇迹「六月飞雪」
    - Phase 5: 梦想封印「瞬」
    - 结束处理
    """
    # 入场：移动到战斗位置
    # 入场：移动到战斗位置
    # 播放 Boss 音乐
    ctx.set_bgm("boss")
    
    ctx.update_boss_hud(phases_remaining=5, timer=30.0)
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
    ctx.update_boss_hud(phases_remaining=5)
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
    ctx.update_boss_hud(phases_remaining=4)
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

    # === Phase 3: 符卡「双重星环」 ===
    ctx.update_boss_hud(phases_remaining=3)
    yield from ctx.run_spell_card(
        name="幻符「双重星环」",
        bonus=150000,
        pattern=phase3_spellcard,
        timeout_seconds=60.0,
        hp=1200,
        **move_params,
    )

    # 阶段转换
    yield from ctx.phase_transition(frames=60)
    yield from ctx.move_to(ctx.state.width / 2, ctx.state.height / 3, frames=30)

    # === Phase 4: 奇迹「六月飞雪」 ===
    ctx.update_boss_hud(phases_remaining=2)
    yield from ctx.run_spell_card(
        name="奇迹「六月飞雪」",
        bonus=200000,
        pattern=phase4_spellcard,
        timeout_seconds=60.0,
        hp=1500,
        move_interval=None,  # Boss保持静止
    )

    # 阶段转换
    yield from ctx.phase_transition(frames=60)
    yield from ctx.move_to(0, ctx.state.height / 2, frames=30)  # 移动到左侧中间（第五阶段起点）

    # === Phase 5: 梦想封印「瞬」 ===
    ctx.update_boss_hud(phases_remaining=1)
    yield from ctx.run_spell_card(
        name="梦想封印「瞬」",
        bonus=250000,
        pattern=phase5_spellcard,
        timeout_seconds=60.0,
        hp=1800,
        move_interval=None,  # 禁用自动移动，使用脚本控制
    )

    # Boss 战结束
    # ctx.kill_boss() 
    # (Controlled by Stage Script now for post-battle dialogue)


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
    boss.add(SpriteInfo(
        name="enemy_boss",
        offset_x=0,
        offset_y=0,
        visible=True
    ))
    
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
        phases_remaining=5,
        visible=True,
    ))

    # 攻击动画状态
    boss.add(BossAttackAnimation())

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
