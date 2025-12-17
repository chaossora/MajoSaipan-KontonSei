from __future__ import annotations

import pygame
import math

from model.game_state import GameState
from model.actor import Actor
from model.components import (
    Position, Velocity, SpriteInfo, RenderHint, HudData, PlayerTag,
    BossHudData, OptionState, OptionConfig, InputState,
    PlayerBulletKindTag, PlayerBulletKind,
    EnemyKindTag, EnemyKind,
    EnemyBulletKindTag, EnemyBulletKind,
    LaserTag, LaserState, LaserType,
    PlayerDamageState,
    Shockwave,
)
from model.game_config import CollectConfig


# ====== 玩家子弹类型 → 精灵映射表 ======
# View 层统一管理子弹贴图配置
PLAYER_BULLET_SPRITES: dict[PlayerBulletKind, tuple[str, int, int]] = {
    # kind: (sprite_name, offset_x, offset_y)
    
    # Normal Bullets (Shared) - Size 20x40 -> Center (-10, -20)
    PlayerBulletKind.MAIN_NORMAL: ("player_bullet_normal", -10, -20),
    # Enhanced Bullets (Shared) - Size 64x128 -> Center (-32, -64)
    PlayerBulletKind.MAIN_ENHANCED: ("player_bullet_enhanced", -32, -64),
    
    # Option Bullets (Alias to Normal/Enhanced)
    PlayerBulletKind.OPTION_NORMAL: ("player_bullet_option", -10, -20),
    PlayerBulletKind.OPTION_ENHANCED: ("player_bullet_option_enhanced", -32, -64),
    
    # Option Tracking Bullet (Unique) - Size 20x32 -> Center (-10, -16)
    PlayerBulletKind.OPTION_TRACKING: ("player_bullet_option_tracking", -10, -16),
}
# 默认子弹精灵（未知类型时的回退）
DEFAULT_BULLET_SPRITE = ("player_bullet_basic", -4, -8)


# ====== 敌人类型 → 精灵映射表 ======
ENEMY_SPRITES: dict[EnemyKind, tuple[str, int, int]] = {
    # 类型: (精灵名, X偏移, Y偏移)
    EnemyKind.FAIRY_SMALL: ("enemy_fairy_small", -16, -16),
    # Frame 88x64 -> Center (-44, -32)
    EnemyKind.FAIRY_LARGE: ("enemy_fairy_large", -44, -32),
    EnemyKind.MIDBOSS: ("enemy_midboss", -32, -32),
    EnemyKind.BOSS: ("enemy_boss", -32, -32),
}
DEFAULT_ENEMY_SPRITE = ("enemy_basic", -16, -16)


# ====== 敌人子弹类型 → 精灵映射表 ======
# ====== 敌人子弹类型 → 精灵映射表 ======
ENEMY_BULLET_SPRITES: dict[EnemyBulletKind, tuple[str, int, int]] = {
    # 类型: (精灵名, X偏移, Y偏移)
    EnemyBulletKind.BASIC: ("enemy_bullet_basic", -4, -4),
    # Boss 子弹 (20x20 -> Center -10, -10)
    EnemyBulletKind.BOSS_BLUE: ("boss_bullet_blue", -10, -10),
    EnemyBulletKind.BOSS_RED: ("boss_bullet_red", -10, -10),
}
DEFAULT_ENEMY_BULLET_SPRITE = ("enemy_bullet_basic", -4, -4)


from view.enemy_renderer import EnemyRenderer
from view.boss_renderer import BossRenderer


class Renderer:
    """渲染器：从游戏状态（只读）渲染精灵和 HUD。"""

    def __init__(self, screen: pygame.Surface, assets) -> None:
        self.screen = screen
        self.assets = assets
        self.font_small = pygame.font.Font(None, 24)
        try:
            if hasattr(assets, 'font_path'):
                self.font_small = pygame.font.Font(assets.font_path, 24)
        except (FileNotFoundError, pygame.error):
            print("Warning: Custom font not found. Using default.")
            self.font_small = pygame.font.Font(None, 24)
        
        self.enemy_renderer = EnemyRenderer(screen, assets)
        self.boss_renderer = BossRenderer(screen, assets)
        
        # 动画状态缓存：{ id(actor): {"state": str, "frame_index": int, "timer": float} }
        self.anim_cache = {}
        
        # 樱花 VFX 状态
        self.sakura_rotation = 0.0

    def render(self, state: GameState, flip: bool = True) -> None:
        GAME_WIDTH = 480
        SIDEBAR_WIDTH = 240
        SCREEN_HEIGHT = state.height

        # 1. 清空全屏 / 绘制侧边栏背景
        # 整体清空
        self.screen.fill((20, 20, 20))
        
        # 侧边栏背景（右侧）
        sidebar_bg = self.assets.get_image("ui_sidebar_bg")
        if sidebar_bg:
            self.screen.blit(sidebar_bg, (GAME_WIDTH, 0))
        
        # 分割线
        pygame.draw.line(self.screen, (255, 255, 255), (GAME_WIDTH, 0), (GAME_WIDTH, SCREEN_HEIGHT), 2)

        # 2. 设定游戏区域 Clipping
        # 所有的游戏内物体渲染只允许在左侧 480 像素内显示
        game_rect = pygame.Rect(0, 0, GAME_WIDTH, SCREEN_HEIGHT)
        self.screen.set_clip(game_rect)

        # 3. 绘制游戏背景（在 Clip 区域内）
        bg = self.assets.get_image("background")
        if bg:
            scroll_speed = 60.0  # 像素/秒
            # 计算偏移量 (0 到 height)
            offset_y = (state.time * scroll_speed) % state.height 
            
            # 绘制两张图以实现循环
            self.screen.blit(bg, (0, offset_y))
            self.screen.blit(bg, (0, offset_y - state.height))
        else:
            self.screen.fill((0, 0, 0))
        
        # 简单的垃圾回收：移除不在当前 state.actors 中的 actor 缓存
        current_actor_ids = {id(a) for a in state.actors}
        for aid in list(self.anim_cache.keys()):
            if aid not in current_actor_ids:
                del self.anim_cache[aid]

        # 初始化本帧的共享发光层
        if not hasattr(self, 'glow_surface') or self.glow_surface.get_size() != (GAME_WIDTH, SCREEN_HEIGHT):
            self.glow_surface = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        else:
            self.glow_surface.fill((0, 0, 0, 0))

        # Pass 1: 绘制激光发光层 (Glow Pass)
        for actor in state.actors:
            if actor.has(LaserTag):
                self._draw_laser_glow(actor)
        
        # 将发光层混合到屏幕（在实体之前，或者在背景之上）
        self.screen.blit(self.glow_surface, (0, 0))

        # Pass 2: 绘制所有游戏对象主体 (Main Pass)
        # 分层渲染：普通 -> 子弹 -> Boss (Boss > Bullets 要求)
        layer_boss = []
        layer_bullet = []
        layer_normal = []
        
        for actor in state.actors:
            # Boss
            ek = actor.get(EnemyKindTag)
            if ek and ek.kind == EnemyKind.BOSS:
                layer_boss.append(actor)
                continue
            
            # Bullets
            if actor.get(PlayerBulletKindTag) or actor.get(EnemyBulletKindTag):
                layer_bullet.append(actor)
                continue
            
            # Others
            layer_normal.append(actor)
            
        # 绘制顺序
        # 先绘制樱花（在角色背后）
        self._render_sakura(state)
        
        for actor in layer_normal:
            self._draw_actor(actor, state)
            
        for actor in layer_bullet:
            self._draw_actor(actor, state)
            
        for actor in layer_boss:
            self._draw_actor(actor, state)

        # Draw Shockwaves (Overlay on top of normal game elements)
        self._draw_shockwaves(state)

        # 绘制子机（在玩家精灵之上）
        self._render_options(state)

        # 绘制 PoC 线
        self._draw_poc_line(state)

        # Boss HUD (保留在游戏区域内)
        self._render_boss_hud(state)

        # 4. 解除 Clip，绘制侧边栏 UI
        self.screen.set_clip(None)

        # 玩家 HUD (移至侧边栏)
        self._render_hud(state)

        # Cut-in Animation (Overlay)
        if state.cutin.active:
            self._render_cutin(state)

        # Dialogue Overlay
        if state.dialogue.active:
            self._render_dialogue(state)

        if flip:
            pygame.display.flip()

    def _draw_actor(self, actor: Actor, state: GameState = None) -> None:
        """绘制精灵和可选的渲染提示。"""
        pos = actor.get(Position)
        if not pos:
            return

        # 优先检查是否是玩家子弹（通过类型查表渲染）
        bullet_kind_tag = actor.get(PlayerBulletKindTag)
        if bullet_kind_tag:
            sprite_name, ox, oy = PLAYER_BULLET_SPRITES.get(
                bullet_kind_tag.kind, DEFAULT_BULLET_SPRITE
            )
            image = self.assets.get_image(sprite_name)
            
            # 旋转逻辑：根据速度方向旋转子弹
            vel = actor.get(Velocity)
            if vel and (vel.vec.x != 0 or vel.vec.y != 0):
                # 默认朝上 (0, -1) -> 对应角度 90度 (atan2(-1, 0) = -90? No, standard math angle)
                # Math: Right=0, Up=90 (in standard cartesian), but screen Y is down.
                # Screen coords: Right=(1,0), Down=(0,1), Up=(0,-1).
                # atan2(y, x): atan2(0, 1)=0, atan2(1, 0)=90, atan2(-1,0)=-90.
                # We want Up (atan2=-90) to be Rotation 0.
                # Angle = -math.degrees(atan2(vy, vx)) - 90
                # Ex: Up (0, -1) -> atan2=-90 -> -(-90)-90 = 0. Correct.
                # Ex: Right (1, 0) -> atan2=0 -> -0-90 = -90. Clockwise 90. Correct.
                angle = -math.degrees(math.atan2(vel.vec.y, vel.vec.x)) - 90
                
                # 只有当角度显著时才旋转（优化）
                if abs(angle) > 0.1:
                    image = pygame.transform.rotate(image, angle)
                    # 旋转后使用中心点绘制，不再使用 ox/oy (ox/oy 本质就是 -w/2, -h/2)
                    rect = image.get_rect(center=(int(pos.x), int(pos.y)))
                    self.screen.blit(image, rect)
                    return

            # 无旋转（垂直向上）或无速度：使用默认偏移绘制（即 TopLeft）
            x = int(pos.x + ox)
            y = int(pos.y + oy)
            self.screen.blit(image, (x, y))
            return

        # 检查是否是敌人子弹（通过类型查表渲染）
        enemy_bullet_kind_tag = actor.get(EnemyBulletKindTag)
        if enemy_bullet_kind_tag:
            # 优先检查 SpriteInfo 覆盖
            sprite_info = actor.get(SpriteInfo)
            if sprite_info and sprite_info.name:
                image = self.assets.get_image(sprite_info.name)
                # 自动居中
                w, h = image.get_size()
                ox, oy = -w // 2, -h // 2
            else:
                sprite_name, ox, oy = ENEMY_BULLET_SPRITES.get(
                    enemy_bullet_kind_tag.kind, DEFAULT_ENEMY_BULLET_SPRITE
                )
                image = self.assets.get_image(sprite_name)
            
            x = int(pos.x + ox)
            y = int(pos.y + oy)
            self.screen.blit(image, (x, y))
            return

        # 检查是否是激光
        if actor.has(LaserTag):
            self._draw_laser(actor, pos)
            return

        # 检查是否是敌人（通过类型查表渲染）
        enemy_kind_tag = actor.get(EnemyKindTag)
        if enemy_kind_tag:
            # 优先处理 Boss
            if enemy_kind_tag.kind == EnemyKind.BOSS:
                 if actor.get(SpriteInfo):
                     self.boss_renderer.render(actor, state)
                     return
            
            # 如果有 SpriteInfo，优先使用 EnemyRenderer (支持动画)
            if actor.get(SpriteInfo):
                self.enemy_renderer.render(actor, state)
                return

            sprite_name, ox, oy = ENEMY_SPRITES.get(
                enemy_kind_tag.kind, DEFAULT_ENEMY_SPRITE
            )
            image = self.assets.get_image(sprite_name)
            x = int(pos.x + ox)
            y = int(pos.y + oy)
            self.screen.blit(image, (x, y))
            # 敌人可能需要渲染提示（如碰撞框）
            hint = actor.get(RenderHint)
            if hint and hint.draw_collider:
                from model.components import Collider
                col = actor.get(Collider)
                if col:
                    pygame.draw.circle(
                        self.screen, (255, 0, 0), (int(pos.x), int(pos.y)), int(col.radius), 1
                    )
            return

        # 其他实体使用 SpriteInfo 组件渲染
        sprite = actor.get(SpriteInfo)
        if not sprite:
            return

        # 检查是否可见（用于闪烁效果）
        if not sprite.visible:
            return

        # 默认取静态图片
        image = self.assets.get_image(sprite.name)
        
        # 尝试播放玩家动画
        inp = actor.get(InputState)
        if inp and hasattr(self.assets, "player_frames") and state:
            # 1. 确定目标动作状态
            target_anim = "idle"
            if inp.left and not inp.right:
                target_anim = "left"
            elif inp.right and not inp.left:
                target_anim = "right"
            
            # 2. 获取/初始化该 actor 的动画缓存
            aid = id(actor)
            if aid not in self.anim_cache:
                self.anim_cache[aid] = {
                    "state": target_anim,
                    "frame_index": 0,
                    "timer": 0.0
                }
            
            cache = self.anim_cache[aid]
            
            # 3. 状态切换检测
            if cache["state"] != target_anim:
                cache["state"] = target_anim
                cache["frame_index"] = 0
                cache["timer"] = 0.0
            
            # 4. 更新动画帧
            # 设定每帧持续时间 (比如 0.05秒 ~ 3帧/60fps)
            frame_duration = 0.08
            cache["timer"] += 1.0 / 60.0  # 假设 60 FPS，或者用 state.delta_time 如果有
            
            if cache["timer"] >= frame_duration:
                cache["timer"] = 0.0
                current_idx = cache["frame_index"]
                
                # 获取当前动作的总帧数
                frames = self.assets.player_frames.get(target_anim, [])
                total_frames = len(frames)
                
                if total_frames > 0:
                    next_idx = current_idx + 1
                    
                    if target_anim == "idle":
                        # 待机：完全循环
                        next_idx = next_idx % total_frames
                    else:
                        # 左右移动：0->7 播放完后，都从第5帧（索引4）开始循环
                        if next_idx >= total_frames:
                            next_idx = 4
                            
                    cache["frame_index"] = next_idx

            # 5. 取出对应帧
            frames = self.assets.player_frames.get(target_anim)
            if frames and 0 <= cache["frame_index"] < len(frames):
                image = frames[cache["frame_index"]]

        x = int(pos.x + sprite.offset_x)
        y = int(pos.y + sprite.offset_y)
        self.screen.blit(image, (x, y))

        hint = actor.get(RenderHint)
        if hint:
            if hint.show_hitbox:
                pygame.draw.circle(self.screen, (255, 0, 0), (int(pos.x), int(pos.y)), 2)
            if hint.show_graze_field and hint.graze_field_radius > 0:
                self._draw_graze_field(pos, hint.graze_field_radius)

    def _draw_poc_line(self, state: GameState) -> None:
        """绘制点收集线（Point-of-Collection）。"""
        cfg: CollectConfig = state.get_resource(CollectConfig)  # type: ignore
        poc_ratio = cfg.poc_line_ratio if cfg else 0.25
        poc_y = int(state.height * poc_ratio)

        pygame.draw.line(
            self.screen,
            (80, 80, 80),
            (0, poc_y),
            (self.screen.get_width(), poc_y),
            1,
        )

    def _render_hud(self, state: GameState) -> None:
        """使用 HudData 和 EntityStats 绘制玩家 HUD。"""
        player = next((a for a in state.actors if a.has(PlayerTag) and a.get(HudData)), None)
        if not player:
            return

        hud = player.get(HudData)
        if not hud:
            return

        lines = [
            f"SCORE  {hud.score:09d}",
            f"LIVES  {hud.lives}/{hud.max_lives}   BOMBS  {hud.bombs}/{hud.max_bombs}",
            f"POWER  {hud.power:.2f}/{hud.max_power:.2f}",
            f"GRAZE  {hud.graze_count}",
        ]

        # 调试统计信息
        s = state.entity_stats
        lines.append(
            f"ENT   total {s.total:3d}  E {s.enemies:3d}  "
            f"EB {s.enemy_bullets:3d}  PB {s.player_bullets:3d}  IT {s.items:3d}"
        )

        # 侧边栏起始 X
        x = state.width + 20
        y = 30
        line_h = 32
        
        def draw_text_outline(text, color, cur_y):
            """绘制带描边的文字"""
            outline_color = (0, 0, 0)
            # 简单描边：8方向
            offsets = [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]
            for ox, oy in offsets:
                surf = self.font_small.render(text, True, outline_color)
                self.screen.blit(surf, (x + ox, cur_y + oy))
            
            # 主体
            surf = self.font_small.render(text, True, color)
            self.screen.blit(surf, (x, cur_y))

        # 1. 标题 (Image)
        status_title = self.assets.get_image("ui_status_title")
        sidebar_w = self.screen.get_width() - state.width
        title_x = state.width + (sidebar_w - status_title.get_width()) // 2
        self.screen.blit(status_title, (title_x, y))
        y += status_title.get_height() + 10

        # 2. 分数 (黄色)
        draw_text_outline(f"SCORE  {hud.score:09d}", (255, 220, 0), y)
        y += line_h

        # 3. 生命值 (红粉)
        draw_text_outline("LIVES", (255, 100, 150), y)
        y += 34 # 增加 Label 和 图标 之间的间距
        
        icon_active = self.assets.get_image("icon_life_active")
        icon_empty = self.assets.get_image("icon_life_empty")
        
        icon_x = x
        for i in range(hud.max_lives):
            if i < hud.lives:
                self.screen.blit(icon_active, (icon_x, y))
            else:
                self.screen.blit(icon_empty, (icon_x, y))
            icon_x += 36 # 间距
        
        y += 40

        # 4. 其他属性 (BOMB:绿, POWER:橙, GRAZE:蓝)
        items = [
            (f"BOMBS  {hud.bombs}/{hud.max_bombs}", (100, 255, 100)),
            (f"POWER  {hud.power:.2f}/{hud.max_power:.2f}", (255, 160, 60)),
            (f"GRAZE  {hud.graze_count}", (100, 200, 255)),
        ]

        for text, color in items:
            draw_text_outline(text, color, y)
            y += line_h

        # 调试统计 (E/EB)
        s = state.entity_stats
        y += 12
        debug_surf = self.font_small.render(f"E:{s.enemies} EB:{s.enemy_bullets}", True, (100, 100, 100))
        self.screen.blit(debug_surf, (x, y))

        # Boss Info (移至侧边栏 - Debug 下方)
        boss_hud = None
        # 简单查找是否有可见的 BossHudData
        # 注意：这里假设已导入 BossHudData，参考 _render_boss_hud 应该没问题
        for actor in state.actors:
            h = actor.get(BossHudData)
            if h and h.visible:
                boss_hud = h
                break
        
        if boss_hud:
            y += 50 # 往下移多一点，避免太挤
            # 1. Boss Title (Image)
            boss_title = self.assets.get_image("ui_boss_title")
            sidebar_w = self.screen.get_width() - state.width
            title_x = state.width + (sidebar_w - boss_title.get_width()) // 2
            self.screen.blit(boss_title, (title_x, y))
            y += boss_title.get_height() + 10
            draw_text_outline(boss_hud.boss_name, (255, 200, 200), y)
            
            # 符卡名
            if boss_hud.is_spell_card and boss_hud.spell_name:
                y += 32
                draw_text_outline(boss_hud.spell_name, (255, 100, 255), y)

            y += 32
            # 时间变红警告
            time_color = (255, 50, 50) if boss_hud.timer_seconds < 10 else (255, 255, 255)
            draw_text_outline(f"TIME {int(boss_hud.timer_seconds):02d}", time_color, y)
            y += 10

        # 绘制擦弹能量条
        self._render_graze_energy_bar(state, hud, y)

    def _render_graze_energy_bar(self, state: GameState, hud: HudData, start_y: int) -> None:
        """绘制擦弹能量条。"""
        bar_x = 20
        bar_y = state.height - 25
        bar_width = 160
        bar_height = 8

        # 背景
        pygame.draw.rect(
            self.screen,
            (40, 40, 40),
            (bar_x, bar_y, bar_width, bar_height),
        )

        # 能量填充
        if hud.max_graze_energy > 0:
            fill_ratio = hud.graze_energy / hud.max_graze_energy
            fill_width = int(bar_width * fill_ratio)

            # 颜色：普通为蓝色，增强状态时金色闪烁
            if hud.is_enhanced:
                # 增强状态金色闪烁效果
                blink = int(state.time * 8) % 2
                bar_color = (255, 220, 80) if blink else (255, 180, 50)
            else:
                # 普通状态蓝色渐变（能量越高越亮）
                intensity = int(100 + 155 * fill_ratio)
                bar_color = (80, intensity, 255)

            if fill_width > 0:
                pygame.draw.rect(
                    self.screen,
                    bar_color,
                    (bar_x, bar_y, fill_width, bar_height),
                )

        # 边框
        border_color = (255, 200, 100) if hud.is_enhanced else (150, 150, 150)
        pygame.draw.rect(
            self.screen,
            border_color,
            (bar_x, bar_y, bar_width, bar_height),
            1,
        )
        
        # Removed label drawing as requested

    def _draw_graze_field(self, pos: Position, radius: float) -> None:
        """绘制擦弹半径覆盖层。"""
        int_radius = int(radius)
        if int_radius <= 0:
            return

        size = int_radius * 2
        overlay = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (int_radius, int_radius)

        pygame.draw.circle(
            overlay,
            (80, 200, 255, 90),
            center,
            int_radius,
            width=2,
        )

        x = int(pos.x) - int_radius
        y = int(pos.y) - int_radius
        self.screen.blit(overlay, (x, y))

    def _render_options(self, state: GameState) -> None:
        """绘制玩家子机。"""
        player = state.get_player()
        if not player:
            return

        option_state = player.get(OptionState)
        option_cfg = player.get(OptionConfig)

        if not (option_state and option_cfg):
            return

        # 获取子机精灵名称（根据角色配置）
        sprite_name = option_cfg.option_sprite
        option_img = self.assets.get_image(sprite_name)

        # 绘制每个激活的子机
        rotation_speed = -180.0  # 度/秒
        angle = (state.time * rotation_speed) % 360
        rotated_img = pygame.transform.rotate(option_img, angle)
        
        for i in range(option_state.active_count):
            if i >= len(option_state.current_positions):
                continue

            pos = option_state.current_positions[i]
            # 使用中心绘制，因为旋转会改变图像尺寸
            # rect.center = (pos[0], pos[1])
            rect = rotated_img.get_rect(center=(int(pos[0]), int(pos[1])))
            self.screen.blit(rotated_img, rect)

    def _render_sakura(self, state: GameState) -> None:
        """绘制无敌樱花 VFX（带旋转效果，在角色背后）。"""
        player = state.get_player()
        if not player:
            return
        
        dmg_state = player.get(PlayerDamageState)
        pos = player.get(Position)
        if not (dmg_state and pos):
            return
        
        # 只有在无敌时才显示樱花
        if dmg_state.invincible_timer <= 0:
            return
        
        # 获取樱花图片
        sakura_img = self.assets.images.get("sakura")
        if not sakura_img:
            return
        
        # 更新旋转角度
        dt = 1.0 / 60.0  # 假设 60 FPS
        rotation_speed = 120.0  # 度/秒
        self.sakura_rotation = (self.sakura_rotation + rotation_speed * dt) % 360
        
        # 旋转并绘制
        rotated = pygame.transform.rotate(sakura_img, self.sakura_rotation)
        rect = rotated.get_rect(center=(int(pos.x), int(pos.y)))
        self.screen.blit(rotated, rect)

    def _render_boss_hud(self, state: GameState) -> None:
        """渲染 Boss HUD：血条、计时器、符卡名、剩余阶段星星。"""
        # 查找场上的 Boss
        boss_hud = None
        for actor in state.actors:
            hud = actor.get(BossHudData)
            if hud and hud.visible:
                boss_hud = hud
                break

        if not boss_hud:
            return

    def _render_cutin(self, state: GameState) -> None:
        """Render Boss Cut-in animation overlay."""
        cutin = state.cutin
        
        # Duration Constants (Should match Controller logic)
        DURATION_ENTER = 0.8
        DURATION_HOLD = 1.0
        DURATION_EXIT = 0.5
        
        # Overlay removed as per user request (no dark/blur background)

        # 2. Portrait
        img = self.assets.get_image(cutin.portrait_name)
        if not img:
            return
            
        # Layout: Horizontal Portrait usually across the screen or eyes.
        # Assuming 480 width.
        
        # Entrance Animation: Slide from Right to Left? Or Scale?
        # User said "Flash out" (appear suddenly).
        # Let's do a quick slide + fade in.
        
        iw, ih = img.get_size()
        # Scale if too big for width
        if iw > state.width:
            ratio = state.width / iw
            iw = state.width
            ih = int(ih * ratio)
            img = pygame.transform.smoothscale(img, (iw, ih))
            
        # Center Y
        target_x = 0
        target_y = (state.height - ih) // 3  # Upper third
        
        draw_x = target_x
        draw_alpha = 255
        
        if cutin.stage == 0: # Enter
            progress = min(1.0, cutin.timer / DURATION_ENTER)
            # Slide from Right
            start_x = state.width
            # Ease Out Back
            c1 = 1.70158
            c3 = c1 + 1
            t = progress - 1
            ease = 1 + c3 * math.pow(t, 3) + c1 * math.pow(t, 2)
            
            draw_x = start_x + (target_x - start_x) * ease
            draw_alpha = int(255 * progress)
            
        elif cutin.stage == 1: # Hold
            draw_x = target_x
            draw_alpha = 255
            
        elif cutin.stage == 2: # Exit
            progress = min(1.0, cutin.timer / DURATION_EXIT)
            # Fade out
            draw_alpha = int(255 * (1 - progress))
            draw_x = target_x - int(100 * progress) # Slight slide left
            
        if draw_alpha < 0: draw_alpha = 0
        if draw_alpha > 255: draw_alpha = 255
        
        img.set_alpha(draw_alpha)
        self.screen.blit(img, (int(draw_x), int(target_y)))
        # Reset alpha for next use (though get_image returns ref, set_alpha might persist)
        # Ideally we copy or reset. Pygame surfaces verify: set_alpha modifies the surface.
        # So we should probably reset it or copy it.
        # For performance, we reset it to 255 if we modify it?
        # Creating a copy every frame is safer for generic asset management.
        # But since we modify it every frame anyway, it will be overwritten next frame.
        # Issue: if other things use "boss_cutin", they will see the alpha.
        # FIX: Blit with special flags or creating temp surface.
        # Pygame blit doesn't support separate alpha param unless per-pixel alpha.
        # The image likely has per-pixel alpha. `set_alpha` on per-pixel alpha surface works as a multiplier?
        # Yes.
        # To be safe, we should restore alpha to 255 at end of render or use a copy.
        # Or better: don't modify the cached asset.
        
        img.set_alpha(255) # Restore alpha for other uses

    def _render_boss_hud(self, state: GameState) -> None:
        """渲染 Boss HUD：血条、计时器、符卡名、剩余阶段星星。"""
        # 查找场上的 Boss
        boss_hud = None
        for actor in state.actors:
            hud = actor.get(BossHudData)
            if hud and hud.visible:
                boss_hud = hud
                break

        if not boss_hud:
            return

        screen_w = state.width

        # ====== 绘制血条（顶部中央） ======
        bg = self.assets.get_image("ui_boss_hp_bg")
        fill = self.assets.get_image("ui_boss_hp_fill")
        frame = self.assets.get_image("ui_boss_hp_frame")
        
        bar_width = bg.get_width()
        bar_height = bg.get_height()
        bar_x = (screen_w - bar_width) // 2
        bar_y = 10

        # 1. Background
        self.screen.blit(bg, (bar_x, bar_y))

        # 2. Fill (根据血量比例裁剪)
        if boss_hud.hp_ratio > 0:
            fill_width = int(bar_width * boss_hud.hp_ratio)
            if fill_width > 0:
                self.screen.blit(fill, (bar_x, bar_y), (0, 0, fill_width, bar_height))

        # 3. Frame
        self.screen.blit(frame, (bar_x, bar_y))

        # ====== 绘制剩余阶段图标 ======
        life_icon = self.assets.get_image("ui_boss_life_icon")
        
        # 间距与位置
        spacing = 20
        star_x = bar_x + bar_width + 12
        star_cy = bar_y + bar_height // 2 - 6 # 再往上移一点点
        
        for i in range(boss_hud.phases_remaining):
            center_x = star_x + i * spacing
            rect = life_icon.get_rect(center=(center_x, star_cy))
            self.screen.blit(life_icon, rect)

        # Removed Timer and Boss Name from here (Moved to Sidebar)

        # Removed Spell Card Name/Bonus from here (Moved to Sidebar)

    def _draw_laser_glow(self, actor: Actor) -> None:
        """绘制激光发光层（到共享 glow_surface）。"""
        laser_state = actor.get(LaserState)
        pos = actor.get(Position)
        if not laser_state or not pos:
            return

        # 预热阶段不绘制辉光
        if laser_state.warmup_timer > 0:
            return

        segments = self._get_laser_segments_for_render(pos, laser_state)
        width = int(laser_state.width)
        
        # 颜色：半透明辉光 (使用激光颜色)
        r, g, b = laser_state.color
        glow_color = (r, g, b, 100)
        glow_width = width + 8
        
        for x1, y1, x2, y2 in segments:
            pygame.draw.line(
                self.glow_surface,
                glow_color,
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                glow_width
            )

    def _draw_laser(self, actor: Actor, pos: Position) -> None:
        """
        绘制激光主体。

        - 预热阶段：绘制细红线（预警）
        - 激活阶段：绘制不透明的白色光束核心
        """
        laser_state = actor.get(LaserState)
        if not laser_state:
            return

        # 获取激光线段
        segments = self._get_laser_segments_for_render(pos, laser_state)

        if laser_state.warmup_timer > 0:
            # 预热阶段：绘制细线预警 (使用激光颜色)
            for x1, y1, x2, y2 in segments:
                pygame.draw.line(
                    self.screen,
                    laser_state.color,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    2
                )
        else:
            # 激活阶段：绘制完整激光主体
            width = int(laser_state.width)

            # 绘制主体激光到屏幕（不透明）
            main_color = laser_state.color
            core_color = (255, 255, 255)  # 核心总是白色
            
            for x1, y1, x2, y2 in segments:
                # 激光外壳
                pygame.draw.line(
                    self.screen,
                    main_color,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    width
                )

                # 激光中心亮线
                pygame.draw.line(
                    self.screen,
                    core_color,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    max(2, width // 3)
                )

    def _get_laser_segments_for_render(
        self,
        laser_pos: Position,
        laser_state: LaserState
    ) -> list:
        """
        获取激光的线段列表用于渲染。

        与碰撞系统共用相同的逻辑，但这里是渲染专用。
        """
        segments = []

        if laser_state.laser_type == LaserType.STRAIGHT:
            # 直线激光
            rad = math.radians(laser_state.angle)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)

            end_x = laser_pos.x + laser_state.length * cos_a
            end_y = laser_pos.y + laser_state.length * sin_a
            segments.append((laser_pos.x, laser_pos.y, end_x, end_y))

        elif laser_state.laser_type == LaserType.SINE_WAVE:
            # 正弦波激光
            rad = math.radians(laser_state.angle)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)

            sample_count = max(int(laser_state.length / 20), 2)

            prev_x = laser_pos.x
            prev_y = laser_pos.y

            for i in range(1, sample_count + 1):
                t = i / sample_count
                dist = t * laser_state.length

                main_x = laser_pos.x + dist * cos_a
                main_y = laser_pos.y + dist * sin_a

                phase_deg = laser_state.sine_phase + (dist / laser_state.sine_wavelength) * 360
                offset = laser_state.sine_amplitude * math.sin(math.radians(phase_deg))

                perp_x = -sin_a * offset
                perp_y = cos_a * offset

                curr_x = main_x + perp_x
                curr_y = main_y + perp_y

                segments.append((prev_x, prev_y, curr_x, curr_y))
                prev_x, prev_y = curr_x, curr_y

        return segments

    def _draw_shockwaves(self, state: GameState) -> None:
        """绘制冲击波 VFX (Shockwave)。"""
        # Create a surface for alpha blending if not exists
        GAME_WIDTH = 480
        SCREEN_HEIGHT = state.height
        
        if not hasattr(self, 'vfx_surface') or self.vfx_surface.get_size() != (GAME_WIDTH, SCREEN_HEIGHT):
            self.vfx_surface = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Clear Vfx Surface
        self.vfx_surface.fill((0, 0, 0, 0))
        
        has_wave = False
        for actor in state.actors:
            wave = actor.get(Shockwave)
            if not wave:
                continue
            
            has_wave = True
            pos = actor.get(Position)
            if not pos: continue
            
            # Draw Circle
            # Color with Alpha
            color = wave.color
            alpha = int(wave.alpha)
            if alpha <= 0: continue
            
            rgba = (*color, alpha)
            
            try:
                pygame.draw.circle(
                    self.vfx_surface,
                    rgba,
                    (int(pos.x), int(pos.y)),
                    int(wave.radius),
                    wave.width
                )
            except (TypeError, ValueError):
                 # Fallback for old pygame
                 # Manually Draw on temp circle? Too slow?
                 # If color is just RGB, circle is opaque on transparent surface.
                 # Alpha comes from surface alpha if per-pixel alpha is set.
                 # Wait, drawing opaque circle on SRALPHA surface = opaque circle.
                 # If we want transparent circle, we must draw with RGBA color.
                 # Modern pygame supports this.
                 pass

        if has_wave:
             self.screen.blit(self.vfx_surface, (0, 0))

    def _render_dialogue(self, state: GameState) -> None:
        """Render dialogue overlay (portraits and text box)."""
        dialogue = state.dialogue
        if not dialogue.lines or dialogue.current_index >= len(dialogue.lines):
            return
            
        line = dialogue.lines[dialogue.current_index]
        GAME_WIDTH = 480
        GAME_HEIGHT = 640
        
        # 1. Overlay (Dim Background)
        # Assuming we want to dim the game behind
        # overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        # overlay.fill((0, 0, 0, 100))
        # self.screen.blit(overlay, (0, 0))
        
        # Global Alpha for Fade Out
        global_alpha = dialogue.alpha if dialogue.closing else 255
        
        # Helper to blit with alpha
        def blit_alpha(source, dest, position, alpha=255):
             if alpha == 255:
                 dest.blit(source, position)
                 return
             
             # Apply alpha
             # For per-pixel alpha surfaces (like PNGs), set_alpha works multiplicatively in SDL2/Pygame2
             # But let's be safe.
             temp = source.copy()
             temp.set_alpha(alpha)
             dest.blit(temp, position)

        # 2. Portraits
        
        if line.layout == "center":
            # Center Mode (Only active speaker shown in center)
            speaker = line.speaker
            variant = dialogue.variants.get(speaker)
            base_key = "portrait_player" if speaker == "player" else "portrait_boss"
            key = base_key
            
            if variant:
                var_key = f"{base_key}_{variant}"
                if self.assets.images.get(var_key):
                    key = var_key
            
            img = self.assets.images.get(key)
            if img:
                x = (GAME_WIDTH - img.get_width()) // 2
                y = 200
                blit_alpha(img, self.screen, (x, y), global_alpha)
                
        else:
            # Default Mode (Side by Side)
            # Left: Player (Ema)
            # Check persistent variant state
            p_variant = dialogue.variants.get("player")
            p_key = "portrait_player"
            if p_variant:
                 var_key = f"portrait_player_{p_variant}"
                 if self.assets.images.get(var_key):
                     p_key = var_key
            
            p_img = self.assets.images.get(p_key)
            if p_img:
                is_player_speaking = (line.speaker == "player")
                x = 40 
                y = 200
                
                img_to_draw = p_img
                if not is_player_speaking:
                    img_to_draw = p_img.copy()
                    img_to_draw.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
                
                blit_alpha(img_to_draw, self.screen, (x, y), global_alpha)

            # Right: Boss (Yuki)
            b_variant = dialogue.variants.get("boss")
            b_key = "portrait_boss"
            if b_variant:
                 var_key = f"portrait_boss_{b_variant}"
                 if self.assets.images.get(var_key):
                     b_key = var_key

            b_img = self.assets.images.get(b_key)
            if b_img:
                is_boss_speaking = (line.speaker == "boss")
                w = b_img.get_width()
                x = GAME_WIDTH - w - 10
                y = 200
                
                img_to_draw = b_img
                if not is_boss_speaking:
                    img_to_draw = b_img.copy()
                    img_to_draw.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
                
                blit_alpha(img_to_draw, self.screen, (x, y), global_alpha)
        
        # 3. Text Box
        box_h = 150
        box_y = GAME_HEIGHT - box_h - 20
        box_rect = pygame.Rect(20, box_y, GAME_WIDTH - 40, box_h)
        
        # Draw Box Background
        s = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 40, 200)) # Dark Blue
        pygame.draw.rect(s, (255, 255, 255), s.get_rect(), 2) # White Border
        # Apply global alpha to box
        # Box has 200 alpha. global_alpha 128 -> 100.
        # set_alpha typically overrides per-pixel alpha for blit? 
        # No, set_alpha(A) on per-pixel surface makes pixels (r,g,b, a*A/255).
        blit_alpha(s, self.screen, box_rect.topleft, global_alpha)
        
        # 4. Text
        font = self.assets.get_font(20)
        name_font = self.assets.get_font(28)
        
        # Try finding Name Image
        name_img_key = "name_ema" if line.speaker == "player" else "name_yuki"
        name_img = self.assets.images.get(name_img_key)
        
        if name_img:
            # Conditional offset for Yuki
            offset_x = 0
            if line.speaker == "boss":
                offset_x = -5
            
            blit_alpha(name_img, self.screen, (box_rect.x + offset_x, box_rect.y - 25), global_alpha)
        else:
            name_color = (100, 200, 255) if line.speaker == "player" else (255, 100, 100)
            name_surf = name_font.render(line.name, True, name_color)
            blit_alpha(name_surf, self.screen, (box_rect.x + 20, box_rect.y + 10), global_alpha)
        
        # Content
        text_color = (255, 255, 255)
        words = line.text.split('\n')
        line_spacing = 30
        
        text_start_y = box_rect.y + 60 
        curr_y = text_start_y
        
        for w in words:
            t_surf = font.render(w, True, text_color)
            blit_alpha(t_surf, self.screen, (box_rect.x + 30, curr_y), global_alpha)
            curr_y += line_spacing
            
        # "Press Z" indicator (Only if not closing)
        if not dialogue.closing and pygame.time.get_ticks() % 1000 < 500:
            hint = font.render("▼", True, (255, 255, 0))
            self.screen.blit(hint, (box_rect.right - 40, box_rect.bottom - 30))
