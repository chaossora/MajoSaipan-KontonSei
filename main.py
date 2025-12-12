"""
东方风格弹幕射击游戏主入口
"""
import argparse
import pygame

from controller.game_controller import GameController
from model.character import CharacterId, get_all_characters


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
        help="角色 ID 名称（如 REIMU_A, MARISA_A）。留空则进入交互选择。",
    )
    args = parser.parse_args()

    # 确定角色 ID
    character_id = _parse_character_id(args.character)
    if character_id is None:
        character_id = _prompt_character_id()

    pygame.init()

    display_width = 720
    display_height = 640
    screen = pygame.display.set_mode((display_width, display_height))
    pygame.display.set_caption("Touhou-like STG")

    controller = GameController(
        screen_width=display_width,
        screen_height=display_height,
        screen=screen,
        character_id=character_id,
        game_width=480
    )
    controller.run()


if __name__ == "__main__":
    main()
