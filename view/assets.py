"""
资源管理模块：加载和管理游戏精灵图。
"""
from __future__ import annotations

import pygame


class Assets:
    """
    资源管理器：目前使用纯色形状代替实际图片。
    """

    def __init__(self) -> None:
        self.images: dict[str, pygame.Surface] = {}
        self.player_frames: dict[str, list[pygame.Surface]] = {}
        self.enemy_sprites: dict[str, dict[str, list[pygame.Surface]]] = {}
        self.vfx: dict[str, list[pygame.Surface]] = {}
        self.sfx: dict[str, pygame.mixer.Sound] = {}
        self.font_path = "assets/fonts/OPPOSans-Bold.ttf"
        self.fonts: dict[int, pygame.font.Font] = {}

    def load(self) -> None:
        # Load Character Sprite Sheet
        try:
            # Correct path verified: assets/sprites/characters/ema.png
            sheet = pygame.image.load("assets/sprites/characters/ema.png").convert_alpha()
            # Dimensions: 2784 x 1536
            # Rows: 3 (Idle, Left, Right)
            # Cols: 8
            # Cell Size: 348 x 512
            
            cell_width = 2784 // 8
            cell_height = 1536 // 3
            
            # Scale down to reasonable game size
            # height 512 -> 72 (approx 1/7.1) - Smaller size
            target_height = 72
            scale_ratio = target_height / cell_height
            target_width = int(cell_width * scale_ratio)

            frames = []
            for row in range(3):
                row_frames = []
                for col in range(8):
                    rect = pygame.Rect(col * cell_width, row * cell_height, cell_width, cell_height)
                    sub_surface = sheet.subsurface(rect)
                    scaled = pygame.transform.smoothscale(sub_surface, (target_width, target_height))
                    row_frames.append(scaled)
                frames.append(row_frames)

            # Store frames
            # Row 0: Idle (Forward), Row 1: Left, Row 2: Right
            
            # Use the first frame of Idle as default static image
            self.images["player_default"] = frames[0][0]
            self.images["player_reimu"] = frames[0][0]
            self.images["player_marisa"] = frames[0][0]
            
            # Store animation frames for renderer to use
            self.player_frames = {
                "idle": frames[0],
                "left": frames[1],
                "right": frames[2]
            }
            print(f"Loaded sprite sheet: ema.png ({target_width}x{target_height} per frame)")
            
        except (FileNotFoundError, pygame.error):
            print("Warning: Sprite sheet assets/sprites/characters/ema.png not found. Using placeholders.")
            # player_default placeholder
            player_img = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(player_img, (0, 200, 255), (16, 16), 10)
            self.images["player_default"] = player_img

            # player_reimu placeholder
            reimu = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(reimu, (255, 80, 120), (16, 16), 10)
            pygame.draw.circle(reimu, (255, 200, 220), (16, 12), 6)
            self.images["player_reimu"] = reimu

            # player_marisa placeholder
            marisa = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(marisa, (255, 215, 0), (16, 16), 10)
            pygame.draw.circle(marisa, (255, 255, 180), (16, 12), 6)
            self.images["player_marisa"] = marisa

        # 基础敌人精灵
        enemy_img = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(enemy_img, (255, 80, 80), (16, 16), 12)
        self.images["enemy_basic"] = enemy_img

        # 小妖精精灵
        fairy_small = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(fairy_small, (255, 140, 200), (16, 16), 10)
        pygame.draw.circle(fairy_small, (255, 220, 240), (16, 12), 6)
        self.images["enemy_fairy_small"] = fairy_small

        # 大妖精精灵
        fairy_large = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(fairy_large, (255, 120, 160), (20, 20), 14)
        pygame.draw.circle(fairy_large, (255, 215, 235), (20, 16), 8)
        self.images["enemy_fairy_large"] = fairy_large

        # 中 Boss 精灵
        midboss = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(midboss, (255, 100, 120), (32, 32), 24)
        pygame.draw.circle(midboss, (255, 200, 210), (32, 28), 14)
        pygame.draw.circle(midboss, (255, 255, 255), (32, 24), 6)
        self.images["enemy_midboss"] = midboss

        # 第一关 Boss 精灵
        boss1 = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(boss1, (180, 80, 200), (32, 32), 28)  # 紫色主体
        pygame.draw.circle(boss1, (220, 160, 240), (32, 26), 16)  # 亮色上半
        pygame.draw.circle(boss1, (255, 200, 255), (32, 22), 8)   # 高光
        # 装饰翅膀
        pygame.draw.ellipse(boss1, (200, 120, 220, 180), (4, 20, 16, 24))
        pygame.draw.ellipse(boss1, (200, 120, 220, 180), (44, 20, 16, 24))
        self.images["boss_stage1"] = boss1

        # 残机道具精灵
        life_img = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(life_img, (255, 100, 150), (8, 8), 7)
        pygame.draw.circle(life_img, (255, 200, 220), (8, 6), 4)
        self.images["item_life"] = life_img

        # 炸弹道具精灵
        bomb_item = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(bomb_item, (100, 200, 100), (8, 8), 7)
        pygame.draw.circle(bomb_item, (180, 255, 180), (8, 6), 4)
        self.images["item_bomb"] = bomb_item

        # ====== Player Bullets ======
        
        # 1. Normal Bullet (Shared)
        try:
            # assets/sprites/bullets/bullet_normal.png
            # 原始方向：左(底) -> 右(头)。
            # 顺时针旋转 -90 或 逆时针 90 得到：下(底) -> 上(头)。
            bn_src = pygame.image.load("assets/sprites/bullets/bullet_normal.png").convert_alpha()
            bn_rot = pygame.transform.rotate(bn_src, 90)
            # Increase size to 20x40
            bn = pygame.transform.smoothscale(bn_rot, (20, 40))
            self.images["player_bullet_normal"] = bn
        except (FileNotFoundError, pygame.error):
            # Fallback
            pb = pygame.Surface((20, 40), pygame.SRCALPHA)
            pygame.draw.rect(pb, (255, 255, 0), (5, 0, 10, 40))
            self.images["player_bullet_normal"] = pb

        # 2. Enhanced Bullet (Shared)
        try:
            # assets/sprites/bullets/bullet_enhanced.png
            be_src = pygame.image.load("assets/sprites/bullets/bullet_enhanced.png").convert_alpha()
            be_rot = pygame.transform.rotate(be_src, 90)
            # Increase size to 64x128
            be = pygame.transform.smoothscale(be_rot, (64, 128))
            self.images["player_bullet_enhanced"] = be
        except (FileNotFoundError, pygame.error):
            be = pygame.Surface((64, 128), pygame.SRCALPHA)
            pygame.draw.rect(be, (255, 200, 50), (16, 0, 32, 128))
            self.images["player_bullet_enhanced"] = be

        # ====== Background ======
        try:
            bg_src = pygame.image.load("assets/sprites/backgrounds/background.png").convert_alpha()
            # Scale to screen size 480x640
            bg = pygame.transform.smoothscale(bg_src, (480, 640))
            self.images["background"] = bg
        except (FileNotFoundError, pygame.error):
            # Fallback: Dark blue gradient or simple rect
            bg = pygame.Surface((480, 640))
            bg.fill((20, 20, 50))
            self.images["background"] = bg

        # ====== Sidebar Background ======
        try:
            sb_src = pygame.image.load("assets/ui/sidebar_bg.png").convert_alpha()
            # Scale to 240x640
            sb = pygame.transform.smoothscale(sb_src, (240, 640))
            self.images["ui_sidebar_bg"] = sb
        except (FileNotFoundError, pygame.error):
            sb_surf = pygame.Surface((240, 640))
            sb_surf.fill((40, 40, 60))
            # Optional: Pattern
            pygame.draw.rect(sb_surf, (30, 30, 50), (10, 10, 220, 620), 2)
            self.images["ui_sidebar_bg"] = sb_surf

        # ====== UI Icons ======
        try:
            # Life Active
            life_act = pygame.image.load("assets/ui/icon_life_active.png").convert_alpha()
            life_act = pygame.transform.smoothscale(life_act, (32, 32))
            self.images["icon_life_active"] = life_act

            # Life Empty
            life_emp = pygame.image.load("assets/ui/icon_life_empty.png").convert_alpha()
            life_emp = pygame.transform.smoothscale(life_emp, (32, 32))
            self.images["icon_life_empty"] = life_emp
        except (FileNotFoundError, pygame.error):
            # Fallback
            la = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(la, (255, 100, 200), (12, 12), 10)
            self.images["icon_life_active"] = la
            
            le = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(le, (100, 100, 100), (12, 12), 10)
            self.images["icon_life_empty"] = le

        # ====== Boss HP Bar ======
        try:
            # Target Size: 360x28 (Height increased)
            hp_w, hp_h = 360, 28
            
            # BG
            bg_src = pygame.image.load("assets/ui/boss_hp_bg.png").convert_alpha()
            self.images["ui_boss_hp_bg"] = pygame.transform.smoothscale(bg_src, (hp_w, hp_h))
            
            # Fill
            fill_src = pygame.image.load("assets/ui/boss_hp_fill.png").convert_alpha()
            self.images["ui_boss_hp_fill"] = pygame.transform.smoothscale(fill_src, (hp_w, hp_h))
            
            # Frame
            frame_src = pygame.image.load("assets/ui/boss_hp_frame.png").convert_alpha()
            self.images["ui_boss_hp_frame"] = pygame.transform.smoothscale(frame_src, (hp_w, hp_h))
            
        except (FileNotFoundError, pygame.error):
            # Fallback will be handled by renderer using shape drawing logic 
            # or created here. Let's create placeholders.
            placeholder_w, placeholder_h = 360, 28
            
            p_bg = pygame.Surface((placeholder_w, placeholder_h))
            p_bg.fill((50, 0, 0))
            self.images["ui_boss_hp_bg"] = p_bg

            p_fill = pygame.Surface((placeholder_w, placeholder_h))
            p_fill.fill((255, 50, 50))
            self.images["ui_boss_hp_fill"] = p_fill

            p_frame = pygame.Surface((placeholder_w, placeholder_h), pygame.SRCALPHA)
            pygame.draw.rect(p_frame, (255, 255, 255), (0, 0, placeholder_w, placeholder_h), 2)
            self.images["ui_boss_hp_frame"] = p_frame

        # ====== Boss Life (Phase) Icon ======
        try:
            # Target Size: 16x16
            life_icon = pygame.image.load("assets/ui/boss_life_icon.png").convert_alpha()
            self.images["ui_boss_life_icon"] = pygame.transform.smoothscale(life_icon, (16, 16))
        except (FileNotFoundError, pygame.error):
            # Fallback: Yellow Circle
            surf = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 200), (8, 8), 6)
            pygame.draw.circle(surf, (255, 255, 255), (8, 8), 6, 1)
            self.images["ui_boss_life_icon"] = surf

        # ====== Status Title ======
        try:
            st_img = pygame.image.load("assets/ui/ui_status_title.png").convert_alpha()
            # Scale proportionally to Width 160
            current_w, current_h = st_img.get_size()
            target_w = 160
            ratio = target_w / current_w
            target_h = int(current_h * ratio)
            self.images["ui_status_title"] = pygame.transform.smoothscale(st_img, (target_w, target_h))
        except (FileNotFoundError, pygame.error):
            # Fallback placeholder (160x40)
            surf = pygame.Surface((160, 40), pygame.SRCALPHA)
            pygame.draw.rect(surf, (100, 100, 255), (0,0,160,40), 2)
            self.images["ui_status_title"] = surf

        # ====== Boss Title ======
        try:
            bt_img = pygame.image.load("assets/ui/ui_boss_title.png").convert_alpha()
            # Scale proportionally to Width 160
            current_w, current_h = bt_img.get_size()
            target_w = 160
            ratio = target_w / current_w
            target_h = int(current_h * ratio)
            self.images["ui_boss_title"] = pygame.transform.smoothscale(bt_img, (target_w, target_h))
        except (FileNotFoundError, pygame.error):
            # Fallback placeholder (160x40)
            surf = pygame.Surface((160, 40), pygame.SRCALPHA)
            pygame.draw.rect(surf, (255, 100, 100), (0,0,160,40), 2)
            self.images["ui_boss_title"] = surf

        # ====== Main Menu Logo ======
        try:
            logo_img = pygame.image.load("assets/ui/logo.png").convert_alpha()
            w, h = logo_img.get_size()
            # Limit width if too large
            if w > 600:
                scale = 600 / w
                logo_img = pygame.transform.smoothscale(logo_img, (600, int(h * scale)))
            self.images["menu_logo"] = logo_img
        except (FileNotFoundError, pygame.error):
            pass # Key won't exist, main_menu will fallback to text

        # ====== Main Menu Background (with Logo) ======
        try:
            bg_img = pygame.image.load("assets/ui/menu_bg.png").convert()
            # Scale to Window Size (720x640)
            self.images["menu_bg"] = pygame.transform.smoothscale(bg_img, (720, 640))
        except (FileNotFoundError, pygame.error):
            pass # Fallback to color fill

        # ====== Menu Cursor ======
        try:
            cursor_img = pygame.image.load("assets/ui/menu_cursor.png").convert_alpha()
            # Scale proportionally to Height 36 (match font size)
            w, h = cursor_img.get_size()
            target_h = 36
            ratio = target_h / h
            target_w = int(w * ratio)
            self.images["menu_cursor"] = pygame.transform.smoothscale(cursor_img, (target_w, target_h))
        except (FileNotFoundError, pygame.error):
            pass

        # ====== Character Portraits ======
        # ====== Character Portraits ======
        try:
            img = pygame.image.load("assets/ui/ema.png").convert_alpha()
            self.images["portrait_ema"] = img
            # Generate Blur
            w, h = img.get_size()
            small = pygame.transform.smoothscale(img, (max(1, w // 10), max(1, h // 10)))
            self.images["portrait_ema_blur"] = pygame.transform.smoothscale(small, (w, h))
        except (FileNotFoundError, pygame.error):
            # Fallback
            s = pygame.Surface((400, 600), pygame.SRCALPHA)
            s.fill((200, 50, 50, 200)) # Reddish
            self.images["portrait_ema"] = s
            self.images["portrait_ema_blur"] = s

        try:
            img = pygame.image.load("assets/ui/hero.png").convert_alpha()
            self.images["portrait_hero"] = img
            # Generate Blur
            w, h = img.get_size()
            small = pygame.transform.smoothscale(img, (max(1, w // 10), max(1, h // 10)))
            self.images["portrait_hero_blur"] = pygame.transform.smoothscale(small, (w, h))
        except (FileNotFoundError, pygame.error):
            s = pygame.Surface((400, 600), pygame.SRCALPHA)
            s.fill((220, 220, 50, 200)) # Yellowish
            self.images["portrait_hero"] = s
            self.images["portrait_hero_blur"] = s

        # ====== Frame ======
        try:
            self.images["select_frame"] = pygame.image.load("assets/ui/select_frame.png").convert_alpha()
        except (FileNotFoundError, pygame.error):
            pass

        # ====== Character Select Title ======
        try:
            self.images["select_title"] = pygame.image.load("assets/ui/select_title.png").convert_alpha()
        except (FileNotFoundError, pygame.error):
            pass

        # 3. Option Tracking Bullet (Unique)
        try:
            # assets/sprites/bullets/bullet_option.png
            bo_src = pygame.image.load("assets/sprites/bullets/bullet_option.png").convert_alpha()
            bo_rot = pygame.transform.rotate(bo_src, 90)
            # 追踪弹通常稍微宽一点或特别一点，设定为 16x32
            bo = pygame.transform.smoothscale(bo_rot, (20, 32))
            self.images["player_bullet_option_tracking"] = bo
        except (FileNotFoundError, pygame.error):
            bo = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(bo, (100, 255, 100), (8, 8), 6)
            self.images["player_bullet_option_tracking"] = bo

        # Aliases for compatibility/Renderer mapping
        self.images["player_bullet_main"] = self.images["player_bullet_normal"]
        self.images["player_bullet_main_enhanced"] = self.images["player_bullet_enhanced"]
        
        # Option normal/enhanced alias to player normal/enhanced as per request
        self.images["player_bullet_option"] = self.images["player_bullet_normal"]
        self.images["player_bullet_option_enhanced"] = self.images["player_bullet_enhanced"]

        # player_bullet_missile (Legacy/Unused?)
        pbm = pygame.Surface((8, 16), pygame.SRCALPHA)
        pygame.draw.rect(pbm, (255, 180, 50), (1, 0, 6, 16), border_radius=2)
        pygame.draw.rect(pbm, (255, 255, 200), (2, 2, 4, 8), border_radius=2)
        self.images["player_bullet_missile"] = pbm

        # 敌人基础子弹精灵
        eb = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(eb, (200, 0, 200), (4, 4), 4)
        self.images["enemy_bullet_basic"] = eb

        # 蓝色小弹 (bullet_small) - 用于扇形弹幕
        b_small = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(b_small, (100, 100, 255), (6, 6), 5) # 浅蓝
        pygame.draw.circle(b_small, (255, 255, 255), (6, 6), 3) # 白芯
        self.images["bullet_small"] = b_small

        # 红色中弹 (bullet_medium) - 用于自机狙
        b_med = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(b_med, (255, 50, 50), (8, 8), 7) # 红
        pygame.draw.circle(b_med, (255, 255, 255), (8, 8), 4) # 白芯
        self.images["bullet_medium"] = b_med

        # 炸弹场精灵
        radius = 96
        size = radius * 2
        bomb_img = pygame.Surface((size, size), pygame.SRCALPHA)

        # 半透明外圈
        pygame.draw.circle(bomb_img, (0, 255, 255, 80), (radius, radius), radius)
        # 较亮内圈
        pygame.draw.circle(bomb_img, (0, 200, 255, 160), (radius, radius), radius // 2)

        self.images["bomb_field"] = bomb_img

        # 掉落物精灵：火力 / 点数
        size = 16
        power_img = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(power_img, (255, 80, 80), (2, 2, size - 4, size - 4), border_radius=4)
        self.images["item_power"] = power_img

        point_img = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(point_img, (80, 160, 255), (2, 2, size - 4, size - 4), border_radius=4)
        self.images["item_point"] = point_img

        # 炸弹光束精灵
        beam = pygame.Surface((32, 256), pygame.SRCALPHA)
        pygame.draw.rect(beam, (255, 255, 120, 160), (12, 0, 8, 256))
        pygame.draw.rect(beam, (255, 255, 255, 200), (14, 0, 4, 256))
        self.images["bomb_beam"] = beam

        # ====== 子机（Option）精灵 ======
        try:
            # Load option.png from user folder
            opt_src = pygame.image.load("assets/sprites/options/option.png").convert_alpha()
            # Scale to 24x24 (smaller)
            opt_img = pygame.transform.smoothscale(opt_src, (24, 24))
            
            self.images["option"] = opt_img
            self.images["option_reimu"] = opt_img
            self.images["option_marisa"] = opt_img
        except (FileNotFoundError, pygame.error):
            # Fallback: Default placeholder (Cyan)
            option_default = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(option_default, (100, 200, 255), (12, 12), 10)
            pygame.draw.circle(option_default, (180, 230, 255), (12, 9), 5)
            
            self.images["option"] = option_default
            self.images["option_reimu"] = option_default
            self.images["option_marisa"] = option_default

        self._load_enemy_sprites()
        self._load_boss_sprites()
        self._load_portraits()
        self._load_items()
        self._load_bullets()
        self._load_vfx()
        self._load_audio()

    def get_image(self, name: str) -> pygame.Surface:
        """
        获取指定名称的精灵图。
        如果不存在则返回品红色方块作为占位符。
        """
        if name in self.images:
            return self.images[name]
        # 回退：品红色方块表示缺少资源
        surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        surf.fill((255, 0, 255))
        self.images[name] = surf
        return surf

    def _load_enemy_sprites(self) -> None:
        """Load and slice enemy sprites."""
        # Fairy Small
        path = "assets/sprites/enemies/fairy_small.png"
        try:
            sheet = pygame.image.load(path).convert_alpha()
            
            # Auto-scale large sheets
            # Target frame height around 48px
            # Original: 3 rows. Target Height = 48 * 3 = 144
            
            sw, sh = sheet.get_size()
            rows, cols = 3, 4
            
            # If image is very large, scale it
            if sh > 300:
                target_frame_h = 48
                target_h = target_frame_h * rows
                scale_ratio = target_h / sh
                target_w = int(sw * scale_ratio)
                sheet = pygame.transform.smoothscale(sheet, (target_w, target_h))
                sw, sh = target_w, target_h
                
            frame_w = sw // cols
            frame_h = sh // rows
            
            frames_idle = []
            frames_start = []
            frames_loop = []
            
            for c in range(cols):
                # Row 0: Idle
                rect = pygame.Rect(c * frame_w, 0, frame_w, frame_h)
                frames_idle.append(sheet.subsurface(rect))
                
                # Row 1: Start Move
                rect = pygame.Rect(c * frame_w, frame_h, frame_w, frame_h)
                frames_start.append(sheet.subsurface(rect))
                
                # Row 2: Loop Move
                rect = pygame.Rect(c * frame_w, frame_h * 2, frame_w, frame_h)
                frames_loop.append(sheet.subsurface(rect))
                
            self.enemy_sprites["enemy_fairy_small"] = {
                "idle": frames_idle,
                "start_move": frames_start,
                "loop_move": frames_loop
            }
            print(f"Loaded enemy sprite: {path} ({sw}x{sh}) -> Frame {frame_w}x{frame_h}")
            
        except (FileNotFoundError, pygame.error) as e:
            print(f"Failed to load enemy sprite {path}: {e}")

        # Fairy Large (Medium)
        path = "assets/sprites/enemies/fairy_large.png"
        try:
            sheet = pygame.image.load(path).convert_alpha()
            sw, sh = sheet.get_size()
            rows, cols = 3, 4
            
            # Use larger target size for "Large/Medium" fairy
            # Small was 48px height. Let's try 64px or keep original if reasonable.
            # If explicit scaling needed:
            if sh > 400: # Scale down if huge
                target_frame_h = 64
                target_h = target_frame_h * rows
                scale_ratio = target_h / sh
                target_w = int(sw * scale_ratio)
                sheet = pygame.transform.smoothscale(sheet, (target_w, target_h))
                sw, sh = target_w, target_h
                
            frame_w = sw // cols
            frame_h = sh // rows
            
            frames_idle = []
            frames_start = []
            frames_loop = []
            
            for c in range(cols):
                # Row 0: Idle
                rect = pygame.Rect(c * frame_w, 0, frame_w, frame_h)
                frames_idle.append(sheet.subsurface(rect))
                
                # Row 1: Start Move
                rect = pygame.Rect(c * frame_w, frame_h, frame_w, frame_h)
                frames_start.append(sheet.subsurface(rect))
                
                # Row 2: Loop Move
                rect = pygame.Rect(c * frame_w, frame_h * 2, frame_w, frame_h)
                frames_loop.append(sheet.subsurface(rect))
                
            self.enemy_sprites["enemy_fairy_large"] = {
                "idle": frames_idle,
                "start_move": frames_start,
                "loop_move": frames_loop
            }
            print(f"Loaded enemy sprite: {path} ({sw}x{sh}) -> Frame {frame_w}x{frame_h}")
            
        except (FileNotFoundError, pygame.error) as e:
            print(f"Failed to load enemy sprite {path}: {e}")

            self.enemy_sprites["enemy_fairy_large"] = {
                "idle": frames_idle,
                "start_move": frames_start,
                "loop_move": frames_loop
            }
            print(f"Loaded enemy sprite: {path} ({sw}x{sh}) -> Frame {frame_w}x{frame_h}")
            
        except (FileNotFoundError, pygame.error) as e:
            print(f"Failed to load enemy sprite {path}: {e}")

    def _load_portraits(self) -> None:
        """Load dialogue portraits."""
        # Player (Ema)
        path = "assets/sprites/portraits/ema.png"
        target_h = 400
        try:
            img = pygame.image.load(path).convert_alpha()
            # Scale to fixed height
            if img.get_height() != target_h:
                scale = target_h / img.get_height()
                new_w = int(img.get_width() * scale)
                img = pygame.transform.smoothscale(img, (new_w, target_h))
                
            self.images["portrait_player"] = img
            print(f"Loaded portrait: {path}")
        except (FileNotFoundError, pygame.error):
            print(f"Failed to load portrait {path}")
            # Placeholder
            s = pygame.Surface((300, 400), pygame.SRCALPHA)
            pygame.draw.rect(s, (255, 100, 100), (50, 50, 200, 300))
            self.images["portrait_player"] = s

        # Player Variation (Ema 2)
        path = "assets/sprites/portraits/ema_2.png"
        try:
            img = pygame.image.load(path).convert_alpha()
            if img.get_height() != target_h:
                scale = target_h / img.get_height()
                new_w = int(img.get_width() * scale)
                img = pygame.transform.smoothscale(img, (new_w, target_h))
            self.images["portrait_player_2"] = img
        except (FileNotFoundError, pygame.error):
            # No placeholder needed, renderer will fallback to default if missing
            pass

        # Boss (Yuki)
        path = "assets/sprites/portraits/yuki.png"
        try:
            img = pygame.image.load(path).convert_alpha()
            # Scale to fixed height
            if img.get_height() != target_h:
                scale = target_h / img.get_height()
                new_w = int(img.get_width() * scale)
                img = pygame.transform.smoothscale(img, (new_w, target_h))
                
            self.images["portrait_boss"] = img
            print(f"Loaded portrait: {path}")
        except (FileNotFoundError, pygame.error):
            print(f"Failed to load portrait {path}")
            s = pygame.Surface((300, 400), pygame.SRCALPHA)
            pygame.draw.rect(s, (100, 100, 255), (50, 50, 200, 300))
            self.images["portrait_boss"] = s
            
        # Boss Variation (Yuki 2)
        path = "assets/sprites/portraits/yuki_2.png"
        try:
            img = pygame.image.load(path).convert_alpha()
            if img.get_height() != target_h:
                scale = target_h / img.get_height()
                new_w = int(img.get_width() * scale)
                img = pygame.transform.smoothscale(img, (new_w, target_h))
            self.images["portrait_boss_2"] = img
        except (FileNotFoundError, pygame.error):
            pass

        # Boss Variation (Yuki 3)
        path = "assets/sprites/portraits/yuki_3.png"
        try:
            img = pygame.image.load(path).convert_alpha()
            if img.get_height() != target_h:
                scale = target_h / img.get_height()
                new_w = int(img.get_width() * scale)
                img = pygame.transform.smoothscale(img, (new_w, target_h))
            self.images["portrait_boss_3"] = img
        except (FileNotFoundError, pygame.error):
            pass

        # Boss Variation (Yuki 4)
        path = "assets/sprites/portraits/yuki_4.png"
        try:
            img = pygame.image.load(path).convert_alpha()
            if img.get_height() != target_h:
                scale = target_h / img.get_height()
                new_w = int(img.get_width() * scale)
                img = pygame.transform.smoothscale(img, (new_w, target_h))
            self.images["portrait_boss_4"] = img
        except (FileNotFoundError, pygame.error):
            pass

        # Names
        target_name_h = 90
        try:
            img = pygame.image.load("assets/ui/name_ema.png").convert_alpha()
            if img.get_height() != target_name_h:
                scale = target_name_h / img.get_height()
                new_w = int(img.get_width() * scale)
                img = pygame.transform.smoothscale(img, (new_w, target_name_h))
            self.images["name_ema"] = img
        except (FileNotFoundError, pygame.error):
            pass
            
        try:
            img = pygame.image.load("assets/ui/name_yuki.png").convert_alpha()
            if img.get_height() != target_name_h:
                scale = target_name_h / img.get_height()
                new_w = int(img.get_width() * scale)
                img = pygame.transform.smoothscale(img, (new_w, target_name_h))
            self.images["name_yuki"] = img
        except (FileNotFoundError, pygame.error):
            pass

    def _load_boss_sprites(self) -> None:
        """Load and slice boss sprites."""
        # Boss (Generic or Specific)
        path = "assets/sprites/enemies/boss.png"
        try:
            sheet = pygame.image.load(path).convert_alpha()
            
            # Bosses are larger, target frame height around 80-96px
            target_frame_h = 96
            rows, cols = 3, 4
            sw, sh = sheet.get_size()
            
            # Auto-scale logic
            expected_h = target_frame_h * rows
            if abs(sh - expected_h) > 10: # If size mismatch significant
               scale_ratio = expected_h / sh
               target_w = int(sw * scale_ratio)
               sheet = pygame.transform.smoothscale(sheet, (target_w, expected_h))
               sw, sh = target_w, expected_h
               
            frame_w = sw // cols
            frame_h = sh // rows
            
            # Row 0: Idle & Transition
            # Frame 0: Static Idle (第一行第一帧用作待机)
            rect_idle = pygame.Rect(0, 0, frame_w, frame_h)
            frames_idle = [sheet.subsurface(rect_idle)]
            
            # Frame 1: Transition 1 (第一行第二帧)
            rect_trans1 = pygame.Rect(frame_w, 0, frame_w, frame_h)
            trans_frame1 = sheet.subsurface(rect_trans1)
            
            # Frame 2: Transition 2 (第一行第三帧 - 新增)
            rect_trans2 = pygame.Rect(frame_w * 2, 0, frame_w, frame_h)
            trans_frame2 = sheet.subsurface(rect_trans2)

            frames_start_main = []
            frames_loop = []
            
            for c in range(cols):
                # Row 1 (Index 1): Start Move Main Frames (第二行)
                rect = pygame.Rect(c * frame_w, frame_h, frame_w, frame_h)
                frames_start_main.append(sheet.subsurface(rect))
                
                # Row 2 (Index 2): Loop Move (第三行)
                rect = pygame.Rect(c * frame_w, frame_h * 2, frame_w, frame_h)
                frames_loop.append(sheet.subsurface(rect))
            
            # Combine transition + start (第二、三帧并入起飞序列首部)
            frames_start = [trans_frame1, trans_frame2] + frames_start_main

            self.enemy_sprites["enemy_boss"] = {
                "idle": frames_idle,
                "start_move": frames_start,
                "loop_move": frames_loop
            }
            print(f"Loaded boss sprite: {path} ({sw}x{sh}) -> Frame {frame_w}x{frame_h}")

            # 加载攻击动画素材 (1行4列)
            attack_path = "assets/sprites/enemies/微信图片_20251216235357_452_38.png"
            try:
                attack_sheet = pygame.image.load(attack_path).convert_alpha()
                aw, ah = attack_sheet.get_size()
                attack_cols = 4
                attack_frame_w = aw // attack_cols

                # 按高度缩放，保持宽高比
                scale_ratio = frame_h / ah
                scaled_w = int(attack_frame_w * scale_ratio)
                scaled_h = frame_h

                # 切割并缩放（保持宽高比）
                attack_frames_raw = []
                for i in range(attack_cols):
                    rect = pygame.Rect(i * attack_frame_w, 0, attack_frame_w, ah)
                    frame = attack_sheet.subsurface(rect)
                    # 按比例缩放，不变形
                    scaled = pygame.transform.smoothscale(frame, (scaled_w, scaled_h))
                    attack_frames_raw.append(scaled)

                # 生成序列: 0→1→2→3→2→1→0 (正放+倒放，共7帧)
                self.enemy_sprites["enemy_boss"]["attack"] = [
                    attack_frames_raw[0],  # 常态
                    attack_frames_raw[1],  # 过渡1
                    attack_frames_raw[2],  # 过渡2
                    attack_frames_raw[3],  # 发射
                    attack_frames_raw[2],  # 过渡2 (倒放)
                    attack_frames_raw[1],  # 过渡1 (倒放)
                    attack_frames_raw[0],  # 常态 (恢复)
                ]
                print(f"Loaded boss attack sprite: {attack_path} -> 7 frames (Scaled to {scaled_w}x{scaled_h})")
            except (FileNotFoundError, pygame.error) as e:
                print(f"Failed to load boss attack sprite {attack_path}: {e}")

        except (FileNotFoundError, pygame.error) as e:
            print(f"Failed to load boss sprite {path}: {e}")

    def _load_vfx(self) -> None:
        """Load visual effects."""
        # Boss Aura
        # 2 Rows * 3 Cols = 6 Frames total.
        path = "assets/sprites/vfx/boss_aura.png"
        try:
           sheet = pygame.image.load(path).convert_alpha()
           sw, sh = sheet.get_size()
           rows, cols = 2, 3
           frame_w = sw // cols
           frame_h = sh // rows
           
           # Target size: Larger than Boss (approx height 140)
           target_h = 120
           scale_ratio = target_h / frame_h
           target_w = int(frame_w * scale_ratio)
           
           frames = []
           for r in range(rows):
               for c in range(cols):
                   rect = pygame.Rect(c*frame_w, r*frame_h, frame_w, frame_h)
                   surface = sheet.subsurface(rect)
                   scaled = pygame.transform.smoothscale(surface, (target_w, target_h))
                   frames.append(scaled)
           
           self.vfx["boss_aura"] = frames
           print(f"Loaded VFX: {path} -> {len(frames)} frames (Scaled to {target_w}x{target_h})")
        except (FileNotFoundError, pygame.error) as e:
           print(f"Failed to load VFX {path}: {e}")

        # Explosion
        # 1 Row * 8 Cols = 8 Frames total.
        path = "assets/sprites/vfx/explosion.png"
        try:
           sheet = pygame.image.load(path).convert_alpha()
           sw, sh = sheet.get_size()
           cols = 8
           frame_w = sw // cols
           frame_h = sh
           
           frames = []
           target_size = (64, 64) # User requested smaller size
           for c in range(cols):
               rect = pygame.Rect(c*frame_w, 0, frame_w, frame_h)
               surface = sheet.subsurface(rect)
               scaled = pygame.transform.smoothscale(surface, target_size)
               frames.append(scaled)
               # Register for SpriteInfo access
               self.images[f"explosion_{c}"] = scaled
           
           self.vfx["explosion"] = frames
           print(f"Loaded VFX: {path} -> {len(frames)} frames (Scaled to {target_size})")
        except (FileNotFoundError, pygame.error) as e:
           print(f"Failed to load VFX {path}: {e}")

        # Boss Cut-in
        try:
            # Try PNG first
            cutin_path = "assets/ui/boss_cutin.png"
            try:
                cutin_img = pygame.image.load(cutin_path).convert_alpha()
            except (FileNotFoundError, pygame.error):
                # Fallback to JPG
                cutin_path = "assets/ui/boss_cutin.jpg"
                cutin_img = pygame.image.load(cutin_path).convert_alpha()
            
            self.images["boss_cutin"] = cutin_img
            print(f"Loaded Boss Cut-in: {cutin_path}")
        except (FileNotFoundError, pygame.error):
            print("Warning: boss_cutin.png/jpg not found. Using placeholder.")
            s = pygame.Surface((480, 200), pygame.SRCALPHA)
            s.fill((255, 0, 0, 128))
            pygame.draw.rect(s, (255, 255, 255), (0, 0, 480, 200), 5)
            self.images["boss_cutin"] = s

        # Sakura (Player Invincibility) - Single image
        path = "assets/sprites/vfx/sakura.png"
        try:
           img = pygame.image.load(path).convert_alpha()
           # Scale to target size
           target_size = (120, 120)
           scaled = pygame.transform.smoothscale(img, target_size)
           self.images["sakura"] = scaled
           print(f"Loaded VFX: {path} -> Scaled to {target_size}")
        except (FileNotFoundError, pygame.error) as e:
           print(f"Failed to load VFX {path}: {e}")

    def _load_items(self) -> None:
        """Load item sprites."""
        # Item definitions: (name, filename, target_size)
        items = [
            ("item_exp_small", "assets/sprites/items/item_exp_small.png", (24, 24)),
            ("item_exp_large", "assets/sprites/items/item_exp_large.png", (24, 24)),
        ]
        
        for name, path, size in items:
            try:
                img = pygame.image.load(path).convert_alpha()
                # Smoothscale to target size
                scaled = pygame.transform.smoothscale(img, size)
                self.images[name] = scaled
                print(f"Loaded item: {path} -> Scaled to {size}")
            except (FileNotFoundError, pygame.error) as e:
                print(f"Failed to load item {path}: {e}")
                # Fallback: Simple colored circle
                fallback = pygame.Surface(size, pygame.SRCALPHA)
                color = (0, 0, 255) if "small" in name else (255, 255, 0)
                pygame.draw.circle(fallback, color, (size[0]//2, size[1]//2), size[0]//2)
                self.images[name] = fallback

    def _load_bullets(self) -> None:
        """Load additional bullet sprites."""
        # Boss Bullets
        bullets = [
            ("boss_bullet_blue", "assets/sprites/bullets/boss_bullet_small.png", (14, 14)),
            ("boss_bullet_red", "assets/sprites/bullets/boss_bullet_large.png", (20, 20)),
        ]
        
        for name, path, size in bullets:
            try:
                img = pygame.image.load(path).convert_alpha()
                scaled = pygame.transform.smoothscale(img, size)
                self.images[name] = scaled
                print(f"Loaded bullet: {path} -> Scaled to {size}")
            except (FileNotFoundError, pygame.error) as e:
                print(f"Failed to load bullet {path}: {e}")
                surf = pygame.Surface(size, pygame.SRCALPHA)
                color = (0, 0, 255) if "blue" in name else (255, 0, 0)
                pygame.draw.circle(surf, color, (size[0]//2, size[1]//2), size[0]//2 - 2)
                self.images[name] = surf

    def _load_audio(self) -> None:
        """Load audio assets (SFX)."""
        sfx_list = [
            ("player_shot", "assets/sfx/player_shot.wav"),
            ("enemy_damage", "assets/sfx/enemy_damage.wav"),
            ("pause", "assets/sfx/pause.wav"),
            ("item_get", "assets/sfx/item_get.wav"),
            ("explosion", "assets/sfx/explosion.wav"),
            ("menu_confirm", "assets/sfx/menu_confirm.wav"),
            ("menu_select", "assets/sfx/menu_select.wav"),
            ("player_death", "assets/sfx/player_death.wav"),
        ]
        
        for name, path in sfx_list:
            try:
                sound = pygame.mixer.Sound(path)
                if name == "player_shot":
                    sound.set_volume(0.05)
                elif name == "item_get":
                    sound.set_volume(0.1)
                elif name == "explosion":
                    sound.set_volume(0.15) # Slightly lower than default 0.2
                else:
                    sound.set_volume(0.2)
                self.sfx[name] = sound
                print(f"Loaded SFX: {path}")
            except (FileNotFoundError, pygame.error) as e:
                print(f"Failed to load SFX {path}: {e}")

    def play_music(self, name: str) -> None:
        """Play background music by name."""
        music_paths = {
            "stage1": "assets/bgm/stage1_theme.flac",
            "boss": "assets/bgm/boss_theme.flac",
        }
        
        if name == "stop":
            pygame.mixer.music.stop()
            print("Music stopped")
            return
        
        if name in music_paths:
            path = music_paths[name]
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(0.2) # Background music volume
                pygame.mixer.music.play(-1) # Loop indefinitely
                print(f"Playing music: {path}")
            except pygame.error as e:
                print(f"Failed to play music {path}: {e}")
        else:
            print(f"Music track not found: {name}")

    def get_font(self, size: int) -> pygame.font.Font:
        """Get cached font of specific size."""
        if size in self.fonts:
            return self.fonts[size]
        
        try:
            font = pygame.font.Font(self.font_path, size)
        except (FileNotFoundError, pygame.error):
            # Fallback to system font
            font = pygame.font.SysFont("arial", size)
            
        self.fonts[size] = font
        return font

    def play_sfx(self, name: str) -> None:
        """Play sound effect by name."""
        if name in self.sfx:
            self.sfx[name].play()
        else:
            # Silent fail for missing sfx to avoid spam
            pass
