from __future__ import annotations

from ..game_state import GameState
from ..components import PlayerLife, PlayerBomb, PlayerDamageState, InputState
from .death_effect import apply_death_effect


def player_damage_system(
    state: GameState,
    dt: float,
) -> None:
    """
    玩家受伤 / 命数系统（不直接调用 bomb 系统）：
    - 只关心：
        * invincible_timer / deathbomb_timer
        * pending_death
        * 在 death window 内有没有按 X

    - deathbomb 本质上就是：
        * pending_death == True 且 deathbomb_timer > 0 时按 X
        * 本系统把 pending_death 清掉（这次不死）
        * BombSystem 同一帧看到 bomb_pressed 再去处理 Bomb 效果
    """
    player = state.get_player()
    if not player:
        return
    inp = player.get(InputState)
    life = player.get(PlayerLife)
    bomb = player.get(PlayerBomb)
    dmg = player.get(PlayerDamageState)
    if not (life and bomb and dmg and inp):
        return

    # 计时器
    if dmg.invincible_timer > 0.0:
        dmg.invincible_timer -= dt
        if dmg.invincible_timer < 0.0:
            dmg.invincible_timer = 0.0

    if dmg.deathbomb_timer > 0.0:
        dmg.deathbomb_timer -= dt
        if dmg.deathbomb_timer < 0.0:
            dmg.deathbomb_timer = 0.0

    if not dmg.pending_death:
        return

    # 死亡窗口中：按 X 取消本次死亡（不在此处判断炸弹库存）
    if inp.bomb_pressed and dmg.deathbomb_timer > 0.0:
        dmg.pending_death = False
        dmg.deathbomb_timer = 0.0
        return

    # 窗口结束：执行掉命
    if dmg.deathbomb_timer <= 0.0:
        dmg.pending_death = False
        life.lives -= 1

        if life.lives > 0:
            # 掉命后进入无敌状态
            dmg.invincible_timer = 2.0
            # 执行死亡效果：清除敌弹、清除敌人、重生
            apply_death_effect(state, player)
        else:
            # 玩家残机用尽，标记游戏结束
            state.game_over = True
