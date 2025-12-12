from __future__ import annotations

import pygame

from model.game_state import GameState, spawn_player, spawn_item
from model.components import ItemType, InputState
from model.character import CharacterId, get_character_preset
from model.systems.movement import movement_system
from model.systems.player_movement import player_move_system
from model.systems.player_shoot import player_shoot_system
from model.systems.option_system import option_system
from model.systems.enemy_shoot import enemy_shoot_system
from model.systems.delayed_bullet_system import delayed_bullet_system
from model.systems.collision import collision_detection_system
from model.systems.collision_damage_system import collision_damage_system
from model.systems.bomb_hit_system import bomb_hit_system
from model.systems.graze_system import graze_system
from model.systems.graze_energy_system import graze_energy_system
from model.systems.item_pickup import item_pickup_system
from model.systems.player_damage import player_damage_system
from model.systems.bomb_system import bomb_system
from model.systems.enemy_death import enemy_death_system
from model.systems.lifetime import lifetime_system
from model.systems.gravity import gravity_system
from model.systems.item_autocollect import item_autocollect_system
from model.systems.poc_system import poc_system
from model.systems.boundary_system import boundary_system
from model.systems.render_hint_system import render_hint_system
from model.systems.hud_data_system import hud_data_system
from model.systems.stats_system import stats_system
from model.systems.stage_system import stage_system
from model.systems.death_effect import player_respawn_visual_system
from model.systems.boss_phase_system import boss_phase_system
from model.systems.boss_movement_system import boss_movement_system
from model.systems.boss_hud_system import boss_hud_system
from model.systems.bullet_motion_system import bullet_motion_system
from model.stages.stage1 import setup_stage1
from model.enemies import spawn_fairy_small, spawn_fairy_large, spawn_midboss

# 导入 bosses 模块以注册 Boss 工厂函数到注册表
import model.bosses

from view.assets import Assets
from view.renderer import Renderer


class GameController:
    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        screen: pygame.Surface,
        character_id: CharacterId | None = None,
        game_width: int | None = None,
    ) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.game_width = game_width if game_width is not None else screen_width
        self.screen = screen
        self.character_id = character_id

        self.clock = pygame.time.Clock()
        self.running = True

        self.assets = Assets()
        self.assets.load()

        self.state = GameState(
            width=self.game_width,
            height=screen_height,
        )

        self.renderer = Renderer(screen, self.assets)

        # 生成玩家
        from model.game_config import PlayerConfig
        cfg: PlayerConfig | None = self.state.get_resource(PlayerConfig)  # type: ignore
        spawn_y = screen_height - (cfg.spawn_offset_y if cfg else 80.0)
        if character_id is not None:
            preset = get_character_preset(character_id)
            if preset:
                spawn_y = screen_height - preset.spawn_offset_y

        spawn_player(
            self.state,
            x=self.game_width / 2,
            y=spawn_y,
            character_id=character_id,
        )

        # 初始化第一关时间线
        setup_stage1(self.state)

        # 生成测试用掉落物
        spawn_item(
            self.state,
            x=self.game_width / 2 - 40,
            y=screen_height / 2,
            item_type=ItemType.POWER,
        )
        spawn_item(
            self.state,
            x=self.game_width / 2 + 40,
            y=screen_height / 2,
            item_type=ItemType.POINT,
        )

    def _poll_input(self) -> dict[str, bool]:
        """获取当前帧的按键状态。"""
        state = {
            "left": False,
            "right": False,
            "up": False,
            "down": False,
            "focus": False,
            "shoot": False,
            "bomb": False,
        }

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        keys = pygame.key.get_pressed()
        state["left"] = keys[pygame.K_LEFT]
        state["right"] = keys[pygame.K_RIGHT]
        state["up"] = keys[pygame.K_UP]
        state["down"] = keys[pygame.K_DOWN]
        state["focus"] = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        state["shoot"] = keys[pygame.K_z]
        state["bomb"] = keys[pygame.K_x]   # X = 炸弹键

        return state

    def _write_input_component(self, key_state: dict[str, bool]) -> None:
        """将输入写入玩家的 InputState 组件，并计算按键边缘事件。"""
        player = self.state.get_player()
        if not player:
            return
        inp = player.get(InputState)
        if not inp:
            return

        prev_bomb = inp.bomb
        prev_shoot = inp.shoot

        inp.left = key_state["left"]
        inp.right = key_state["right"]
        inp.up = key_state["up"]
        inp.down = key_state["down"]
        inp.focus = key_state["focus"]
        inp.shoot = key_state["shoot"]
        inp.bomb = key_state["bomb"]

        inp.bomb_pressed = key_state["bomb"] and not prev_bomb
        inp.shoot_pressed = key_state["shoot"] and not prev_shoot

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.state.time += dt
            self.state.frame += 1

            key_state = self._poll_input()
            self._write_input_component(key_state)

            # 1. 玩家移动、子机、射击、敌人射击
            player_move_system(self.state, dt)
            option_system(self.state, dt)  # 子机位置更新：在移动后、射击前
            player_shoot_system(self.state, dt)
            enemy_shoot_system(self.state, dt)
            delayed_bullet_system(self.state, dt)  # 延迟子弹队列处理

            # PoC 系统：更新点收集线激活标记
            poc_system(self.state)

            gravity_system(self.state, dt)
            item_autocollect_system(self.state, dt)
            stage_system(self.state, dt)

            # Boss 移动系统（在普通移动前）
            boss_movement_system(self.state, dt)

            # 2. 所有物体移动
            movement_system(self.state, dt)

            # 2.1 子弹运动状态机：处理运动阶段切换
            bullet_motion_system(self.state, dt)

            # 2.5 边界处理：限制玩家在屏幕内，清理出界子弹
            boundary_system(self.state)

            # 2.6 生命周期系统：删除过期实体
            lifetime_system(self.state, dt)

            # 3. 碰撞检测与事件处理
            collision_detection_system(self.state)
            collision_damage_system(self.state, dt)

            # Boss 阶段系统：检测血量耗尽或超时，处理阶段转换
            boss_phase_system(self.state, dt)

            bomb_hit_system(self.state, dt)
            graze_system(self.state, dt)
            graze_energy_system(self.state, dt)  # 擦弹能量系统：累积能量，触发增强
            item_pickup_system(self.state, dt)

            # 4. 玩家受伤系统：处理死亡炸弹窗口
            player_damage_system(self.state, dt)

            # 5. 炸弹系统
            bomb_system(self.state, dt)

            # 5.5 敌人死亡系统：处理掉落和清理
            enemy_death_system(self.state, dt)

            # 5.6 玩家重生闪烁效果
            player_respawn_visual_system(self.state, dt)

            # 6. 渲染前更新 HUD 和统计数据
            render_hint_system(self.state)
            boss_hud_system(self.state, dt)  # Boss HUD 数据聚合更新
            hud_data_system(self.state)
            stats_system(self.state)

            # 8. 渲染
            self.renderer.render(self.state)

        pygame.quit()
