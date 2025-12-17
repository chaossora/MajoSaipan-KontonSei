from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Optional, List, Generator, TYPE_CHECKING

from .registry import Registry
from .components import (
    BombConfigData, Position, BombFieldTag, Collider, Lifetime, SpriteInfo, CollisionLayer,
    EnemyBulletTag, PlayerBulletTag, PlayerBulletKind, PlayerBulletKindTag, Bullet, Velocity,
    HomingBullet, BulletGrazeState, Shockwave,
)
from .actor import Actor
from .scripting.task import TaskRunner
from .scripting.context import TaskContext

if TYPE_CHECKING:
    from .game_state import GameState


class BombType(Enum):
    """炸弹类型枚举"""
    CIRCLE = auto()  # 圆形炸弹
    BEAM = auto()    # 光束炸弹
    CONVERT = auto()  # 转换炸弹：将敌弹转换为追踪自机弹


bomb_registry: Registry[BombType] = Registry("bomb")


def dispatch_bomb(state, player_pos: Position, cfg: BombConfigData) -> List[Actor]:
    """分发炸弹行为，返回创建的炸弹实体列表。"""
    handler: Optional[Callable] = bomb_registry.get(cfg.bomb_type)
    if handler:
        return handler(state, player_pos, cfg)
    return _bomb_circle(state, player_pos, cfg)


@bomb_registry.register(BombType.CIRCLE)
def _bomb_circle(state, player_pos: Position, cfg: BombConfigData) -> List[Actor]:
    """圆形炸弹：以玩家位置为中心生成炸弹场。"""
    from .game_state import spawn_bomb_field
    bomb = spawn_bomb_field(
        state,
        x=player_pos.x,
        y=player_pos.y,
        radius=cfg.radius,
        duration=cfg.duration,
    )
    return [bomb]


@bomb_registry.register(BombType.BEAM)
def _bomb_beam(state, player_pos: Position, cfg: BombConfigData) -> List[Actor]:
    """光束炸弹：向上生成多段光束。"""
    actors: List[Actor] = []
    num_segments = 12
    spacing = cfg.beam_length / num_segments
    radius = cfg.beam_width / 2
    for i in range(num_segments):
        y = player_pos.y - (i + 1) * spacing
        bomb = Actor()
        bomb.add(Position(player_pos.x, y))
        bomb.add(Collider(
            radius=radius,
            layer=CollisionLayer.PLAYER_BULLET,
            mask=CollisionLayer.ENEMY | CollisionLayer.ENEMY_BULLET,
        ))
        bomb.add(BombFieldTag())
        bomb.add(Lifetime(time_left=cfg.duration))
        bomb.add(SpriteInfo(
            name=cfg.effect_sprite,
            offset_x=int(-radius),
            offset_y=int(-radius),
        ))
        state.add_actor(bomb)
        actors.append(bomb)
    return actors


@bomb_registry.register(BombType.CONVERT)
def _bomb_convert(state, player_pos: Position, cfg: BombConfigData) -> List[Actor]:
    """
    转换炸弹：无敌结束时将全屏敌弹转换为玩家追踪子弹。
    
    使用脚本实现：
    1. 无敌时间由 bomb_system 统一处理
    2. 启动脚本等待无敌结束
    3. 脚本结束时转换子弹
    """
    from random import Random
    
    player = state.get_player()
    if not player:
        return []
    
    # 确保玩家有 TaskRunner
    runner = player.get(TaskRunner)
    if not runner:
        runner = TaskRunner()
        player.add(runner)
    
    # 创建上下文并启动脚本
    ctx = TaskContext(state=state, owner=player, rng=Random())
    runner.start_task(_convert_bomb_script, ctx, cfg)
    
    return []


def _convert_bomb_script(
    ctx: TaskContext,
    cfg: BombConfigData,
) -> Generator[int, None, None]:
    """
    转换炸弹脚本：等待无敌结束后转换子弹。
    """
    from .components import PlayerBomb
    
    player = ctx.owner
    if not player:
        return
    
    # 等待无敌结束
    wait_frames = int(cfg.invincible_time * 60)  # 60 FPS
    yield wait_frames
    
    # 转换子弹
    convert_enemy_bullets(
        ctx.state,
        damage=cfg.convert_damage,
        lifetime=cfg.convert_lifetime,
        speed=cfg.convert_speed,
        turn_rate=cfg.convert_turn_rate,
    )
    
    # 炸弹结束
    bomb = player.get(PlayerBomb)
    if bomb:
        bomb.active = False

    # Spawn Pink Shockwave
    from .actor import Actor
    wave = Actor()
    wave.add(Position(player.get(Position).x, player.get(Position).y))
    wave.add(Shockwave(
        max_radius=800.0,
        speed=1200.0,
        color=(255, 192, 203), # Pink
        width=50,
        radius=10.0,
        alpha=200.0,
        fade_speed=400.0
    ))
    ctx.state.add_actor(wave)


def convert_enemy_bullets(
    state,
    damage: int,
    lifetime: float,
    speed: float,
    turn_rate: float,
) -> None:
    """
    执行敌弹转换：将所有敌弹变成追踪玩家子弹。
    """
    enemy_bullets = [a for a in state.actors if a.has(EnemyBulletTag)]
    
    for bullet in enemy_bullets:
        # 移除敌弹相关组件
        bullet.remove(EnemyBulletTag)
        if bullet.has(BulletGrazeState):
            bullet.remove(BulletGrazeState)
        
        # 添加玩家子弹组件
        bullet.add(PlayerBulletTag())
        bullet.add(PlayerBulletKindTag(kind=PlayerBulletKind.OPTION_TRACKING))
        
        # 更新伤害
        old_bullet = bullet.get(Bullet)
        if old_bullet:
            bullet.remove(Bullet)
        bullet.add(Bullet(damage=damage))
        
        # 更新碰撞层
        old_collider = bullet.get(Collider)
        if old_collider:
            bullet.remove(Collider)
            bullet.add(Collider(
                radius=old_collider.radius,
                layer=CollisionLayer.PLAYER_BULLET,
                mask=CollisionLayer.ENEMY,
            ))
        
        # 更新生命周期
        old_lifetime = bullet.get(Lifetime)
        if old_lifetime:
            bullet.remove(Lifetime)
        bullet.add(Lifetime(time_left=lifetime))
        
        # 添加追踪组件
        bullet.add(HomingBullet(
            turn_rate=turn_rate,
            speed=speed,
        ))
