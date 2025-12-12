from __future__ import annotations

import pygame

from model.game_state import GameState
from model.actor import Actor
from model.components import (
    Position, SpriteInfo, RenderHint, HudData, PlayerTag,
    BossHudData, OptionState, OptionConfig,
    PlayerBulletKindTag, PlayerBulletKind,
    EnemyKindTag, EnemyKind,
    EnemyBulletKindTag, EnemyBulletKind,
)
from model.game_config import CollectConfig


# ====== 玩家子弹类型 → 精灵映射表 ======
# View 层统一管理子弹贴图配置
PLAYER_BULLET_SPRITES: dict[PlayerBulletKind, tuple[str, int, int]] = {
    # 类型: (精灵名, X偏移, Y偏移)
    PlayerBulletKind.MAIN_NORMAL: ("player_bullet_main", -4, -8),
    PlayerBulletKind.MAIN_ENHANCED: ("player_bullet_main_enhanced", -4, -8),
    PlayerBulletKind.OPTION_NORMAL: ("player_bullet_option", -4, -8),
    PlayerBulletKind.OPTION_ENHANCED: ("player_bullet_option_enhanced", -4, -8),
}
# 默认子弹精灵（未知类型时的回退）
DEFAULT_BULLET_SPRITE = ("player_bullet_basic", -4, -8)


# ====== 敌人类型 → 精灵映射表 ======
ENEMY_SPRITES: dict[EnemyKind, tuple[str, int, int]] = {
    # 类型: (精灵名, X偏移, Y偏移)
    EnemyKind.FAIRY_SMALL: ("enemy_fairy_small", -16, -16),
    EnemyKind.FAIRY_LARGE: ("enemy_fairy_large", -20, -20),
    EnemyKind.MIDBOSS: ("enemy_midboss", -32, -32),
    EnemyKind.BOSS: ("enemy_boss", -32, -32),
}
DEFAULT_ENEMY_SPRITE = ("enemy_basic", -16, -16)


# ====== 敌人子弹类型 → 精灵映射表 ======
ENEMY_BULLET_SPRITES: dict[EnemyBulletKind, tuple[str, int, int]] = {
    # 类型: (精灵名, X偏移, Y偏移)
    EnemyBulletKind.BASIC: ("enemy_bullet_basic", -4, -4),
}
DEFAULT_ENEMY_BULLET_SPRITE = ("enemy_bullet_basic", -4, -4)


class Renderer:
    """渲染器：从游戏状态（只读）渲染精灵和 HUD。"""

    def __init__(self, screen: pygame.Surface, assets) -> None:
        self.screen = screen
        self.assets = assets
        self.font_small = pygame.font.Font(None, 18)

    def render(self, state: GameState) -> None:
        """渲染一帧画面"""
        self.screen.fill((0, 0, 0))

        # 绘制所有游戏对象
        for actor in state.actors:
            self._draw_actor(actor)

        # 绘制子机（在玩家精灵之上）
        self._render_options(state)

        # 绘制 PoC 线
        self._draw_poc_line(state)

        # 绘制 Boss HUD
        self._render_boss_hud(state)

        # 绘制玩家 HUD
        self._render_hud(state)

        pygame.display.flip()

    def _draw_actor(self, actor: Actor) -> None:
        """绘制实体精灵和可选的渲染提示（如碰撞框）。"""
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
            x = int(pos.x + ox)
            y = int(pos.y + oy)
            self.screen.blit(image, (x, y))
            return

        # 检查是否是敌人子弹（通过类型查表渲染）
        enemy_bullet_kind_tag = actor.get(EnemyBulletKindTag)
        if enemy_bullet_kind_tag:
            sprite_name, ox, oy = ENEMY_BULLET_SPRITES.get(
                enemy_bullet_kind_tag.kind, DEFAULT_ENEMY_BULLET_SPRITE
            )
            image = self.assets.get_image(sprite_name)
            x = int(pos.x + ox)
            y = int(pos.y + oy)
            self.screen.blit(image, (x, y))
            return

        # 检查是否是敌人（通过类型查表渲染）
        enemy_kind_tag = actor.get(EnemyKindTag)
        if enemy_kind_tag:
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

        image = self.assets.get_image(sprite.name)
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

        x, y, line_h = 10, 10, 20
        for text in lines:
            surf = self.font_small.render(text, True, (255, 255, 255))
            self.screen.blit(surf, (x, y))
            y += line_h

        # 绘制擦弹能量条
        self._render_graze_energy_bar(state, hud, y)

    def _render_graze_energy_bar(self, state: GameState, hud: HudData, start_y: int) -> None:
        """绘制擦弹能量条。"""
        bar_x = 10
        bar_y = start_y + 5
        bar_width = 120
        bar_height = 10

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

        # 绘制标签
        if hud.is_enhanced:
            label = "ENHANCED!"
            label_color = (255, 220, 100)
        else:
            percent = int(100 * hud.graze_energy / hud.max_graze_energy) if hud.max_graze_energy > 0 else 0
            label = f"ENERGY {percent}%"
            label_color = (200, 200, 200)

        label_surf = self.font_small.render(label, True, label_color)
        self.screen.blit(label_surf, (bar_x + bar_width + 8, bar_y - 1))

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

        # 计算精灵偏移（居中绘制）
        offset_x = -option_img.get_width() // 2
        offset_y = -option_img.get_height() // 2

        # 绘制所有激活的子机
        for i in range(option_state.active_count):
            if i >= len(option_state.current_positions):
                continue

            pos = option_state.current_positions[i]
            x = int(pos[0]) + offset_x
            y = int(pos[1]) + offset_y
            self.screen.blit(option_img, (x, y))

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

        screen_w = self.screen.get_width()

        # ====== 绘制血条（顶部中央） ======
        bar_width = 280
        bar_height = 8
        bar_x = (screen_w - bar_width) // 2
        bar_y = 24

        # 绘制背景
        pygame.draw.rect(
            self.screen,
            (60, 60, 60),
            (bar_x, bar_y, bar_width, bar_height),
        )
        # 绘制血量填充
        fill_width = int(bar_width * boss_hud.hp_ratio)
        bar_color = (255, 100, 100) if not boss_hud.is_spell_card else (255, 180, 100)
        pygame.draw.rect(
            self.screen,
            bar_color,
            (bar_x, bar_y, fill_width, bar_height),
        )
        # 边框
        pygame.draw.rect(
            self.screen,
            (200, 200, 200),
            (bar_x, bar_y, bar_width, bar_height),
            1,
        )

        # ====== 绘制剩余阶段星星 ======
        star_x = bar_x + bar_width + 8
        for i in range(boss_hud.phases_remaining):
            pygame.draw.circle(
                self.screen,
                (255, 255, 200),
                (star_x + i * 14, bar_y + 4),
                5,
            )
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (star_x + i * 14, bar_y + 4),
                5,
                1,
            )

        # ====== 绘制计时器（血条左侧） ======
        timer_text = f"{int(boss_hud.timer_seconds):02d}"
        timer_surf = self.font_small.render(timer_text, True, (255, 255, 255))
        self.screen.blit(timer_surf, (bar_x - 28, bar_y - 2))

        # ====== 绘制 Boss 名称 ======
        name_surf = self.font_small.render(boss_hud.boss_name, True, (255, 255, 255))
        self.screen.blit(name_surf, (bar_x, bar_y - 16))

        # ====== 绘制符卡名（右上角） ======
        if boss_hud.is_spell_card and boss_hud.spell_name:
            # 符卡名颜色：有奖励资格时为亮色，无则为暗色
            spell_color = (255, 200, 200) if boss_hud.spell_bonus_available else (150, 150, 150)
            spell_surf = self.font_small.render(boss_hud.spell_name, True, spell_color)
            spell_x = screen_w - spell_surf.get_width() - 10
            self.screen.blit(spell_surf, (spell_x, 50))

            # 绘制符卡奖励分数
            if boss_hud.spell_bonus_available:
                bonus_text = f"Bonus: {boss_hud.spell_bonus}"
                bonus_surf = self.font_small.render(bonus_text, True, (200, 200, 150))
                self.screen.blit(bonus_surf, (spell_x, 68))
