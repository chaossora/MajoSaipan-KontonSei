import pygame
from model.game_state import GameState
from model.components import Velocity, SpriteInfo, Position

class BossRenderer:
    def __init__(self, screen: pygame.Surface, assets):
        self.screen = screen
        self.assets = assets
        
        # 动画状态缓存: { entity_id: { "state": "idle", "timer": 0.0, "face_right": True } }
        self.anim_states = {}
        
        # 动画配置
        self.FRAME_DURATION = 0.1  # 加快帧率 (0.1 -> 0.06)
        
    def render(self, actor, state: GameState):
        """渲染 Boss"""
        sprite_info = actor.get(SpriteInfo)
        if not sprite_info or not sprite_info.visible:
            return
            
        pos = actor.get(Position)
        if not pos:
            return

        # 1. 获取/初始化状态
        aid = id(actor)
        # 1. 获取/初始化状态
        aid = id(actor)
        if aid not in self.anim_states:
            self.anim_states[aid] = {
                "state": "idle",    # idle, start_move, loop_move
                "timer": 0.0,
                "face_right": True,
                "frame_idx": 0,
                "last_x": pos.x,  # 记录上一帧 X 坐标
                "last_y": pos.y,  # 记录上一帧 Y 坐标
                "stop_counter": 0, # 停止计时器 (用于防抖动)
                "aura_timer": 0.0,
                "aura_frame_idx": 0
            }
        
        anim = self.anim_states[aid]
        
        # 2. 计算速度与朝向 (Flip Logic)
        # 通过位置差计算速度
        current_x = pos.x
        current_y = pos.y
        last_x = anim.get("last_x", current_x)
        last_y = anim.get("last_y", current_y)
        
        dx = current_x - last_x
        dy = current_y - last_y
        
        anim["last_x"] = current_x
        anim["last_y"] = current_y
        
        # 阈值判断：dx > 0.2 表示有明显【横向】移动，用于翻转
        if dx > 0.2:
            anim["face_right"] = True
        elif dx < -0.2:
            anim["face_right"] = False
            
        # 3. 更新状态机 (State Machine)
        # 综合判断 X 和 Y 的移动
        speed_sq = dx*dx + dy*dy
        
        # 降低阈值并增加迟滞 (Hysteresis)
        # 只要有一点点移动 (0.05px/frame) 就视为移动中
        # 且必须连续 10 帧静止才切换回 Idle
        current_is_moving = speed_sq > 0.0025
        
        # 3. 更新状态机 (State Machine)
        # 综合判断 X 和 Y 的移动
        speed_sq = dx*dx + dy*dy
        
        # 降低阈值并增加迟滞 (Hysteresis)
        current_is_moving = speed_sq > 0.0025
        
        if current_is_moving:
            anim["stop_counter"] = 0
            is_moving = True  # 只要动了就是动
        else:
            anim["stop_counter"] += 1
            # 只有连续静止 5 帧，才视为"打算停下" (User Request: 立即倒放，减少迟滞)
            is_moving = anim["stop_counter"] < 5
        
        current_state = anim["state"]
        target_state = current_state
        
        # 状态流转逻辑更新：支持 end_move 过渡
        # 状态流转逻辑更新：支持 end_move 过渡
        # [User Request] 测试模式：全部强制为待机动作 (只有第一帧)
        # target_state = "idle"
        
        # 原有逻辑暂时屏蔽

        if not is_moving:
            # 判定为停止
            if current_state in ("loop_move", "start_move"):
                # 如果正在飞，切换到回正动作
                target_state = "end_move"
            elif current_state == "end_move":
                # 检查回正动作是否播完
                frames = self._get_frames(sprite_info.name, "end_move")
                if anim["frame_idx"] >= len(frames) - 1:
                    target_state = "idle"  # 播完变回 IDLE
            # else: 已经是 idle，保持
        else:
            # 判定为移动
            if current_state in ("idle", "end_move"):
                # 如果是静止或正在回正，重新开始移动
                target_state = "start_move"
            elif current_state == "start_move":
                # 起飞动作播放完 -> 循环
                frames = self._get_frames(sprite_info.name, "start_move")
                if anim["frame_idx"] >= len(frames) - 1:
                    target_state = "loop_move"
            # else: 已经是 loop_move，保持

            
        # 状态切换处理
        if target_state != current_state:
            # 尝试平滑过渡：Start <-> End
            # 只有这两个状态互转时才插值帧索引，实现"倒带"效果
            handled = False
            if (current_state == "start_move" and target_state == "end_move") or \
               (current_state == "end_move" and target_state == "start_move"):
                # 获取当前动画的总帧数 (假设 start 和 end 长度一致)
                current_frames = self._get_frames(sprite_info.name, current_state)
                total_frames = len(current_frames)
                if total_frames > 0:
                    # 映射索引：i -> N-1-i (倒带)
                    # 限制 old_idx 范围防越界
                    old_idx = min(anim["frame_idx"], total_frames - 1)
                    new_idx = total_frames - 1 - old_idx
                    anim["frame_idx"] = max(0, new_idx)
                    handled = True
            
            # 如果不是平滑过渡情况，重置动画
            if not handled:
                anim["frame_idx"] = 0
            
            anim["state"] = target_state
            anim["timer"] = 0.0
            
        # 4. 推进动画帧
        anim["timer"] += 1.0 / 60.0 # 假设 60 FPS
        if anim["timer"] >= self.FRAME_DURATION:
            anim["timer"] = 0.0
            anim["frame_idx"] += 1
            
            # 循环处理
            frames = self._get_frames(sprite_info.name, target_state)
            if not frames: 
                return 

            if target_state in ("start_move", "end_move"):
                # 过渡动作不循环
                if anim["frame_idx"] >= len(frames):
                    anim["frame_idx"] = len(frames) - 1
            else:
                # Idle 和 Loop 循环
                anim["frame_idx"] %= len(frames)
                
        # 4.5 更新并渲染气场特效 (Aura)
        if hasattr(self.assets, "vfx") and "boss_aura" in self.assets.vfx:
            anim["aura_timer"] = anim.get("aura_timer", 0.0) + 1.0/60.0
            if anim["aura_timer"] >= 0.1: # 0.1s per frame
                anim["aura_timer"] = 0.0
                anim["aura_frame_idx"] = anim.get("aura_frame_idx", 0) + 1
            
            aura_frames = self.assets.vfx["boss_aura"]
            if aura_frames:
                idx = anim.get("aura_frame_idx", 0) % len(aura_frames)
                aura_img = aura_frames[idx]
                if aura_img:
                     rect = aura_img.get_rect(center=(int(pos.x), int(pos.y)))
                     self.screen.blit(aura_img, rect)

        # 5. 绘制
        frames = self._get_frames(sprite_info.name, target_state)
        if frames:
            # 安全检查 & 待机特殊处理
            # 待机状态：只取第一帧（静态），且不进行镜像翻转
            if target_state == "idle":
                idx = 0
            else:
                idx = min(anim["frame_idx"], len(frames)-1)
            
            image = frames[idx]
            
            # 镜像翻转
            # 仅在非待机状态下翻转 (end_move 属于侧身动作，也需要翻转)
            if not anim["face_right"] and target_state != "idle":
                image = pygame.transform.flip(image, True, False)
                
            # 绘制中心对齐
            # 使用 center=(pos.x, pos.y) 自动处理居中，加上 sprite_info.offset 进行微调
            # 如果 offset 是 0, 0，则图片中心对齐 actor 位置
            rect = image.get_rect(center=(int(pos.x + sprite_info.offset_x), int(pos.y + sprite_info.offset_y)))
            self.screen.blit(image, rect)
            
    def _get_frames(self, sprite_name: str, state: str) -> list[pygame.Surface]:
        """从 Assets 获取对应状态的帧列表"""
        # 复用 enemy_sprites 字典
        if not hasattr(self.assets, "enemy_sprites"):
            return []
            
        sprite_data = self.assets.enemy_sprites.get(sprite_name)
        if not sprite_data:
            return []
            
        if state == "end_move":
            # 动态生成回正动画：复用 start_move 并倒放
            start_frames = sprite_data.get("start_move", [])
            return list(reversed(start_frames))
            
        return sprite_data.get(state, [])
