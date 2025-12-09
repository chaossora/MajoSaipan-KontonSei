from __future__ import annotations

import pygame

from model.game_state import GameState
from model.actor import Actor
from model.components import Position, SpriteInfo, RenderHint, HudData, PlayerTag
from model.game_config import CollectConfig


class Renderer:
    """渲染器：从模型状态（只读）渲染精灵和 HUD。"""

    def __init__(self, screen: pygame.Surface, assets) -> None:
        self.screen = screen
        self.assets = assets
        self.font_small = pygame.font.Font(None, 18)

    def render(self, state: GameState) -> None:
        self.screen.fill((0, 0, 0))

        # 绘制所有游戏对象
        for actor in state.actors:
            self._draw_actor(actor)

        # PoC 线
        self._draw_poc_line(state)

        # HUD
        self._render_hud(state)

        pygame.display.flip()

    def _draw_actor(self, actor: Actor) -> None:
        """绘制精灵和可选的渲染提示。"""
        pos = actor.get(Position)
        sprite = actor.get(SpriteInfo)
        if not (pos and sprite):
            return

        # 检查是否可见（闪烁效果）
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
        """绘制点收集（Point-of-Collection）线。"""
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
        """使用 HudData 和 EntityStats 绘制 HUD。"""
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

        # 调试统计
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
