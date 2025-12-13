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
    BossState, BossPhase, PhaseType, BossMovementState, BossHudData,
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

def phase1_nonspell(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    Phase 1: 非符 - 「万华镜」
    
    多层旋转的玫瑰曲线弹幕，形成万花筒效果
    - 内层顺时针旋转
    - 外层逆时针旋转
    - 不同颜色/大小的子弹
    """
    angle_offset = 0.0
    wave = 0
    
    while True:
        x, y = ctx.owner_pos()
        
        # 内层：3瓣玫瑰，顺时针
        fire_rose_curve(
            ctx, x, y,
            petals=3,
            radius=60,
            bullet_count=24,
            speed=70,
            archetype="bullet_small",
            rotation=angle_offset,
            expand_first=True,
            hold_frames=25,
        )
        
        # 外层：5瓣玫瑰，逆时针（每隔一波）
        if wave % 2 == 0:
            fire_rose_curve(
                ctx, x, y,
                petals=5,
                radius=90,
                bullet_count=30,
                speed=60,
                archetype="bullet_medium",
                rotation=-angle_offset * 0.7 + 36,
                expand_first=True,
                hold_frames=35,
            )
        
        angle_offset += 11
        wave += 1
        yield 28


def phase2_spellcard(ctx: "TaskContext") -> Generator[int, None, None]:
    """
    Phase 2: 符卡「银河涡流」
    
    螺旋星系弹幕 + 流星五角星的组合：
    1. 中心发射螺旋星系弹幕
    2. 四角发射流星五角星
    3. 追踪弹穿插其中
    """
    rotation = 0.0
    wave = 0
    
    while True:
        x, y = ctx.owner_pos()
        screen_w = ctx.state.width
        
        # 主弹幕：螺旋星系
        if wave % 3 == 0:
            fire_spiral_galaxy(
                ctx, x, y,
                arms=4,
                bullets_per_arm=12,
                base_radius=80,
                spiral_tightness=180,
                speed=65,
                archetype="bullet_small",
                rotation=rotation,
                clockwise=(wave // 3) % 2 == 0,
            )
        
        # 流星五角星从屏幕边缘飞入
        if wave % 4 == 1:
            # 从左上角
            yield from _draw_meteor_star(ctx, 40, 40, 45, rotation, 130)
        elif wave % 4 == 3:
            # 从右上角
            yield from _draw_meteor_star(ctx, screen_w - 40, 40, 45, -rotation, 50)
        
        # 环形弹幕填充
        if wave % 2 == 0:
            fire_ring(ctx, x, y, count=8, speed=80, archetype="bullet_medium", 
                     start_angle=rotation * 2)
        
        rotation += 15
        wave += 1
        yield 35


def _draw_meteor_star(
    ctx: "TaskContext",
    start_x: float,
    start_y: float,
    radius: float,
    rotation: float,
    meteor_angle: float,
) -> Generator[int, None, None]:
    """辅助函数：一颗一颗画出流星五角星"""
    bullets_per_edge = 5
    draw_interval = 2
    
    vertices = []
    for k in range(5):
        angle_deg = rotation + k * 72 - 90
        angle_rad = math.radians(angle_deg)
        vx = radius * math.cos(angle_rad)
        vy = radius * math.sin(angle_rad)
        vertices.append((vx, vy))
    
    edge_indices = [(0, 2), (2, 4), (4, 1), (1, 3), (3, 0)]
    total_bullets = 5 * bullets_per_edge
    total_draw_frames = total_bullets * draw_interval
    
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
            
            bullet_x = start_x + rel_x
            bullet_y = start_y + rel_y
            
            arc_spread = 55
            final_angle = base_scatter_angle + (t - 0.5) * arc_spread
            turn_duration = 25 + int(abs(t - 0.5) * 35)
            wait_for_draw = total_draw_frames - bullet_idx * draw_interval
            
            motion = (MotionBuilder(speed=0, angle=meteor_angle)
                .wait(wait_for_draw)
                .set_speed(90)
                .wait(40)
                .turn_to(final_angle, turn_duration)
                .accelerate_to(120, 25)
                .build())
            
            ctx.fire(bullet_x, bullet_y, 0, meteor_angle, "bullet_small", motion=motion)
            bullet_idx += 1
            yield draw_interval


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


# ============ Boss Factory ============

@boss_registry.register("stage1_boss")
def spawn_stage1_boss(state: "GameState", x: float, y: float) -> Actor:
    """
    Spawn the Stage 1 Boss.
    
    Creates a Boss Actor with:
    - 3 phases (1 non-spell, 2 spell cards)
    - Movement behavior
    - HUD data
    
    Args:
        state: GameState to spawn the boss in
        x: X position
        y: Y position
    
    Returns:
        The created Boss Actor
    """
    from pygame.math import Vector2
    
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
    
    # Define phases
    phases = [
        BossPhase(
            phase_type=PhaseType.NON_SPELL,
            hp=800,
            duration=30.0,
            task=phase1_nonspell,
        ),
        BossPhase(
            phase_type=PhaseType.SPELL_CARD,
            hp=1000,
            duration=45.0,
            spell_name="星符「银河涡流」",
            spell_bonus=100000,
            task=phase2_spellcard,
        ),
        BossPhase(
            phase_type=PhaseType.SPELL_CARD,
            hp=1200,
            duration=60.0,
            spell_name="幻符「星辰万象」",
            spell_bonus=150000,
            task=phase3_spellcard,
        ),
    ]
    
    # Boss state with phases
    boss_state = BossState(
        boss_name="小妖精头目",
        phases=phases,
        current_phase_index=0,
        phase_timer=phases[0].duration,
        drop_power=16,
        drop_point=24,
    )
    boss.add(boss_state)
    
    # Initial health (first phase HP)
    boss.add(Health(max_hp=phases[0].hp, hp=phases[0].hp))
    
    # Movement behavior
    boss.add(BossMovementState(
        y_min=60.0,
        y_max=160.0,
        idle_time_min=1.5,
        idle_time_max=2.5,
        move_duration_min=0.5,
        move_duration_max=0.8,
        target_offset_range=60.0,
    ))
    
    # HUD data
    boss.add(BossHudData(
        boss_name="小妖精头目",
        phases_remaining=len(phases),
        visible=True,
    ))
    
    # TaskRunner for phase tasks
    boss.add(TaskRunner())
    
    # Add to game state
    state.add_actor(boss)
    
    return boss
