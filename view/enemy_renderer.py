import pygame
import math
from model.game_state import GameState
from model.components import Velocity, SpriteInfo, Position

class EnemyRenderer:
    def __init__(self, screen: pygame.Surface, assets):
        self.screen = screen
        self.assets = assets
        
        # 动画状态缓存: { entity_id: { "state": "idle", "timer": 0.0, "face_right": True } }
        self.anim_states = {}
        
        # 动画配置
        self.FRAME_DURATION = 0.1  # 每帧持续时间(秒)
        
    def render(self, actor, state: GameState):
        """渲染单个敌人"""
        sprite_info = actor.get(SpriteInfo)
        if not sprite_info or not sprite_info.visible:
            return
            
        pos = actor.get(Position)
        vel = actor.get(Velocity)
        if not pos:
            return

        # 1. 获取/初始化状态
        aid = id(actor)
        if aid not in self.anim_states:
            self.anim_states[aid] = {
                "state": "idle",    # idle, start_move, loop_move
                "timer": 0.0,
                "face_right": True,
                "frame_idx": 0
            }
        
        anim = self.anim_states[aid]
        
        # 2. 更新朝向 (Flip Logic)
        # 阈值判断：vx > 0.5 右, vx < -0.5 左
        vx = vel.vec.x if vel else 0
        if vx > 0.1:
            anim["face_right"] = True
        elif vx < -0.1:
            anim["face_right"] = False
            
        # 3. 更新状态机 (State Machine)
        # IDLE: 速度小
        # START_MOVE: 速度大，且处于过渡期
        # LOOP_MOVE: 速度大，过渡完成后
        
        is_moving = abs(vx) > 0.1
        current_state = anim["state"]
        
        target_state = current_state
        
        if not is_moving:
            target_state = "idle"
        else:
            # 正在移动
            if current_state == "idle":
                target_state = "start_move" # IDLE -> START
            elif current_state == "start_move":
                # 检查是否播放完 START 动画
                frames = self._get_frames(sprite_info.name, "start_move")
                if anim["frame_idx"] >= len(frames) - 1:
                    target_state = "loop_move" # START -> LOOP
            # elif current_state == "loop_move": 保持 loop
            
        # 状态切换处理
        if target_state != current_state:
            anim["state"] = target_state
            anim["frame_idx"] = 0
            anim["timer"] = 0.0
            
        # 4. 推进动画帧
        anim["timer"] += 1.0 / 60.0 # 假设 60 FPS
        if anim["timer"] >= self.FRAME_DURATION:
            anim["timer"] = 0.0
            anim["frame_idx"] += 1
            
            # 循环处理
            frames = self._get_frames(sprite_info.name, target_state)
            if not frames: # 防御性编程
                return 

            if target_state == "start_move":
                # Start 动作不循环，播完停在最后一帧(或切到 Loop，由上面逻辑处理)
                if anim["frame_idx"] >= len(frames):
                    anim["frame_idx"] = len(frames) - 1
            else:
                # Idle 和 Loop 都是循环的
                anim["frame_idx"] %= len(frames)
                
        # 5. 绘制
        frames = self._get_frames(sprite_info.name, target_state)
        if frames:
            # 安全检查
            idx = min(anim["frame_idx"], len(frames)-1)
            image = frames[idx]
            
            # 镜像翻转
            # 假设素材默认是【向右】的
            # 如果 anim["face_right"] is False (向左)，则翻转
            if not anim["face_right"]:
                image = pygame.transform.flip(image, True, False)
                
            # 绘制中心对齐
            rect = image.get_rect(center=(int(pos.x + sprite_info.offset_x), int(pos.y + sprite_info.offset_y)))
            self.screen.blit(image, rect)
            
    def _get_frames(self, sprite_name: str, state: str) -> list[pygame.Surface]:
        """从 Assets 获取对应状态的帧列表"""
        # 约定：Assets 中存储结构为 dict:
        # assets.enemy_sprites[sprite_name] = { "idle": [f1,f2...], "start_move": [...], "loop_move": [...] }
        if not hasattr(self.assets, "enemy_sprites"):
            return []
            
        sprite_data = self.assets.enemy_sprites.get(sprite_name)
        if not sprite_data:
            return []
            
        return sprite_data.get(state, [])
