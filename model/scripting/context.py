"""
TaskContext：Task 脚本的执行上下文。

提供稳定的引擎原语，用于发射子弹、生成敌人和查询游戏状态。
这是原语层的核心，脚本通过 ctx.xxx() 调用这些原语。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING, Optional, Tuple, Callable, Generator, Any

from pygame.math import Vector2

if TYPE_CHECKING:
    from model.game_state import GameState
    from model.actor import Actor


def angle_to_velocity(speed: float, angle: float) -> Vector2:
    """
    将极坐标 (speed, angle) 转换为速度向量。
    
    坐标系约定：
    - 0° = 右（+X 方向）
    - 90° = 下（+Y 方向，因为 Y 轴向下）
    - 角度顺时针增加
    
    Args:
        speed: 速度，单位 px/s
        angle: 角度，单位度
    
    Returns:
        速度向量 (px/s)
    """
    rad = math.radians(angle)
    return Vector2(math.cos(rad) * speed, math.sin(rad) * speed)


@dataclass
class TaskContext:
    """
    Task 执行上下文，提供稳定的引擎原语。
    
    Attributes:
        state: GameState 引用
        owner: 拥有此 Task 的 Actor（Boss/Enemy/Stage）
        rng: 确定性随机数生成器（用于回放）
    """
    state: "GameState"
    owner: Optional["Actor"]
    rng: Random
    
    def player_pos(self) -> Tuple[float, float]:
        """
        获取玩家当前位置。
        
        Returns:
            (x, y) 坐标元组，如果玩家不存在则返回 (0, 0)
        """
        from model.components import Position
        
        player = self.state.get_player()
        if player:
            pos = player.get(Position)
            if pos:
                return (pos.x, pos.y)
        return (0.0, 0.0)
    
    def owner_pos(self) -> Tuple[float, float]:
        """
        获取 Task 宿主 Actor 的位置。
        
        Returns:
            (x, y) 坐标元组，如果宿主没有 Position 则返回 (0, 0)
        """
        from model.components import Position
        
        if self.owner:
            pos = self.owner.get(Position)
            if pos:
                return (pos.x, pos.y)
        return (0.0, 0.0)
    
    def random(self) -> float:
        """
        获取确定性随机数 [0, 1)。
        
        使用上下文的 RNG 以保证可复现性。
        """
        return self.rng.random()
    
    def random_range(self, a: float, b: float) -> float:
        """
        获取范围内的确定性随机数 [a, b)。
        
        Args:
            a: 下界（包含）
            b: 上界（不包含）
        """
        return a + self.rng.random() * (b - a)
    
    def fire(
        self,
        x: float,
        y: float,
        speed: float,
        angle: float,
        archetype: str = "default",
        motion: Optional[Any] = None,
        damage: Optional[int] = None,
        sprite: Optional[str] = None,
        radius: Optional[float] = None,
        layer: Optional[Any] = None,
        mask: Optional[Any] = None,
        lifetime: Optional[float] = None,
    ) -> "Actor":
        """
        在指定位置发射子弹。
        
        这是核心的子弹创建原语。所有弹幕图案最终都应调用此方法。
        
        Args:
            x: 子弹生成的 X 位置
            y: 子弹生成的 Y 位置
            speed: 子弹速度，单位 px/s
            angle: 子弹角度，单位度（0° = 右，90° = 下）
            archetype: 子弹原型 ID，用于查找默认属性
            motion: 可选的 MotionProgram，用于复杂的子弹运动
            damage: 覆盖伤害值（None 则使用原型默认值）
            sprite: 覆盖精灵名（None 则使用原型默认值）
            radius: 覆盖碰撞半径（None 则使用原型默认值）
            layer: 覆盖碰撞层（None 则使用原型默认值）
            mask: 覆盖碰撞掩码（None 则使用原型默认值）
            lifetime: 覆盖生命周期秒数（None 则使用原型默认值）
        
        Returns:
            创建的子弹 Actor
        """
        from model.actor import Actor
        from model.components import (
            Position, Velocity, Collider, SpriteInfo,
            EnemyBulletTag, EnemyBulletKind, EnemyBulletKindTag,
            Bullet, BulletGrazeState, Lifetime,
        )
        from model.scripting.archetype import get_archetype
        
        # 获取原型属性
        arch = get_archetype(archetype)
        
        # 使用提供的覆盖值或原型默认值
        actual_damage = damage if damage is not None else arch.damage
        actual_sprite = sprite if sprite is not None else arch.sprite
        actual_radius = radius if radius is not None else arch.radius
        actual_layer = layer if layer is not None else arch.layer
        actual_mask = mask if mask is not None else arch.mask
        actual_lifetime = lifetime if lifetime is not None else arch.lifetime
        
        # 创建子弹 Actor
        bullet = Actor()
        
        # 位置
        bullet.add(Position(x, y))
        
        # 从 speed 和 angle 计算速度向量
        velocity = angle_to_velocity(speed, angle)
        bullet.add(Velocity(velocity))
        
        # 标签和子弹数据
        bullet.add(EnemyBulletTag())
        bullet.add(EnemyBulletKindTag(EnemyBulletKind.BASIC))
        bullet.add(Bullet(damage=actual_damage))
        bullet.add(BulletGrazeState())
        
        # 从原型获取精灵信息
        bullet.add(SpriteInfo(name=actual_sprite))
        
        # 使用原型的碰撞层/掩码
        bullet.add(Collider(
            radius=actual_radius,
            layer=actual_layer,
            mask=actual_mask,
        ))
        
        # 生命周期
        bullet.add(Lifetime(time_left=actual_lifetime))
        
        # 可选的 MotionProgram
        if motion is not None:
            bullet.add(motion)
        
        # 添加到游戏状态
        self.state.add_actor(bullet)
        
        return bullet
    
    def _angle_to_player(self, x: float, y: float) -> float:
        """
        计算从 (x, y) 到玩家位置的角度。
        
        坐标系约定：
        - 0° = 右（+X 方向）
        - 90° = 下（+Y 方向）
        - 角度顺时针增加
        
        Args:
            x: 源 X 位置
            y: 源 Y 位置
        
        Returns:
            指向玩家的角度（度）
        """
        px, py = self.player_pos()
        dx = px - x
        dy = py - y
        return math.degrees(math.atan2(dy, dx))
    
    def fire_aimed(
        self,
        x: float,
        y: float,
        speed: float,
        archetype: str = "default",
        motion: Optional[Any] = None,
        damage: Optional[int] = None,
        sprite: Optional[str] = None,
        radius: Optional[float] = None,
        layer: Optional[Any] = None,
        mask: Optional[Any] = None,
        lifetime: Optional[float] = None,
    ) -> "Actor":
        """
        发射朝向玩家当前位置的子弹（自机狙）。
        
        这是一个便捷方法，计算朝向玩家的角度并调用 fire()。
        
        Args:
            x: 子弹生成的 X 位置
            y: 子弹生成的 Y 位置
            speed: 子弹速度，单位 px/s
            archetype: 子弹原型 ID
            motion: 可选的 MotionProgram
            damage: 覆盖伤害值
            sprite: 覆盖精灵名
            radius: 覆盖碰撞半径
            layer: 覆盖碰撞层
            mask: 覆盖碰撞掩码
            lifetime: 覆盖生命周期秒数
        
        Returns:
            创建的子弹 Actor
        """
        angle = self._angle_to_player(x, y)
        return self.fire(
            x, y, speed, angle,
            archetype=archetype,
            motion=motion,
            damage=damage,
            sprite=sprite,
            radius=radius,
            layer=layer,
            mask=mask,
            lifetime=lifetime,
        )
    
    def spawn_enemy(
        self,
        kind: Any,  # EnemyKind
        x: float,
        y: float,
        behavior: Optional[Callable[["TaskContext"], Generator[int, None, None]]] = None,
        hp: Optional[int] = None,
    ) -> "Actor":
        """
        生成敌人并可选地启动其行为 Task。
        
        Args:
            kind: EnemyKind 枚举值，指定敌人类型
            x: 敌人生成的 X 位置
            y: 敌人生成的 Y 位置
            behavior: 可选的 Task 生成器函数，用于敌人行为
            hp: 可选的 HP 覆盖值（None 则使用敌人类型的默认值）
        
        Returns:
            创建的敌人 Actor
        
        **Requirements: 12.1**
        """
        from model.enemies import enemy_registry
        
        # 从注册表获取生成函数
        spawn_fn = enemy_registry.get(kind)
        if spawn_fn is None:
            raise ValueError(f"未知的敌人类型: {kind}")
        
        # 构建生成函数的参数
        kwargs = {}
        if hp is not None:
            kwargs["hp"] = hp
        if behavior is not None:
            kwargs["behavior"] = behavior
            kwargs["rng"] = self.rng  # 共享 RNG 以保证确定性
        
        # 生成敌人（生成函数处理行为附加）
        enemy = spawn_fn(self.state, x, y, **kwargs)
        
        return enemy
    
    def enemies_alive(self) -> int:
        """
        统计游戏状态中存活的敌人数量。
        
        Returns:
            带有 EnemyTag 组件的 Actor 数量
        """
        from model.components import EnemyTag
        
        return sum(1 for a in self.state.actors if a.get(EnemyTag))
    
    def spawn_boss(
        self,
        boss_id: str,
        x: float,
        y: float,
        phases: Optional[list] = None,
    ) -> "Actor":
        """
        生成 Boss 并启动其阶段 Task。
        
        此方法使用 boss_registry 创建 Boss Actor，
        并可选地启动阶段 Task。
        
        Args:
            boss_id: 在 boss_registry 中注册的 Boss ID
            x: Boss 生成的 X 位置
            y: Boss 生成的 Y 位置
            phases: 可选的阶段 Task 生成器函数列表。
                    如果提供，将使用这些而非 Boss 的默认阶段。
        
        Returns:
            创建的 Boss Actor
        
        Raises:
            ValueError: 如果 boss_id 未在注册表中找到
        
        Requirements: 10.3
        """
        from model.boss_registry import boss_registry
        from model.scripting.task import TaskRunner
        from model.components import BossState
        
        # 从注册表获取生成函数
        spawn_fn = boss_registry.get(boss_id)
        if spawn_fn is None:
            raise ValueError(f"未知的 boss_id: {boss_id}")
        
        # 生成 Boss
        boss = spawn_fn(self.state, x, y)
        
        # 如果提供了 phases，添加 TaskRunner 并启动阶段管理
        if phases is not None:
            # 如果没有 TaskRunner 组件则添加
            runner = boss.get(TaskRunner)
            if runner is None:
                runner = TaskRunner()
                boss.add(runner)
            
            # 如果存在 BossState 则存储 phases
            boss_state = boss.get(BossState)
            if boss_state is not None:
                # 存储阶段 Task 函数供 boss_phase_system 后续使用
                # 实际的阶段 Task 将在阶段转换时由 boss_phase_system 启动
                pass
            
            # 为 Boss 的 Task 创建上下文
            boss_ctx = TaskContext(
                state=self.state,
                owner=boss,
                rng=self.rng,  # 共享 RNG 以保证确定性
            )
            
            # 如果提供了 phases，启动第一个阶段 Task
            if phases:
                runner.start_task(phases[0], boss_ctx)
        
        return boss
    
    def move_to(
        self,
        target_x: float,
        target_y: float,
        frames: int,
    ) -> Generator[int, None, None]:
        """
        在指定帧数内平滑移动宿主 Actor 到目标位置。
        
        这是一个生成器方法，设计用于 `yield from`：
            yield from ctx.move_to(x, y, frames=60)
        
        移动是线性插值 - 每帧移动相同距离。
        所有帧完成后，位置会精确设置为目标值，
        以避免浮点累积误差。
        
        Args:
            target_x: 目标 X 位置
            target_y: 目标 Y 位置
            frames: 完成移动的帧数
        
        Yields:
            每帧移动返回 1
        
        Requirements: 12.2
        """
        from model.components import Position
        
        if self.owner is None:
            return
        
        pos = self.owner.get(Position)
        if pos is None:
            return
        
        if frames <= 0:
            # 如果帧数为 0 或负数，立即移动
            pos.x = target_x
            pos.y = target_y
            return
        
        start_x, start_y = pos.x, pos.y
        dx = (target_x - start_x) / frames
        dy = (target_y - start_y) / frames
        
        for _ in range(frames):
            pos.x += dx
            pos.y += dy
            yield 1
        
        # 确保精确到达目标位置，避免浮点累积误差
        pos.x = target_x
        pos.y = target_y
