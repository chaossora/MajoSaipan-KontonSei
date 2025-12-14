"""
主菜单场景：游戏标题画面和菜单选项。
"""
from __future__ import annotations

import math
import pygame
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from view.assets import Assets


class MenuState(Enum):
    """菜单状态"""
    TITLE = auto()
    CHARACTER_SELECT = auto()
    OPTIONS = auto()


class MenuResult(Enum):
    """菜单返回结果"""
    NONE = auto()
    START_GAME = auto()
    EXIT = auto()


class MainMenu:
    """主菜单场景"""

    def __init__(self, screen: pygame.Surface, assets: Assets) -> None:
        self.screen = screen
        self.assets = assets
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # 菜单状态
        self.state = MenuState.TITLE
        self.selected_index = 0
        self.time = 0.0
        
        # 菜单选项
        self.menu_items = [
            "开始游戏",
            "退出游戏",
        ]
        
        # 角色选择
        self.character_index = 0
        self.selected_character_id = None
        
        # 字体
        try:
            self.font_title = pygame.font.Font(assets.font_path, 48)
            self.font_subtitle = pygame.font.Font(assets.font_path, 24)
            self.font_menu = pygame.font.Font(assets.font_path, 36) # 28 -> 36
            self.font_small = pygame.font.Font(assets.font_path, 18)
        except (FileNotFoundError, pygame.error):
            self.font_title = pygame.font.Font(None, 64)
            self.font_subtitle = pygame.font.Font(None, 32)
            self.font_menu = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 24)
        
        # 输入冷却
        self.input_cooldown = 0.0
        
        # 星星粒子背景
        self.stars = self._generate_stars(100)
        
        # 生成模糊背景 (用于角色选择界面)
        self.bg_blurred = None
        bg_img = self.assets.images.get("menu_bg")
        if bg_img:
             # Downscale for blur effect
             w, h = bg_img.get_size()
             small = pygame.transform.smoothscale(bg_img, (w // 10, h // 10))
             blurred = pygame.transform.smoothscale(small, (w, h))
             
             # Apply dark overlay (变暗)
             overlay = pygame.Surface((w, h), pygame.SRCALPHA)
             overlay.fill((0, 0, 0, 100)) # 100/255 opacity black
             blurred.blit(overlay, (0, 0))
             
             self.bg_blurred = blurred
             
        # 转场变量
        self.fade_alpha = 255.0 # Start with black fade-in
        self.fade_state = "IN"  # IN (255->0), OUT (0->255), NONE
        self.next_menu_state = None
        self.next_result = None
        
        # Split Screen Ratio (0.0 - 1.0), 0.5 = Center
        self.split_ratio = 0.5
    
    def _generate_stars(self, count: int) -> list[dict]:
        """生成星星粒子"""
        import random
        stars = []
        for _ in range(count):
            stars.append({
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height),
                "speed": random.uniform(20, 80),
                "size": random.randint(1, 3),
                "brightness": random.randint(100, 255),
            })
        return stars
    
    def _update_stars(self, dt: float) -> None:
        """更新星星粒子"""
        for star in self.stars:
            star["y"] += star["speed"] * dt
            if star["y"] > self.height:
                star["y"] = 0
                star["x"] = __import__("random").randint(0, self.width)
    
    def _draw_stars(self) -> None:
        """绘制星星粒子"""
        for star in self.stars:
            brightness = star["brightness"]
            color = (brightness, brightness, brightness)
            pygame.draw.circle(
                self.screen, 
                color, 
                (int(star["x"]), int(star["y"])), 
                star["size"]
            )
    
    def _draw_text_with_shadow(
        self, 
        text: str, 
        font: pygame.font.Font, 
        color: tuple[int, int, int], 
        x: int, 
        y: int,
        center: bool = False,
        shadow_offset: int = 2,
        target_surface: pygame.Surface = None
    ) -> None:
        """绘制带阴影的文字"""
        surf = target_surface if target_surface else self.screen
        
        shadow_color = (0, 0, 0)
        
        # 阴影
        shadow_surf = font.render(text, True, shadow_color)
        main_surf = font.render(text, True, color)
        
        if center:
            main_rect = main_surf.get_rect(center=(x, y))
            shadow_rect = shadow_surf.get_rect(center=(x + shadow_offset, y + shadow_offset))
        else:
            main_rect = main_surf.get_rect(topleft=(x, y))
            shadow_rect = shadow_surf.get_rect(topleft=(x + shadow_offset, y + shadow_offset))
        
        surf.blit(shadow_surf, shadow_rect)
        surf.blit(main_surf, main_rect)
    
    def _draw_title_screen(self) -> None:
        """绘制标题画面"""
        # 标题
        title_y = 120
        wave = math.sin(self.time * 2) * 5
        
        # 如果有带 Logo 的背景图，跳过标题和副标题绘制
        if "menu_bg" not in self.assets.images:
            # 游戏标题
            logo_img = self.assets.images.get("menu_logo")
            if logo_img:
                # Draw Logo Image
                logo_rect = logo_img.get_rect(center=(self.width // 2, int(title_y + wave)))
                self.screen.blit(logo_img, logo_rect)
            else:
                self._draw_text_with_shadow(
                    "MajoSaipanKontonSei",
                    self.font_title,
                    (255, 220, 100),
                    self.width // 2,
                    int(title_y + wave),
                    center=True,
                    shadow_offset=3
                )
            
            # 副标题
            self._draw_text_with_shadow(
                "~ Chaos Reign ~",
                self.font_subtitle,
                (200, 180, 255),
                self.width // 2,
                title_y + 60,
                center=True
            )
        
        # 菜单选项
        menu_start_y = 400 # 300 -> 400
        menu_spacing = 60  # 50 -> 60 (Spacing slightly increased for bigger font)
        
        for i, item in enumerate(self.menu_items):
            is_selected = (i == self.selected_index)
            
            # 选中效果
            if is_selected:
                # 闪烁高亮
                alpha = int(180 + 75 * math.sin(self.time * 6))
                color = (255, 255, alpha)
                # 箭头指示器
                arrow_x = self.width // 2 - 100
                arrow_wave = math.sin(self.time * 8) * 5
                
                cursor_img = self.assets.images.get("menu_cursor")
                if cursor_img:
                    # Image Cursor
                    cursor_rect = cursor_img.get_rect(center=(int(arrow_x + arrow_wave), menu_start_y + i * menu_spacing))
                    self.screen.blit(cursor_img, cursor_rect)
                else:
                    self._draw_text_with_shadow(
                        "▶",
                        self.font_menu,
                        (255, 100, 100),
                        int(arrow_x + arrow_wave),
                        menu_start_y + i * menu_spacing,
                        center=True
                    )
            else:
                color = (180, 180, 180)
            
            self._draw_text_with_shadow(
                item,
                self.font_menu,
                color,
                self.width // 2,
                menu_start_y + i * menu_spacing,
                center=True
            )
        
        # 底部提示
        hint_y = self.height - 60
        self._draw_text_with_shadow(
            "↑↓ 选择  Z 确认  X 返回",
            self.font_small,
            (150, 150, 150),
            self.width // 2,
            hint_y,
            center=True
        )
        
        # 版权信息
        self._draw_text_with_shadow(
            "© 2024 Touhou KontonSei Project",
            self.font_small,
            (100, 100, 100),
            self.width // 2,
            hint_y + 30,
            center=True
        )
    
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        """简单的多行文本换行逻辑"""
        lines = []
        current_line = ""
        for char in text:
            test_line = current_line + char
            # 检查宽度
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
        return lines

    def _draw_character_select(self) -> None:
        """绘制双角色对决选择画面 (带缩放和边框)"""
        from model.character import get_all_characters
        characters = get_all_characters()
        if not characters: return

        # ==========================
        # 1. 绘制标题 (Title)
        # ==========================
        title_img = self.assets.images.get("select_title")
        if title_img:
            # Scale up (1.25x)
            w, h = title_img.get_size()
            new_size = (int(w * 1.25), int(h * 1.25))
            title_scaled = pygame.transform.smoothscale(title_img, new_size)
            
            # Draw centered at Y=50
            rect = title_scaled.get_rect(center=(self.width // 2, 50))
            self.screen.blit(title_scaled, rect)
        else:
            self._draw_text_with_shadow("CHARACTER SELECT", self.font_title, (255, 220, 100), self.width // 2, 30, center=True)

        # ==========================
        # 2. 定义内容区域 (Content Area)
        # ==========================
        margin_x = 55
        margin_top = 130
        margin_bot = 60
        layout_w = self.width - margin_x * 2
        layout_h = self.height - margin_top - margin_bot
        layout_rect = pygame.Rect(margin_x, margin_top, layout_w, layout_h)
        
        # Content Inner Rect (Offset down by 25px relative to frame)
        padding = 15
        offset_y = 25
        content_rect = pygame.Rect(
            layout_rect.left + padding,
            layout_rect.top + padding + offset_y,
            layout_w - padding * 2,
            layout_h - padding * 2
        )
        content_w, content_h = content_rect.size
        
        # 创建内容表面 (用于剪裁和绘图)
        content_surf = pygame.Surface((content_w, content_h), pygame.SRCALPHA)
        
        # ==========================
        # 3. 绘制角色 (Split Logic)
        # ==========================
        # 计算相对坐标
        split_cx = content_w * self.split_ratio
        tilt = 60
        top_x = split_cx + tilt
        bot_x = split_cx - tilt
        
        surf_left = pygame.Surface((content_w, content_h), pygame.SRCALPHA)
        surf_right = pygame.Surface((content_w, content_h), pygame.SRCALPHA)
        
        active_idx = self.character_index
        
        # Determine keys
        if active_idx == 0:
            key_ema = "portrait_ema"
            key_hero = "portrait_hero_blur"
        else:
            key_ema = "portrait_ema_blur"
            key_hero = "portrait_hero"
            
        # Draw Left (Ema)
        p_reimu = self.assets.images.get(key_ema)
        if p_reimu:
            # Auto-Scale
            rw, rh = p_reimu.get_size()
            target_h = content_h + 20
            if abs(rh - target_h) > 5:
                ratio = target_h / rh
                new_w = int(rw * ratio)
                new_h = int(rh * ratio)
                p_reimu = pygame.transform.smoothscale(p_reimu, (new_w, new_h))
                
            # 调整位置 (相对于 content_surf)
            r_rect = p_reimu.get_rect(midbottom=(content_w * 0.25, content_h + 10))
            surf_left.blit(p_reimu, r_rect)
            
        # Draw Right (Hero)
        p_marisa = self.assets.images.get(key_hero)
        if p_marisa:
            mw, mh = p_marisa.get_size()
            target_h = content_h + 20
            if abs(mh - target_h) > 5:
                ratio = target_h / mh
                new_w = int(mw * ratio)
                new_h = int(mh * ratio)
                p_marisa = pygame.transform.smoothscale(p_marisa, (new_w, new_h))

            m_rect = p_marisa.get_rect(midbottom=(content_w * 0.75, content_h + 10))
            surf_right.blit(p_marisa, m_rect)
            
        # Darken Inactive Layer
        if active_idx == 1: # Right Active -> Darken Left
            surf_left.fill((100, 100, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
        else: # Left Active -> Darken Right
            surf_right.fill((100, 100, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)
            
        # Apply Masks (Relative)
        mask_left = pygame.Surface((content_w, content_h), pygame.SRCALPHA)
        pygame.draw.polygon(mask_left, (255, 255, 255), [(0,0), (top_x, 0), (bot_x, content_h), (0, content_h)])
        surf_left.blit(mask_left, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        
        mask_right = pygame.Surface((content_w, content_h), pygame.SRCALPHA)
        pygame.draw.polygon(mask_right, (255, 255, 255), [(top_x, 0), (content_w, 0), (content_w, content_h), (bot_x, content_h)])
        surf_right.blit(mask_right, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Composite
        content_surf.blit(surf_left, (0,0))
        content_surf.blit(surf_right, (0,0))
        
        # Divider Line
        pygame.draw.line(content_surf, (255, 255, 200), (top_x, 0), (bot_x, content_h), 4)
        
        # ==========================
        # 4. 绘制信息文字 (On Content Surf)
        # ==========================
        active_char = characters[active_idx]
        text_cx = content_w * 0.25 if active_idx == 0 else content_w * 0.70
        info_y = content_h * 0.65
        
        # Determine Text Colors
        if active_idx == 0: # Ema (Pink)
            name_color = (255, 105, 180) # HotPink
            desc_color = (255, 192, 203) # Pink (Lighter)
        else: # Hero (Red)
            name_color = (220, 20, 60) # Crimson
            desc_color = (255, 160, 160) # Lighter Red
            
        # Name
        self._draw_text_with_shadow(active_char.name, self.font_title, name_color, text_cx, info_y, center=True, target_surface=content_surf)
        
        # Desc
        wrapped_lines = self._wrap_text(active_char.description, self.font_small, 260)
        desc_y = info_y + 50
        for i, line in enumerate(wrapped_lines):
            self._draw_text_with_shadow(line, self.font_small, desc_color, text_cx, desc_y + i * 22, center=True, target_surface=content_surf)
            


        # ==========================
        # 5. 渲染到屏幕 (Render to Screen)
        # ==========================
        self.screen.blit(content_surf, content_rect.topleft)
        
        # ==========================
        # 6. 绘制边框 (Frame)
        # ==========================
        frame = self.assets.images.get("select_frame")
        if frame:
            # Draw frame centered on the layout rect
            f_rect = frame.get_rect(center=layout_rect.center)
            self.screen.blit(frame, f_rect)
        else:
            # Fallback Border
            pygame.draw.rect(self.screen, (180, 160, 100), layout_rect, 3, border_radius=4)
    
    def handle_input(self, dt: float) -> MenuResult:
        """处理输入，返回菜单结果"""
        self.input_cooldown -= dt
        if self.input_cooldown > 0:
            return MenuResult.NONE
        
        keys = pygame.key.get_pressed()
        
        if self.state == MenuState.TITLE:
            # 标题菜单
            if keys[pygame.K_UP]:
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
                self.input_cooldown = 0.15
            elif keys[pygame.K_DOWN]:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
                self.input_cooldown = 0.15
            elif keys[pygame.K_z] or keys[pygame.K_RETURN]:
                self.input_cooldown = 0.2
                if self.selected_index == 0:
                    # 开始游戏 -> 触发转场 -> 角色选择
                    self.fade_state = "OUT"
                    self.next_menu_state = MenuState.CHARACTER_SELECT
                    self.character_index = 0
                    return MenuResult.NONE
                elif self.selected_index == 1:
                    # 退出
                    self.fade_state = "OUT"
                    self.next_result = MenuResult.EXIT
                    return MenuResult.NONE
            elif keys[pygame.K_ESCAPE]:
                self.fade_state = "OUT"
                self.next_result = MenuResult.EXIT
                return MenuResult.NONE
        
        elif self.state == MenuState.CHARACTER_SELECT:
            from model.character import get_all_characters, CharacterId
            characters = get_all_characters()
            
            if keys[pygame.K_LEFT]:
                self.character_index = (self.character_index - 1) % len(characters)
                self.input_cooldown = 0.15
            elif keys[pygame.K_RIGHT]:
                self.character_index = (self.character_index + 1) % len(characters)
                self.input_cooldown = 0.15
            elif keys[pygame.K_z] or keys[pygame.K_RETURN]:
                # 选中角色并开始游戏 -> 触发转场
                self.selected_character_id = list(CharacterId)[self.character_index]
                self.input_cooldown = 0.2
                self.fade_state = "OUT"
                self.next_result = MenuResult.START_GAME
                return MenuResult.NONE
            elif keys[pygame.K_x] or keys[pygame.K_ESCAPE]:
                # 返回标题 -> 触发转场
                self.fade_state = "OUT"
                self.next_menu_state = MenuState.TITLE
                self.input_cooldown = 0.2
                return MenuResult.NONE
        
        return MenuResult.NONE
    
    def update(self, dt: float) -> MenuResult:
        """更新菜单状态"""
        self.time += dt
        
        # 转场逻辑
        if self.fade_state == "IN":
            self.fade_alpha -= 800 * dt  # Fade In Speed (Slower)
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fade_state = "NONE"
        elif self.fade_state == "OUT":
            self.fade_alpha += 1200 * dt  # Fade Out Speed (Fastish)
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                # 执行切换
                if self.next_result:
                    return self.next_result
                if self.next_menu_state:
                    self.state = self.next_menu_state
                    self.next_menu_state = None
                    self.fade_state = "IN"
                    self.input_cooldown = 0.2
                    
                    # Reset Split Ratio for Character Select
                    if self.state == MenuState.CHARACTER_SELECT:
                        self.split_ratio = 0.5
        
        # 只有在没有转场时才处理输入
        if self.fade_state == "NONE":
            result = self.handle_input(dt)
            if result != MenuResult.NONE:
                return result
        elif self.input_cooldown > 0:
            self.input_cooldown -= dt
            
        # Dual-Split Animation (Only animate when fully visible)
        if self.state == MenuState.CHARACTER_SELECT and self.fade_state == "NONE":
            target_ratio = 0.65 if self.character_index == 0 else 0.35
            diff = target_ratio - self.split_ratio
            self.split_ratio += diff * 3.0 * dt
            
        self._update_stars(dt)
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return MenuResult.EXIT
        
        return MenuResult.NONE
    
    def render(self) -> None:
        """渲染菜单"""
        bg_drawn = False
        
        # Character Select uses Blurred BG
        if self.state == MenuState.CHARACTER_SELECT and self.bg_blurred:
            self.screen.blit(self.bg_blurred, (0, 0))
            bg_drawn = True
        else:
            bg_img = self.assets.images.get("menu_bg")
            if bg_img:
                self.screen.blit(bg_img, (0, 0))
                bg_drawn = True
        
        if not bg_drawn:
            self.screen.fill((15, 10, 30))
        
        # 星星粒子
        self._draw_stars()
        
        # 根据状态绘制
        if self.state == MenuState.TITLE:
            self._draw_title_screen()
        elif self.state == MenuState.CHARACTER_SELECT:
            self._draw_character_select()
            
        # 转场遮罩
        if self.fade_alpha > 1:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(min(255, self.fade_alpha))))
            self.screen.blit(overlay, (0, 0))
        
        pygame.display.flip()
    
    def run(self) -> tuple[MenuResult, "CharacterId | None"]:
        """运行菜单循环，返回结果和选中的角色 ID"""
        from model.character import CharacterId
        
        clock = pygame.time.Clock()
        
        while True:
            dt = clock.tick(60) / 1000.0
            
            result = self.update(dt)
            
            if result == MenuResult.START_GAME:
                # 如果没有在角色选择中选择角色，使用默认
                if self.selected_character_id is None:
                    self.selected_character_id = list(CharacterId)[0]
                return (result, self.selected_character_id)
            elif result == MenuResult.EXIT:
                return (result, None)
            
            self.render()
