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
        self.font_path = "assets/fonts/PixelifySans-Black.ttf"

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
            # height 512 -> 80 (approx 1/6.4) - Middle ground size
            target_height = 80
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
            
        except FileNotFoundError:
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
