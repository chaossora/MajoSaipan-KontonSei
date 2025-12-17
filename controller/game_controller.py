from __future__ import annotations

import pygame

from model.game_state import GameState, spawn_player, spawn_item

# 固定时间步常量
TARGET_FPS = 60
FIXED_DT = 1.0 / TARGET_FPS  # 固定时间步长（秒）
MAX_TICKS_PER_RENDER = 5  # 每帧最大逻辑 tick 次数，防止 spiral of death
from model.components import ItemType, InputState
from model.character import CharacterId, get_character_preset
from model.systems.movement import movement_system
from model.systems.player_movement import player_move_system
from model.systems.player_shoot import player_shoot_system
from model.systems.option_system import option_system
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
from model.systems.death_effect import player_respawn_visual_system
from model.systems.boss_hud_system import boss_hud_system
from model.systems.task_system import task_system
from model.systems.motion_program_system import motion_program_system
from model.systems.homing_bullet_system import homing_bullet_system
from model.systems.laser_collision_system import laser_collision_system
from model.systems.laser_motion_system import laser_motion_system
from model.systems.vfx_system import vfx_system
from model.systems.shockwave_system import shockwave_system
from model.stages.stage1 import setup_stage1
from model.enemies import spawn_fairy_small, spawn_fairy_large, spawn_midboss
from model.scripting.archetype import register_default_archetypes

# 导入 bosses 模块以注册 Boss 工厂函数到注册表
import model.bosses

from view.assets import Assets
from view.renderer import Renderer
from view.pause_renderer import PauseRenderer


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
        self.quit_requested = False  # 窗口关闭请求（区别于返回菜单）
        self.accumulator = 0.0  # 时间累积器
        
        # Pause State
        self.paused = False
        self.pause_selection = 0

        self.assets = Assets()
        self.assets.load()
        
        self.pause_renderer = PauseRenderer(screen, self.assets)

        # 注册默认子弹原型
        register_default_archetypes()

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
        
        # 播放背景音乐
        self.assets.play_music("stage1")

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
                self.quit_requested = True  # 标记为窗口关闭请求
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = True
                    pygame.mixer.music.pause()
                    self.assets.play_sfx("pause")

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

    def _logic_tick(self, dt: float) -> None:
        """执行一次逻辑 tick，使用固定时间步 dt。"""
        self.state.time += dt
        self.state.frame += 1

        # 0. TaskSystem: 推进所有 Task 脚本（可能发射子弹/生成敌人）
        # Requirements 8.1: TaskSystem 在最前执行
        task_system(self.state, dt)

        # 1. 玩家移动、子机、射击、敌人射击
        player_move_system(self.state, dt)
        option_system(self.state, dt)  # 子机位置更新：在移动后、射击前
        if player_shoot_system(self.state, dt):
            if "player_shot" in self.assets.sfx:
                self.assets.sfx["player_shot"].play()

        # PoC 系统：更新点收集线激活标记
        poc_system(self.state)

        gravity_system(self.state, dt)
        item_autocollect_system(self.state, dt)

        # 1.5 MotionSystem: 更新子弹 MotionProgram，修改 Velocity
        # Requirements 8.2: MotionSystem 在 movement_system 之前执行
        motion_program_system(self.state, dt)

        # 1.6 追踪子弹系统：更新 HomingBullet 速度方向
        homing_bullet_system(self.state, dt)

        # 2. 所有物体移动
        movement_system(self.state, dt)

        # 2.5 边界处理：限制玩家在屏幕内，清理出界子弹
        boundary_system(self.state)

        # 2.6 生命周期系统：删除过期实体
        lifetime_system(self.state, dt)

        # 3. 碰撞检测与事件处理
        collision_detection_system(self.state)
        laser_collision_system(self.state)      # 激光碰撞检测
        laser_motion_system(self.state, dt)     # 激光运动更新
        collision_damage_system(self.state, dt)

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
        vfx_system(self.state, dt) # Run Animation updates
        shockwave_system(self.state, dt) # Run Shockwave updates
        boss_hud_system(self.state, dt)  # Boss HUD 数据聚合更新
        hud_data_system(self.state)
        stats_system(self.state)

    def _handle_pause_input(self) -> None:
        """处理暂停菜单输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.quit_requested = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = False # Resume
                    pygame.mixer.music.unpause()
                elif event.key == pygame.K_UP:
                    self.pause_selection = (self.pause_selection - 1) % 3
                elif event.key == pygame.K_DOWN:
                    self.pause_selection = (self.pause_selection + 1) % 3
                elif event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE):
                    if self.pause_selection == 0: # Resume
                        self.paused = False
                        pygame.mixer.music.unpause()
                    elif self.pause_selection == 1: # Return to Title
                        self.running = False # Exit game loop -> returns to MainMenu
                        pygame.mixer.music.stop()
                    elif self.pause_selection == 2: # Quit Game
                        self.running = False
                        self.quit_requested = True
                        pygame.mixer.music.stop()

    def _update_cutin(self, dt: float) -> None:
        """Update cut-in animation state."""
        cutin = self.state.cutin
        
        # Duration match renderer
        DURATION_ENTER = 0.8
        DURATION_HOLD = 1.0
        # DURATION_EXIT = 0.5 # Used implicitly
        
        # 1. First Frame Logic (Stop Music)
        if cutin.stage == 0 and cutin.timer == 0.0:
            if cutin.control_bgm:
                self.assets.play_music("stop")
            
        cutin.timer += dt
        
        if cutin.stage == 0: # Enter
            if cutin.timer >= DURATION_ENTER:
                cutin.stage = 1
                cutin.timer = 0.0
                
        elif cutin.stage == 1: # Hold
            if cutin.timer >= DURATION_HOLD:
                cutin.stage = 2
                cutin.timer = 0.0
                
        elif cutin.stage == 2: # Exit
            # DURATION_EXIT = 0.5
            if cutin.timer >= 0.5:
                cutin.active = False
                # Cut-in finished
                # Start Boss Music after fade out
                if cutin.control_bgm:
                    self.assets.play_music("boss")


    def run(self) -> None:
        """主循环：使用 accumulator 模式实现固定时间步。"""
        while self.running:
            # 获取实际经过的时间
            real_dt = self.clock.tick(TARGET_FPS) / 1000.0
            self.accumulator += real_dt

            # ==========================
            # 暂停逻辑 (Paused State)
            # ==========================
            if self.paused:
                self._handle_pause_input()
                self.accumulator = 0.0 # 暂停时不累积时间
                
                # 渲染: 游戏画面(不翻转) + 暂停覆盖 + 翻转
                self.renderer.render(self.state, flip=False)
                self.pause_renderer.render(self.pause_selection)
                pygame.display.flip()
                continue

            # ==========================
            # Boss Cut-in Logic
            # ==========================
            if self.state.cutin.active:
                self._update_cutin(real_dt)
                self.accumulator = 0.0 # Don't accumulate game logic time
                self.renderer.render(self.state, flip=True)
                continue

            # ==========================
            # Dialogue Logic
            # ==========================
            if self.state.dialogue.active:
                dialogue = self.state.dialogue
                
                if dialogue.closing:
                    # Closing Phase (Just Fade Out)
                    dialogue.timer -= real_dt
                    
                    # Logic: Fade over 1.0 second.
                    if dialogue.timer > 0:
                        dialogue.alpha = int(255 * dialogue.timer)
                    else:
                        dialogue.alpha = 0
                        
                    if dialogue.timer <= 0:
                        dialogue.active = False
                        dialogue.finished = True
                        dialogue.closing = False
                else:
                    # Active Reading Phase
                    # Ensure current line variant is applied
                    if dialogue.current_index < len(dialogue.lines):
                        line = dialogue.lines[dialogue.current_index]
                        if line.variant:
                            dialogue.variants[line.speaker] = line.variant

                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                            self.quit_requested = True
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_z or event.key == pygame.K_RETURN:
                                 # Advance
                                 dialogue.current_index += 1
                                 if dialogue.current_index >= len(dialogue.lines):
                                     dialogue.closing = True
                                     dialogue.timer = 1.0 # 1s fade out (no wait)
                                     dialogue.alpha = 255
                
                self.accumulator = 0.0
                self.renderer.render(self.state, flip=True)
                continue


            # ==========================
            # 运行逻辑 (Running State)
            # ==========================
            
            # 轮询输入（每帧一次，在逻辑 tick 之前）
            key_state = self._poll_input()
            self._write_input_component(key_state)

            # 固定时间步逻辑更新
            tick_count = 0
            while self.accumulator >= FIXED_DT and tick_count < MAX_TICKS_PER_RENDER:
                self._logic_tick(FIXED_DT)
                
                # Check for BGM request
                if self.state.bgm_request:
                    self.assets.play_music(self.state.bgm_request)
                    self.state.bgm_request = None
                
                # Check for SFX requests
                if self.state.sfx_requests:
                    for sfx_name in self.state.sfx_requests:
                        self.assets.play_sfx(sfx_name)
                    self.state.sfx_requests.clear()
                
                self.accumulator -= FIXED_DT
                tick_count += 1

            # Spiral of death 防护：如果 tick 次数达到上限，重置 accumulator
            if tick_count >= MAX_TICKS_PER_RENDER:
                self.accumulator = 0.0

            # 渲染 (Normal Render with Flip)
            self.renderer.render(self.state, flip=True)

        # 不在这里调用 pygame.quit()，让主循环控制退出
