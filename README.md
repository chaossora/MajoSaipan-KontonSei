# Touhou_KontonSei

一个用 pygame 写的东方风格 STG（弹幕射击游戏）原型，采用简化的 ECS（Actor + Component + System）架构。

## 特性

- 完整的 MVC + ECS 架构设计
- 可选角色系统（樱羽艾玛 / 二阶堂希罗）
- Task 协程脚本系统（LuaSTG 风格 `yield N` 语义）
- 丰富的弹幕模式（自机狙、N-WAY、环形、螺旋等）
- 子机系统（动态位置、多种射击模式）
- Boss 战系统（多阶段、符卡、奖励机制）
- 东方风格的游戏机制（擦弹、擦弹能量/增强状态、PoC、死亡炸弹）
- 使用注册表模式实现高度可扩展性

## 运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动游戏（交互式选择角色）
python main.py

# 直接指定角色
python main.py -c REIMU_A
python main.py -c MARISA_A
```

**环境要求**：Python 3.10+

## 操作

| 按键 | 功能 |
|------|------|
| 方向键 | 移动 |
| Shift | 低速移动 + 显示判定点/擦弹圈 |
| Z | 射击 |
| X | 炸弹 |

## 目录结构

```
├── main.py                        # 入口，角色选择
├── requirements.txt
│
├── assets/                        # 游戏资源
│   ├── bgm/                       # 背景音乐
│   ├── fonts/                     # 字体
│   ├── sfx/                       # 音效
│   └── sprites/                   # 精灵图
│       ├── backgrounds/           # 背景
│       ├── bullets/               # 子弹
│       ├── characters/            # 角色
│       ├── enemies/               # 敌人
│       ├── items/                 # 道具
│       ├── options/               # 子机
│       ├── vfx/                   # 特效
│       └── ui/                    # 界面
│
├── controller/
│   └── game_controller.py         # 主循环，系统调用顺序
│
├── model/                         # 逻辑层（ECS 核心）
│   ├── actor.py                   # Actor 容器（add/get/has）
│   ├── components.py              # 所有组件定义（114+）
│   ├── game_state.py              # 世界状态 + 工厂函数
│   ├── game_config.py             # 配置类（CollectConfig, GrazeConfig 等）
│   ├── collision_events.py        # 碰撞事件类型
│   ├── registry.py                # 通用注册表基础设施
│   ├── bullet_patterns.py         # 弹幕模式系统（5 种）
│   ├── bomb_handlers.py           # 炸弹类型处理器（3 种：CIRCLE/BEAM/CONVERT）
│   ├── shot_handlers.py           # 射击类型处理器
│   ├── item_effects.py            # 道具效果系统（4 种）
│   ├── movement_path.py           # 敌人移动路径库
│   ├── enemies.py                 # 敌人工厂（小妖精/大妖精/中Boss）
│   ├── stage.py                   # 关卡事件定义
│   ├── option_shot_handlers.py    # 子机射击处理器
│   ├── player_shot_patterns.py    # 玩家射击模式
│   │
│   ├── character/                 # 角色预设系统
│   │   └── __init__.py            # CharacterId, CharacterPreset
│   │
│   ├── bosses/                    # Boss 工厂
│   │   ├── __init__.py
│   │   └── stage1_boss.py         # Stage 1 Boss
│   │
│   ├── scripting/                 # 协程脚本系统
│   │   ├── __init__.py
│   │   ├── task.py                # Task / TaskRunner 协程容器
│   │   ├── context.py             # TaskContext 引擎原语接口
│   │   ├── archetype.py           # BulletArchetype 子弹原型
│   │   ├── motion.py              # MotionProgram 运动指令
│   │   ├── patterns.py            # 弹幕模式辅助函数
│   │   ├── behaviors.py           # 敌人行为脚本
│   │   └── stage_runner.py        # 关卡脚本执行器
│   │
│   ├── stages/                    # 关卡脚本
│   │   └── stage1.py              # 第一关时间表
│   │
│   └── systems/                   # 逻辑系统（30+）
│       ├── player_movement.py     # 玩家移动
│       ├── player_shoot.py        # 玩家射击
│       ├── option_system.py       # 子机系统
│       ├── movement.py            # 通用移动 + 路径跟随
│       ├── collision.py           # 碰撞检测
│       ├── collision_damage_system.py  # 伤害结算
│       ├── bomb_hit_system.py     # 炸弹命中
│       ├── bomb_system.py         # 炸弹激活
│       ├── graze_system.py        # 擦弹系统
│       ├── graze_energy_system.py # 擦弹能量系统
│       ├── item_pickup.py         # 道具拾取
│       ├── item_autocollect.py    # 道具自动吸取
│       ├── player_damage.py       # 玩家受伤/死亡炸
│       ├── enemy_death.py         # 敌人死亡 + 掉落
│       ├── boss_hud_system.py     # Boss HUD 数据聚合
│       ├── task_system.py         # Task 协程系统
│       ├── motion_program_system.py # 子弹运动指令系统
│       ├── homing_bullet_system.py # 追踪子弹系统
│       ├── laser_collision_system.py # 激光碰撞检测
│       ├── laser_motion_system.py # 激光运动更新
│       ├── poc_system.py          # PoC 状态计算
│       ├── gravity.py             # 重力系统
│       ├── lifetime.py            # 生命周期清理
│       ├── boundary_system.py     # 边界处理
│       ├── death_effect.py        # 死亡效果（清弹/重生）
│       ├── vfx_system.py          # 动画/特效系统
│       ├── render_hint_system.py  # 渲染提示
│       ├── hud_data_system.py     # HUD 数据聚合
│       └── stats_system.py        # 实体统计
│
└── view/                          # 渲染层
    ├── assets.py                  # 资源加载
    ├── renderer.py                # 主渲染器 + HUD
    ├── boss_renderer.py           # Boss 动画渲染
    ├── enemy_renderer.py          # 敌人动画渲染
    ├── pause_renderer.py          # 暂停菜单渲染
    └── main_menu.py               # 主菜单
```

## 核心架构

### MVC + ECS 混合架构

项目采用 **MVC（Model-View-Controller）** 与 **ECS（Entity-Component-System）** 的混合架构：

```
┌─────────────────────────────────────────────────────────────┐
│  Controller (controller/)                                   │
│  └─ game_controller.py: 主循环、输入处理、系统调度         │
├─────────────────────────────────────────────────────────────┤
│  Model (model/)                          ← ECS 核心         │
│  ├─ Actor: 实体容器 (add/get/has)                          │
│  ├─ Component: 纯数据 (components.py, 114+ 组件)           │
│  ├─ System: 纯逻辑 (systems/, 30+ 系统)                    │
│  ├─ GameState: 世界状态 + 工厂函数                         │
│  ├─ Registry: 装饰器注册表模式 (12 个)                      │
│  └─ Scripting: 协程脚本系统 (LuaSTG 风格)                  │
├─────────────────────────────────────────────────────────────┤
│  View (view/)                                               │
│  └─ renderer.py, boss_renderer.py, enemy_renderer.py: 渲染  │
└─────────────────────────────────────────────────────────────┘
```

### 脚本系统架构

脚本系统采用三层架构设计，位于 `model/scripting/`：

```
┌─────────────────────────────────────────────────────────────┐
│  脚本层 (Script Layer)                                      │
│  ├─ stages/stage1.py: 关卡脚本                             │
│  ├─ behaviors.py: 敌人行为脚本                              │
│  └─ bosses/stage1_boss.py: Boss 弹幕脚本                   │
│      └─ 使用 yield N 语义编写游戏逻辑                       │
├─────────────────────────────────────────────────────────────┤
│  原语层 (Primitives Layer) - context.py                    │
│  ├─ TaskContext: 脚本 API 接口                              │
│  │   ├─ fire() / fire_aimed() / fire_laser(): 发射弹幕     │
│  │   ├─ spawn_enemy() / spawn_boss(): 生成实体             │
│  │   ├─ run_phase() / run_spell_card(): Boss 阶段管理      │
│  │   └─ move_to() / wait_for_phase_end(): 控制流           │
│  ├─ BulletArchetype: 子弹原型定义 (archetype.py)           │
│  ├─ MotionProgram: 子弹运动指令 (motion.py)                │
│  └─ patterns.py: 弹幕模式辅助函数 (fire_ring, fire_fan)    │
├─────────────────────────────────────────────────────────────┤
│  底层系统 (Runtime Layer)                                   │
│  ├─ Task / TaskRunner: 协程容器 (task.py)                  │
│  ├─ task_system.py: 协程调度执行                           │
│  ├─ motion_program_system.py: 运动指令执行                 │
│  └─ StageRunner: 关卡脚本执行器 (stage_runner.py)          │
└─────────────────────────────────────────────────────────────┘
```

**数据流向**：
```
脚本 (yield N) → TaskRunner → task_system → 原语调用 → 底层系统/ECS
```

### ECS 模式

```
Actor（实体）
   └─ 组件容器，只有 add() / get() / has() 方法

Component（组件）
   └─ 纯数据，定义在 model/components.py

System（系统）
   └─ 纯逻辑，定义在 model/systems/
   └─ 每帧按顺序执行，读写组件数据
```

### 主循环系统调用顺序

`controller/game_controller.py` 中每帧执行：

```
输入轮询 → 写入 InputState 组件
    ↓
task_system                 # Task 协程系统（关卡/敌人行为脚本）
player_move_system          # 玩家移动
option_system               # 子机位置更新
player_shoot_system         # 玩家射击
    ↓
poc_system                  # PoC 状态计算
gravity_system              # 重力
item_autocollect_system     # 道具自动吸取
    ↓
motion_program_system       # 子弹运动指令系统
homing_bullet_system        # 追踪子弹系统
movement_system             # 通用位移更新
boundary_system             # 边界处理
lifetime_system             # 生命周期清理
    ↓
collision_detection_system  # 碰撞检测 → 写入 CollisionEvents
laser_collision_system      # 激光碰撞检测
laser_motion_system         # 激光运动更新
collision_damage_system     # 伤害结算
bomb_hit_system             # 炸弹命中
graze_system                # 擦弹
graze_energy_system         # 擦弹能量累积
item_pickup_system          # 道具拾取
    ↓
player_damage_system        # 玩家受伤/死亡炸判断
bomb_system                 # 炸弹激活
enemy_death_system          # 敌人死亡 + 掉落
player_respawn_visual_system # 重生闪烁
    ↓
render_hint_system          # 渲染提示
vfx_system                  # 动画/特效更新
boss_hud_system             # Boss HUD 聚合
hud_data_system             # 玩家 HUD 聚合
stats_system                # 实体统计
    ↓
renderer.render()           # 渲染
```

## 组件一览

### 物理 / 渲染
| 组件 | 说明 |
|------|------|
| `Position` | 位置 (x, y) |
| `Velocity` | 速度向量 |
| `Gravity` | 重力加速度 |
| `Collider` | 碰撞体 (radius, layer, mask) |
| `SpriteInfo` | 精灵图信息 |
| `Lifetime` | 生命周期倒计时 |

### 玩家
| 组件 | 说明 |
|------|------|
| `PlayerTag` | 玩家标记 |
| `MoveStats` | 移动速度（普通/低速） |
| `FocusState` | 低速状态 |
| `InputState` | 输入状态 |
| `PlayerLife` | 残机数 |
| `PlayerBomb` | 炸弹数 |
| `PlayerPower` | 火力值 |
| `PlayerScore` | 分数 |
| `PlayerGraze` | 擦弹计数 |
| `GrazeEnergy` | 擦弹能量（增强状态） |
| `PlayerDamageState` | 受伤/无敌/死亡炸状态 |
| `PlayerRespawnState` | 重生闪烁状态 |
| `PlayerShotPattern` | 射击模式配置 |
| `BombConfigData` | 炸弹配置 |

### 敌人
| 组件 | 说明 |
|------|------|
| `EnemyTag` | 敌人标记 |
| `EnemyKindTag` | 敌人类型 (FAIRY_SMALL/FAIRY_LARGE/MIDBOSS/BOSS) |
| `Health` | 血量 |
| `EnemyShootingV2` | 敌人射击配置 + 弹幕模式 |
| `EnemyDropConfig` | 掉落配置 |
| `EnemyJustDied` | 死亡标记 |
| `PathFollower` | 路径跟随 |

### Boss
| 组件 | 说明 |
|------|------|
| `BossState` | Boss 核心状态（阶段列表、计时器等） |
| `BossPhase` | 单个阶段定义（HP、时限、弹幕配置） |
| `SpellCardState` | 符卡状态（奖励资格、伤害倍率） |
| `BossMovementState` | Boss 移动状态机 |
| `BossHudData` | Boss HUD 聚合数据 |

### 子弹 / 道具
| 组件 | 说明 |
|------|------|
| `Bullet` | 子弹伤害 |
| `HomingBullet` | 追踪子弹（转向率、速度） |
| `BulletGrazeState` | 是否已被擦过 |
| `BulletBounce` | 子弹反弹（最大次数、当前次数） |
| `PlayerBulletTag` | 玩家子弹标记 |
| `EnemyBulletTag` | 敌弹标记 |
| `BombFieldTag` | 炸弹场标记 |
| `Item` | 道具类型 + 数值 |
| `ItemTag` | 道具标记 |

### 激光
| 组件 | 说明 |
|------|------|
| `LaserState` | 激光状态（类型、宽度、长度、角度、反射等） |
| `LaserTag` | 激光标记 |

### 子机
| 组件 | 说明 |
|------|------|
| `OptionConfig` | 子机配置（数量、伤害、射击模式） |
| `OptionState` | 子机运行状态（当前位置列表） |
| `OptionTag` | 子机标记（槽位索引） |

### 动画 / 特效
| 组件 | 说明 |
|------|------|
| `Animation` | 帧动画组件（帧数、时长、循环） |
| `VfxTag` | 特效标记 |
| `BossAttackAnimation` | Boss 攻击动画状态 |
| `BossAuraState` | Boss 光环状态 |

### HUD / 渲染
| 组件 | 说明 |
|------|------|
| `HudData` | 玩家 HUD 聚合数据 |
| `RenderHint` | 渲染提示（判定点/擦弹圈） |

## 碰撞事件系统

碰撞检测系统每帧将碰撞写入 `CollisionEvents`，后续系统消费这些事件：

| 事件类型 | 说明 |
|----------|------|
| `PlayerBulletHitEnemy` | 玩家子弹命中敌人 |
| `EnemyBulletHitPlayer` | 敌弹命中玩家 |
| `BombHitEnemy` | 炸弹命中敌人 |
| `BombClearedEnemyBullet` | 炸弹清除敌弹 |
| `PlayerPickupItem` | 玩家拾取道具 |
| `PlayerGrazeEnemyBullet` | 玩家擦弹 |

## 碰撞层系统

使用 `CollisionLayer` 位标志进行高效碰撞过滤：

```python
class CollisionLayer(IntFlag):
    PLAYER = auto()
    ENEMY = auto()
    PLAYER_BULLET = auto()
    ENEMY_BULLET = auto()
    ITEM = auto()
```

每个 `Collider` 有 `layer`（自身类型）和 `mask`（可碰撞对象）。

## 注册表系统

使用装饰器模式实现可扩展的注册表：

| 注册表 | 用途 |
|--------|------|
| `enemy_registry` | 敌人工厂函数 (EnemyKind → spawn_xxx) |
| `boss_registry` | Boss 工厂函数 (str → spawn_boss) |
| `bullet_pattern_registry` | 弹幕模式处理器 |
| `bomb_registry` | 炸弹类型处理器 |
| `shot_registry` | 射击类型处理器 |
| `item_effect_registry` | 道具效果处理器 |
| `character_registry` | 角色预设 |
| `wave_pattern_registry` | 波次模式处理器 |
| `path_handler_registry` | 路径处理器 |
| `bullet_archetype_registry` | 子弹原型定义 |
| `option_shot_registry` | 子机射击处理器 |
| `player_shot_pattern_registry` | 玩家射击模式 |

**使用示例**：
```python
@enemy_registry.register(EnemyKind.FAIRY_SMALL)
def spawn_fairy_small(state, x, y, hp=5) -> Actor:
    ...
```

## 弹幕模式

| 模式 | 说明 |
|------|------|
| `AIM_PLAYER` | 自机狙：朝玩家方向发射 |
| `STRAIGHT_DOWN` | 直下：垂直向下 |
| `N_WAY` | 扇形弹：以自机狙方向为中心展开 |
| `RING` | 环形弹：360° 均匀分布 |
| `SPIRAL` | 螺旋弹：环形 + 每次旋转 |

## 角色系统

| 角色 | 特点 |
|------|------|
| 樱羽艾玛（REIMU_A） | 直射弹 + CONVERT 炸弹（将敌弹转为追踪弹）+ 灵梦式子机 |
| 二阶堂希罗（MARISA_A） | 扩散弹 + BEAM 光束炸弹 + 魔理沙式子机 |

角色预设包含：移动速度、碰撞半径、射击模式配置、炸弹配置、子机配置、初始残机/炸弹等。

## 炸弹类型

| 类型 | 说明 |
|------|------|
| `CIRCLE` | 圆形炸弹场，以玩家为中心 |
| `BEAM` | 垂直光束（多段），向上发射 |
| `CONVERT` | 无敌结束后将所有敌弹转换为追踪玩家子弹 |

## Boss 系统

### 阶段类型
| 类型 | 说明 |
|------|------|
| `NON_SPELL` | 非符卡：普通弹幕阶段 |
| `SPELL_CARD` | 符卡：有名称和奖励分数 |
| `SURVIVAL` | 生存符卡：Boss 无敌，玩家需存活 |

### 符卡奖励机制
- 未被击中 + 未使用炸弹 → 击破时获得奖励分数
- 使用炸弹或被击中 → 失去奖励资格

### Boss Bomb 抗性
- 普通杂兵：Bomb 命中即死
- Boss 非符卡：每帧伤害上限 (`bomb_damage_cap`)
- Boss 符卡：可配置完全免疫 (`bomb_spell_immune`)
- 生存符卡：完全无敌

## 关卡系统

### 事件类型
| 类型 | 说明 |
|------|------|
| `SPAWN_WAVE` | 生成敌人波次 |
| `SPAWN_BOSS` | 生成 Boss |

### 波次模式
| 模式 | 说明 |
|------|------|
| `LINE` | 横向一排 |
| `COLUMN` | 纵向一列 |
| `FAN` | 扇形分布 |
| `SPIRAL` | 螺旋分布 |

### 敌人路径
| 路径 | 说明 |
|------|------|
| `straight_down_slow` | 缓慢直线下落 |
| `straight_down_fast` | 快速直线下落 |
| `diag_down_right` | 右下斜飞 |
| `sine_down` | 左右摇摆下落 |

## 道具系统

| 道具 | 效果 |
|------|------|
| `POWER` | +火力值 + 基础分 |
| `POINT` | +分数（高度越高分越多，PoC 线上满分） |
| `LIFE` | +残机 |
| `BOMB` | +炸弹 |

### 自动吸取触发条件
- 玩家在 PoC 线上方
- 满 Power（可配置）
- 使用炸弹时

## 激光系统

| 激光类型 | 说明 |
|----------|------|
| `STRAIGHT` | 直线激光 |
| `SINE_WAVE` | 正弦波形激光 |

**激光特性**：
- 预热阶段（warmup）：激光变宽前的准备期
- 旋转：支持角速度旋转
- 反射：碰到边界可反射
- 线段碰撞检测：使用点到线段距离判断命中

## 子机系统

子机（Option）是跟随玩家的副武器单位。

| 射击模式 | 说明 |
|----------|------|
| `REIMU_STYLE` | 普通：直射，低速：追踪 |
| `MARISA_STYLE` | 普通：扩散，低速：直射 |
| `STRAIGHT` | 始终直射 |
| `HOMING` | 始终追踪 |
| `SPREAD` | 始终扇形 |

**子机特性**：
- 动态位置：普通/低速模式下位置不同
- Power 联动：根据火力值决定子机数量
- 平滑过渡：位置切换时有插值动画

## 擦弹能量系统

擦弹不仅加分，还会积累能量：

- **能量积累**：每次擦弹 +5 能量（可配置）
- **增强状态**：能量满（100）时自动触发
- **增强效果**：火力增强、射击模式变化
- **能量消耗**：增强状态下能量持续消耗
- **能量衰减**：停止擦弹后能量会缓慢衰减

## 协程脚本系统

基于 Python 生成器的协程系统，位于 `model/scripting/`，提供 LuaSTG 风格的脚本能力。

### yield N 语义

- `yield 1` = 等待 1 帧，下一帧继续
- `yield 60` = 等待 60 帧（约 1 秒）

### 核心组件

| 组件 | 说明 |
|------|------|
| `Task` | 单个协程任务 |
| `TaskRunner` | 协程执行器组件 |
| `TaskContext` | 引擎原语接口 |
| `BulletArchetype` | 子弹原型系统 |
| `MotionProgram` | 子弹运动指令 |

### TaskContext 主要方法

```python
# 发射子弹
ctx.fire(x, y, speed, angle, archetype="basic")
ctx.fire_aimed(x, y, speed, archetype="basic")  # 自机狙

# 发射激光
ctx.fire_laser(x, y, angle, width, length, laser_type=LaserType.STRAIGHT)

# 生成敌人/Boss
ctx.spawn_enemy(kind, x, y, hp=10, behavior=None)
ctx.spawn_boss(boss_id, x, y)

# Boss 阶段管理
ctx.run_phase(pattern, timeout, hp)
ctx.run_spell_card(name, bonus, pattern, timeout, hp)

# 移动
ctx.move_to(x, y, frames)  # 平滑移动
ctx.move_to_player_x(y, frames)  # 移动到玩家 X 坐标

# 等待
ctx.wait_for_phase_end()
ctx.enemies_alive()  # 获取存活敌人数
```

### MotionProgram 指令

子弹运动指令系统，可实现复杂弹道：

| 指令 | 说明 |
|------|------|
| `Wait(frames)` | 等待帧数 |
| `SetSpeed(speed)` | 设置速度 |
| `SetAngle(angle)` | 设置角度 |
| `AccelerateTo(speed, frames)` | 加速到目标速度 |
| `TurnTo(angle, frames)` | 转向到目标角度 |
| `AimPlayer()` | 转向玩家 |

## 扩展指南

### 添加新角色

在 `model/character/__init__.py` 中：

```python
@character_registry.register(CharacterId.NEW_CHAR)
def _new_char() -> CharacterPreset:
    return CharacterPreset(
        name="新角色",
        description="角色描述",
        speed_normal=220.0,
        speed_focus=120.0,
        shot_pattern=PlayerShotPatternConfig(
            kind=PlayerShotPatternKind.SPREAD,
            cooldown=0.08,
            bullet_speed=520.0,
            ...
        ),
        bomb=BombConfigData(bomb_type=BombType.CIRCLE, ...),
        option=OptionConfig(
            option_shot_kind=OptionShotKind.REIMU_STYLE,
            max_options=4,
            ...
        ),
        ...
    )
```

### 添加新子弹原型

在 `model/scripting/archetype.py` 中：

```python
register_archetype(BulletArchetype(
    id="my_bullet",
    damage=2,
    sprite="my_sprite",
    radius=6.0,
    lifetime=30.0,
))

# 使用
ctx.fire(x, y, speed, angle, archetype="my_bullet")
```

### 添加新子机射击模式

在 `model/option_shot_handlers.py` 中：

```python
@option_shot_registry.register(OptionShotKind.NEW_STYLE)
def _option_shot_new(speed: float, is_focusing: bool, target_angle: float) -> List[ShotData]:
    # 返回射击数据列表
    if is_focusing:
        return [ShotData(velocity=..., offset=...)]
    else:
        return [ShotData(...), ShotData(...)]
```

### 添加新弹幕模式

在 `model/bullet_patterns.py` 中：

```python
@bullet_pattern_registry.register(BulletPatternKind.NEW_PATTERN)
def _pattern_new(state, shooter_pos, config, pattern_state) -> List[Vector2]:
    # 返回子弹速度向量列表
    return [Vector2(...), ...]
```

### 添加新 Boss

在 `model/bosses/` 中创建新文件：

```python
@boss_registry.register("new_boss")
def spawn_new_boss(state: GameState, x: float, y: float) -> Actor:
    boss = Actor()
    boss.add(BossState(
        boss_name="新Boss",
        phases=[
            BossPhase(phase_type=PhaseType.NON_SPELL, hp=500, duration=30.0, ...),
            BossPhase(phase_type=PhaseType.SPELL_CARD, hp=800, duration=45.0, spell_name="符卡名", ...),
        ],
        ...
    ))
    ...
    return boss
```

### 添加新关卡

在 `model/stages/` 中创建新文件，定义 Task 生成器函数作为关卡脚本：

```python
def stage_script(ctx: TaskContext) -> Generator[int, None, None]:
    # 生成敌人波次
    ctx.spawn_enemy(EnemyKind.FAIRY_SMALL, x=100, y=50, behavior=fairy_behavior_1)
    yield 60  # 等待 60 帧（1 秒）
    
    # 等待敌人清空
    while ctx.enemies_alive() > 0:
        yield 1
    
    # 生成 Boss
    ctx.spawn_boss("boss_id", x=200, y=100)
```

## 调试提示

- **关闭敌人生成**：修改 `stages/stage1.py` 中的事件表
- **验证碰撞**：`game_controller.py` 初始化时会掉落测试道具
- **实体统计**：HUD 底部显示各类实体数量

## 数据流示意图

```
[输入] → InputState 组件
    ↓
玩家/敌人射击系统 → 生成子弹（带 Collider/Tag/Bullet）
    ↓
movement_system 按 Velocity 更新 Position
    ↓
collision_detection_system
    ├─ 玩家弹 vs 敌人 → PlayerBulletHitEnemy
    ├─ 敌弹 vs 玩家  → EnemyBulletHitPlayer
    ├─ 炸弹 vs 敌人  → BombHitEnemy
    ├─ 炸弹 vs 敌弹  → BombClearedEnemyBullet
    └─ 玩家 vs 道具  → PlayerPickupItem
    ↓
伤害/效果系统消费 CollisionEvents
    └─ 更新 Health / 标记 EnemyJustDied / 更新玩家状态
    ↓
enemy_death_system → 掉落 Item
    ↓
lifetime_system → 清理过期实体
    ↓
renderer → 根据 Position/SpriteInfo/HudData 绘制
```

## 依赖

- Python 3.10+
- pygame

