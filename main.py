"""
东方风格弹幕射击游戏主入口
"""
import argparse
import pygame

from controller.game_controller import GameController
from model.character import CharacterId, get_all_characters
from view.assets import Assets
from view.main_menu import MainMenu, MenuResult


def _parse_character_id(name: str | None) -> CharacterId | None:
    """解析命令行参数中的角色 ID"""
    if not name:
        return None
    token = name.strip().upper()
    for cid in CharacterId:
        if token == cid.name:
            return cid
    return None


def _prompt_character_id() -> CharacterId | None:
    """交互式角色选择提示"""
    chars = get_all_characters()
    if not chars:
        return None
    print("选择角色：")
    for idx, preset in enumerate(chars, start=1):
        print(f"  {idx}. {preset.name} - {preset.description}")
    choice = input(f"输入编号 [1-{len(chars)}]（留空默认为 1）：").strip()
    if not choice:
        return list(CharacterId)[0]
    if choice.isdigit():
        i = int(choice)
        if 1 <= i <= len(chars):
            return list(CharacterId)[i - 1]
    # 回退到默认角色
    return list(CharacterId)[0]


def main():
    """游戏主函数"""
    parser = argparse.ArgumentParser(description="东方风格弹幕射击游戏")
    parser.add_argument(
        "-c",
        "--character",
        help="角色 ID 名称（如 REIMU_A, MARISA_A）。留空则进入主菜单。",
    )
    parser.add_argument(
        "--skip-menu",
        action="store_true",
        help="跳过主菜单直接开始游戏（需配合 -c 使用）。",
    )
    args = parser.parse_args()

    pygame.init()

    display_width = 720
    display_height = 640
    screen = pygame.display.set_mode((display_width, display_height))
    pygame.display.set_caption("東方混沌勢 ~ Touhou KontonSei")
    # Increase audio channels to handle intense SFX
    pygame.mixer.set_num_channels(32)

    # 如果指定了角色且跳过菜单，直接开始
    character_id = _parse_character_id(args.character)
    if character_id is not None and args.skip_menu:
        _start_game(screen, display_width, display_height, character_id)
        return

    # 否则显示主菜单
    while True:
        # 加载资源用于菜单
        assets = Assets()
        assets.load()
        
        menu = MainMenu(screen, assets)
        result, selected_character = menu.run()
        
        if result == MenuResult.EXIT:
            pygame.quit()
            return
        elif result == MenuResult.START_GAME:
            # 开始游戏
            should_quit = _start_game(screen, display_width, display_height, selected_character)
            if should_quit:
                # 窗口关闭按钮被点击，直接退出程序
                pygame.quit()
                return
            # 否则返回主菜单（循环继续）


def _start_game(
    screen: pygame.Surface,
    display_width: int,
    display_height: int,
    character_id: CharacterId | None
) -> bool:
    """启动游戏，返回 True 表示窗口被关闭需要退出程序"""
    controller = GameController(
        screen_width=display_width,
        screen_height=display_height,
        screen=screen,
        character_id=character_id,
        game_width=480
    )
    controller.run()
    return controller.quit_requested


if __name__ == "__main__":
    main()
