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

    def load(self) -> None:
        """加载所有游戏资源"""
        # 默认玩家精灵
        player_img = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(player_img, (0, 200, 255), (16, 16), 10)
        self.images["player_default"] = player_img

        # 灵梦玩家精灵
        reimu = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(reimu, (255, 80, 120), (16, 16), 10)
        pygame.draw.circle(reimu, (255, 200, 220), (16, 12), 6)
        self.images["player_reimu"] = reimu

        # 魔理沙玩家精灵
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

        # 玩家基础子弹精灵
        pb = pygame.Surface((8, 16), pygame.SRCALPHA)
        pygame.draw.rect(pb, (255, 255, 0), (2, 0, 4, 16))
        self.images["player_bullet_basic"] = pb

        # 玩家导弹子弹精灵
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

        # ====== 子机精灵 ======
        # 灵梦子机（红/粉配色）
        option_reimu = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(option_reimu, (255, 100, 140), (8, 8), 6)
        pygame.draw.circle(option_reimu, (255, 180, 200), (8, 6), 3)
        self.images["option_reimu"] = option_reimu

        # 魔理沙子机（金/黄配色）
        option_marisa = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(option_marisa, (255, 200, 60), (8, 8), 6)
        pygame.draw.circle(option_marisa, (255, 240, 150), (8, 6), 3)
        self.images["option_marisa"] = option_marisa

        # 默认子机（青色）
        option_default = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(option_default, (100, 200, 255), (8, 8), 6)
        pygame.draw.circle(option_default, (180, 230, 255), (8, 6), 3)
        self.images["option"] = option_default

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
