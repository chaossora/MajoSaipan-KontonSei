from __future__ import annotations

import pygame


class Assets:
    """
    简单的资源管理：现在只用一些纯色形状代替实际图片
    """

    def __init__(self) -> None:
        self.images: dict[str, pygame.Surface] = {}

    def load(self) -> None:
        # player_default
        player_img = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(player_img, (0, 200, 255), (16, 16), 10)
        self.images["player_default"] = player_img

        # player_reimu
        reimu = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(reimu, (255, 80, 120), (16, 16), 10)
        pygame.draw.circle(reimu, (255, 200, 220), (16, 12), 6)
        self.images["player_reimu"] = reimu

        # player_marisa
        marisa = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(marisa, (255, 215, 0), (16, 16), 10)
        pygame.draw.circle(marisa, (255, 255, 180), (16, 12), 6)
        self.images["player_marisa"] = marisa

        # enemy_basic
        enemy_img = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(enemy_img, (255, 80, 80), (16, 16), 12)
        self.images["enemy_basic"] = enemy_img

        # enemy_fairy_small
        fairy_small = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(fairy_small, (255, 140, 200), (16, 16), 10)
        pygame.draw.circle(fairy_small, (255, 220, 240), (16, 12), 6)
        self.images["enemy_fairy_small"] = fairy_small

        # enemy_fairy_large
        fairy_large = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(fairy_large, (255, 120, 160), (20, 20), 14)
        pygame.draw.circle(fairy_large, (255, 215, 235), (20, 16), 8)
        self.images["enemy_fairy_large"] = fairy_large

        # enemy_midboss
        midboss = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(midboss, (255, 100, 120), (32, 32), 24)
        pygame.draw.circle(midboss, (255, 200, 210), (32, 28), 14)
        pygame.draw.circle(midboss, (255, 255, 255), (32, 24), 6)
        self.images["enemy_midboss"] = midboss

        # boss_stage1 (Stage 1 Boss)
        boss1 = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(boss1, (180, 80, 200), (32, 32), 28)  # 紫色主体
        pygame.draw.circle(boss1, (220, 160, 240), (32, 26), 16)  # 亮色上半
        pygame.draw.circle(boss1, (255, 200, 255), (32, 22), 8)   # 高光
        # 装饰翅膀
        pygame.draw.ellipse(boss1, (200, 120, 220, 180), (4, 20, 16, 24))
        pygame.draw.ellipse(boss1, (200, 120, 220, 180), (44, 20, 16, 24))
        self.images["boss_stage1"] = boss1

        # item_life (残机掉落)
        life_img = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(life_img, (255, 100, 150), (8, 8), 7)
        pygame.draw.circle(life_img, (255, 200, 220), (8, 6), 4)
        self.images["item_life"] = life_img

        # item_bomb (炸弹掉落)
        bomb_item = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(bomb_item, (100, 200, 100), (8, 8), 7)
        pygame.draw.circle(bomb_item, (180, 255, 180), (8, 6), 4)
        self.images["item_bomb"] = bomb_item

        # player_bullet_basic
        pb = pygame.Surface((8, 16), pygame.SRCALPHA)
        pygame.draw.rect(pb, (255, 255, 0), (2, 0, 4, 16))
        self.images["player_bullet_basic"] = pb

        # player_bullet_missile
        pbm = pygame.Surface((8, 16), pygame.SRCALPHA)
        pygame.draw.rect(pbm, (255, 180, 50), (1, 0, 6, 16), border_radius=2)
        pygame.draw.rect(pbm, (255, 255, 200), (2, 2, 4, 8), border_radius=2)
        self.images["player_bullet_missile"] = pbm

        # enemy_bullet_basic
        eb = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(eb, (200, 0, 200), (4, 4), 4)
        self.images["enemy_bullet_basic"] = eb

        # 炸弹范围精灵
        radius = 96
        size = radius * 2
        bomb_img = pygame.Surface((size, size), pygame.SRCALPHA)

        # 半透明的外圈
        pygame.draw.circle(bomb_img, (0, 255, 255, 80), (radius, radius), radius)
        # 稍亮一点的内圈
        pygame.draw.circle(bomb_img, (0, 200, 255, 160), (radius, radius), radius // 2)

        self.images["bomb_field"] = bomb_img

        # 掉落物：火力 / 点数
        size = 16
        power_img = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(power_img, (255, 80, 80), (2, 2, size - 4, size - 4), border_radius=4)
        self.images["item_power"] = power_img

        point_img = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(point_img, (80, 160, 255), (2, 2, size - 4, size - 4), border_radius=4)
        self.images["item_point"] = point_img

        # 炸弹光束占位符
        beam = pygame.Surface((32, 256), pygame.SRCALPHA)
        pygame.draw.rect(beam, (255, 255, 120, 160), (12, 0, 8, 256))
        pygame.draw.rect(beam, (255, 255, 255, 200), (14, 0, 4, 256))
        self.images["bomb_beam"] = beam

    def get_image(self, name: str) -> pygame.Surface:
        if name in self.images:
            return self.images[name]
        # 回退：品红色方块表示缺少资源
        surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        surf.fill((255, 0, 255))
        self.images[name] = surf
        return surf
