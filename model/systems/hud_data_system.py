from __future__ import annotations

from ..game_state import GameState
from ..components import (
    HudData,
    PlayerLife,
    PlayerBomb,
    PlayerPower,
    PlayerScore,
    PlayerGraze,
    GrazeEnergy,
)


def hud_data_system(state: GameState) -> None:
    """
    将玩家状态聚合到 HudData，让视图层只需读取 HudData。
    支持多玩家（遍历所有 PlayerTag 实体）。
    """
    players = state.get_players()
    if not players:
        return

    for player in players:
        hud = player.get(HudData)
        if not hud:
            continue

        life = player.get(PlayerLife)
        bomb = player.get(PlayerBomb)
        power = player.get(PlayerPower)
        score = player.get(PlayerScore)
        graze = player.get(PlayerGraze)
        graze_energy = player.get(GrazeEnergy)

        if life:
            hud.lives = life.lives
            hud.max_lives = life.max_lives
        if bomb:
            hud.bombs = bomb.bombs
            hud.max_bombs = bomb.max_bombs
        if power:
            hud.power = power.power
            hud.max_power = power.max_power
        if score:
            hud.score = score.score
        if graze:
            hud.graze_count = graze.count
        if graze_energy:
            hud.graze_energy = graze_energy.energy
            hud.max_graze_energy = graze_energy.max_energy
            hud.is_enhanced = graze_energy.is_enhanced
