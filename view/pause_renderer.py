import pygame
from view.assets import Assets

class PauseRenderer:
    def __init__(self, screen: pygame.Surface, assets: Assets):
        self.screen = screen
        self.assets = assets
        self.font_item = pygame.font.Font(assets.font_path, 32)
        self.font_title = pygame.font.Font(assets.font_path, 48)
        
        # Overlay surface (semi-transparent black)
        self.overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 128)) # 50% opacity
        
    def render(self, selected_index: int):
        """Render the pause menu overlay and options."""
        # 1. Draw Overlay
        self.screen.blit(self.overlay, (0, 0))
        
        # 2. Draw Options
        options = ["继续游戏", "返回标题", "退出游戏"]
        
        # Calculate center positions
        center_x = self.screen.get_width() // 2
        start_y = self.screen.get_height() // 2 - 50
        
        # Draw "PAUSE" title (Optional, if desired)
        # title_surf = self.font_title.render("PAUSED", True, (255, 255, 255))
        # self.screen.blit(title_surf, title_surf.get_rect(center=(center_x, start_y - 80)))
        
        for i, text in enumerate(options):
            color = (255, 255, 255) if i == selected_index else (150, 150, 150)
            
            # Shadow/Outline
            shadow_surf = self.font_item.render(text, True, (0, 0, 0))
            shadow_rect = shadow_surf.get_rect(center=(center_x + 2, start_y + i * 50 + 2))
            self.screen.blit(shadow_surf, shadow_rect)
            
            # Main Text
            text_surf = self.font_item.render(text, True, color)
            text_rect = text_surf.get_rect(center=(center_x, start_y + i * 50))
            self.screen.blit(text_surf, text_rect)
