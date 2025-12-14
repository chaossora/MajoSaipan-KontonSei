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
            
            # 检查 BossState（纯脚本驱动模式下仅用于存储 Boss 名称和掉落配置）
            boss_state = boss.get(BossState)
            
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
            yield 1  # 每帧执行（LuaSTG 风格）
        
        # 确保精确到达目标位置，避免浮点累积误差
        pos.x = target_x
        pos.y = target_y
    
    # ====== Boss 控制原语（纯脚本驱动模式） ======
    
    def set_hp(self, hp: int, max_hp: Optional[int] = None) -> None:
        """
        设置宿主的 HP（用于 Boss 阶段开始时）。
        
        Args:
            hp: 当前 HP
            max_hp: 最大 HP（None 则使用 hp 值）
        """
        from model.components import Health
        
        if self.owner is None:
            return
        
        actual_max = max_hp if max_hp is not None else hp
        health = self.owner.get(Health)
        if health:
            health.hp = hp
            health.max_hp = actual_max
        else:
            self.owner.add(Health(max_hp=actual_max, hp=hp))
    
    def get_hp(self) -> int:
        """获取宿主当前 HP。"""
        from model.components import Health
        
        if self.owner is None:
            return 0
        health = self.owner.get(Health)
        return health.hp if health else 0
    
    def get_hp_ratio(self) -> float:
        """获取宿主 HP 百分比 (0.0 - 1.0)。"""
        from model.components import Health
        
        if self.owner is None:
            return 0.0
        health = self.owner.get(Health)
        if health and health.max_hp > 0:
            return health.hp / health.max_hp
        return 0.0
    
    def set_invulnerable(self, invulnerable: bool) -> None:
        """
        设置宿主无敌状态（阶段转换时使用）。
        
        Args:
            invulnerable: 是否无敌
        """
        from model.components import SpellCardState
        
        if self.owner is None:
            return
        
        spell = self.owner.get(SpellCardState)
        if spell:
            spell.invulnerable = invulnerable
        elif invulnerable:
            # 如果需要无敌但没有 SpellCardState，创建一个临时的
            self.owner.add(SpellCardState(invulnerable=True))
    
    def set_spell_card(
        self,
        name: str,
        bonus: int,
        damage_multiplier: float = 1.0,
    ) -> None:
        """
        开始符卡阶段。
        
        Args:
            name: 符卡名称
            bonus: 符卡奖励分数
            damage_multiplier: 伤害倍率（<1 表示减伤）
        """
        from model.components import SpellCardState, BossHudData
        
        if self.owner is None:
            return
        
        # 添加或更新 SpellCardState
        spell = self.owner.get(SpellCardState)
        if spell:
            spell.spell_name = name
            spell.spell_bonus_value = bonus
            spell.spell_bonus_available = True
            spell.damage_multiplier = damage_multiplier
            spell.invulnerable = False
        else:
            self.owner.add(SpellCardState(
                spell_name=name,
                spell_bonus_value=bonus,
                spell_bonus_available=True,
                damage_multiplier=damage_multiplier,
            ))
        
        # 更新 HUD
        hud = self.owner.get(BossHudData)
        if hud:
            hud.is_spell_card = True
            hud.spell_name = name
            hud.spell_bonus = bonus
            hud.spell_bonus_available = True
    
    def end_spell_card(self, give_bonus: bool = True) -> None:
        """
        结束符卡阶段。
        
        Args:
            give_bonus: 是否给予符卡奖励
        """
        from model.components import SpellCardState, BossHudData, PlayerScore
        
        if self.owner is None:
            return
        
        spell = self.owner.get(SpellCardState)
        if spell and give_bonus and spell.spell_bonus_available:
            # 给玩家加分
            player = self.state.get_player()
            if player:
                score = player.get(PlayerScore)
                if score:
                    score.score += spell.spell_bonus_value
        
        # 移除 SpellCardState
        self.owner.remove(SpellCardState)
        
        # 更新 HUD
        hud = self.owner.get(BossHudData)
        if hud:
            hud.is_spell_card = False
            hud.spell_name = ""
            hud.spell_bonus = 0
    
    def clear_bullets(self) -> None:
        """清除所有敌方子弹（阶段转换用）。"""
        from model.components import EnemyBulletTag
        
        to_remove = [a for a in self.state.actors if a.get(EnemyBulletTag)]
        for actor in to_remove:
            self.state.remove_actor(actor)
    
    def update_boss_hud(
        self,
        phases_remaining: Optional[int] = None,
        timer: Optional[float] = None,
    ) -> None:
        """
        更新 Boss HUD 数据。
        
        Args:
            phases_remaining: 剩余阶段数（星星显示）
            timer: 倒计时秒数
        """
        from model.components import BossHudData, Health
        
        if self.owner is None:
            return
        
        hud = self.owner.get(BossHudData)
        if hud is None:
            return
        
        # 更新 HP 比例
        health = self.owner.get(Health)
        if health and health.max_hp > 0:
            hud.hp_ratio = health.hp / health.max_hp
        
        if phases_remaining is not None:
            hud.phases_remaining = phases_remaining
        if timer is not None:
            hud.timer_seconds = timer
    
    def run_phase(
        self,
        pattern: Callable[["TaskContext"], Generator[int, None, None]],
        timeout_seconds: float,
        hp: int,
        max_hp: Optional[int] = None,
        move_interval: Optional[tuple[int, int]] = (90, 180),
        move_duration: Optional[tuple[int, int]] = (24, 48),
        move_range_x: float = 60.0,
        move_range_y: tuple[float, float] = (60.0, 160.0),
    ) -> Generator[int, None, bool]:
        """
        运行一个弹幕阶段，直到 HP 耗尽或超时。
        
        这是纯脚本驱动 Boss 的核心原语。每帧检查 HP 和计时器，
        同时推进弹幕 pattern 生成器，并处理 Boss 移动。
        
        Args:
            pattern: 弹幕 Task 生成器函数
            timeout_seconds: 超时秒数
            hp: 阶段 HP
            max_hp: 最大 HP（None 则使用 hp）
            move_interval: 移动间隔帧数范围 (min, max)，None 禁用移动
            move_duration: 移动持续帧数范围 (min, max)
            move_range_x: X 方向移动范围（相对于屏幕中心）
            move_range_y: Y 方向移动范围 (min, max)
        
        Yields:
            1（每帧执行，LuaSTG 风格）
        
        Returns:
            True 如果超时结束，False 如果 HP 耗尽
        """
        from model.components import Position
        
        # 设置阶段 HP
        self.set_hp(hp, max_hp)
        
        # 初始化弹幕生成器
        pattern_gen = pattern(self)
        pattern_wait = 0
        
        # 移动状态
        move_enabled = move_interval is not None
        move_timer = 0
        is_moving = False
        move_progress = 0.0
        move_frames_total = 0
        move_start_x = 0.0
        move_start_y = 0.0
        move_target_x = 0.0
        move_target_y = 0.0
        
        if move_enabled and self.owner:
            pos = self.owner.get(Position)
            if pos:
                move_timer = int(move_interval[0] + self.random() * (move_interval[1] - move_interval[0]))
        
        # 计时器（帧数）
        timeout_frames = int(timeout_seconds * 60)
        elapsed_frames = 0
        
        screen_center_x = self.state.width / 2
        margin = 50.0
        
        while elapsed_frames < timeout_frames:
            # 检查 HP
            if self.get_hp() <= 0:
                return False  # HP 耗尽
            
            # 更新 HUD 计时器
            remaining = (timeout_frames - elapsed_frames) / 60.0
            self.update_boss_hud(timer=remaining)
            
            # 处理移动
            if move_enabled and self.owner:
                pos = self.owner.get(Position)
                if pos:
                    if is_moving:
                        # 正在移动：更新位置
                        move_progress += 1.0 / move_frames_total
                        if move_progress >= 1.0:
                            pos.x = move_target_x
                            pos.y = move_target_y
                            is_moving = False
                            # 设置下次移动等待
                            move_timer = int(move_interval[0] + self.random() * (move_interval[1] - move_interval[0]))
                        else:
                            # 缓动
                            t = move_progress
                            if t < 0.5:
                                eased = 2 * t * t
                            else:
                                eased = 1 - (-2 * t + 2) ** 2 / 2
                            pos.x = move_start_x + (move_target_x - move_start_x) * eased
                            pos.y = move_start_y + (move_target_y - move_start_y) * eased
                    else:
                        # 等待中
                        move_timer -= 1
                        if move_timer <= 0:
                            # 开始新移动
                            is_moving = True
                            move_progress = 0.0
                            move_start_x = pos.x
                            move_start_y = pos.y
                            move_target_x = screen_center_x + (self.random() - 0.5) * 2 * move_range_x
                            move_target_x = max(margin, min(self.state.width - margin, move_target_x))
                            move_target_y = move_range_y[0] + self.random() * (move_range_y[1] - move_range_y[0])
                            move_frames_total = int(move_duration[0] + self.random() * (move_duration[1] - move_duration[0]))
            
            # 推进弹幕生成器
            if pattern_wait <= 0:
                try:
                    pattern_wait = next(pattern_gen)
                except StopIteration:
                    # 弹幕结束，继续等待直到 HP 耗尽或超时
                    pass
            else:
                pattern_wait -= 1
            
            elapsed_frames += 1
            yield 1  # 每帧执行（LuaSTG 风格）
        
        return True  # 超时
    
    def run_spell_card(
        self,
        name: str,
        bonus: int,
        pattern: Callable[["TaskContext"], Generator[int, None, None]],
        timeout_seconds: float,
        hp: int,
        max_hp: Optional[int] = None,
        damage_multiplier: float = 1.0,
        move_interval: Optional[tuple[int, int]] = (90, 180),
        move_duration: Optional[tuple[int, int]] = (24, 48),
        move_range_x: float = 60.0,
        move_range_y: tuple[float, float] = (60.0, 160.0),
    ) -> Generator[int, None, bool]:
        """
        运行符卡阶段（便捷方法，组合 set_spell_card + run_phase + end_spell_card）。
        
        Args:
            name: 符卡名称
            bonus: 符卡奖励
            pattern: 弹幕 Task 生成器函数
            timeout_seconds: 超时秒数
            hp: 阶段 HP
            max_hp: 最大 HP
            damage_multiplier: 伤害倍率
            move_interval: 移动间隔帧数范围
            move_duration: 移动持续帧数范围
            move_range_x: X 方向移动范围
            move_range_y: Y 方向移动范围
        
        Yields:
            每帧返回 1
        
        Returns:
            True 如果超时，False 如果 HP 耗尽
        """
        self.set_spell_card(name, bonus, damage_multiplier)
        timeout = yield from self.run_phase(
            pattern, timeout_seconds, hp, max_hp,
            move_interval, move_duration, move_range_x, move_range_y,
        )
        self.end_spell_card(give_bonus=not timeout)
        return timeout
    
    def phase_transition(self, frames: int = 60) -> Generator[int, None, None]:
        """
        阶段转换：清屏 + 无敌 + 等待。
        
        Args:
            frames: 转换等待帧数
        """
        self.clear_bullets()
        self.set_invulnerable(True)
        
        for _ in range(frames):
            yield 1  # 每帧执行（LuaSTG 风格）
        
        self.set_invulnerable(False)
    
    def kill_boss(self) -> None:
        """
        Boss 战结束，标记 Boss 死亡并触发掉落。
        """
        from model.components import EnemyJustDied, BossHudData
        
        if self.owner is None:
            return
        
        # 添加死亡标记
        if not self.owner.get(EnemyJustDied):
            self.owner.add(EnemyJustDied(by_player_bullet=True))
        
        # 隐藏 HUD
        hud = self.owner.get(BossHudData)
        if hud:
            hud.visible = False
        
        # 清屏
        self.clear_bullets()
    
    def random_move(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        frames: int,
    ) -> Generator[int, None, None]:
        """
        随机移动到指定范围内的一个位置。
        
        Args:
            x_min: X 坐标最小值
            x_max: X 坐标最大值
            y_min: Y 坐标最小值
            y_max: Y 坐标最大值
            frames: 移动帧数
        
        Yields:
            每帧返回 1
        """
        target_x = x_min + self.random() * (x_max - x_min)
        target_y = y_min + self.random() * (y_max - y_min)
        yield from self.move_to(target_x, target_y, frames)
    
    def idle_move_loop(
        self,
        x_center: float,
        y_min: float,
        y_max: float,
        x_range: float = 60.0,
        idle_frames_min: int = 90,
        idle_frames_max: int = 180,
        move_frames_min: int = 24,
        move_frames_max: int = 48,
    ) -> Generator[int, None, None]:
        """
        Boss 闲置移动循环（无限循环，需配合阶段使用）。
        
        在弹幕阶段中可以并行运行此循环来实现自动移动：
        - 等待随机时间
        - 移动到随机位置
        - 重复
        
        注意：这是无限循环，通常不直接使用。
        建议在 run_phase 的 pattern 中按需调用 random_move。
        """
        margin = 50.0
        while True:
            # 等待
            wait = int(idle_frames_min + self.random() * (idle_frames_max - idle_frames_min))
            for _ in range(wait):
                yield 1  # 每帧执行（LuaSTG 风格）
            
            # 移动
            target_x = x_center + (self.random() - 0.5) * 2 * x_range
            target_x = max(margin, min(self.state.width - margin, target_x))
            target_y = y_min + self.random() * (y_max - y_min)
            
            move_frames = int(move_frames_min + self.random() * (move_frames_max - move_frames_min))
            yield from self.move_to(target_x, target_y, move_frames)
