# Touhou_KontonSei

一个用 pygame 写的东方风格 STG（弹幕射击游戏）原型，采用简化的 ECS（Actor + Component + System）架构。

## 特性

- 完整的 MVC + ECS 架构设计
- 可选角色系统（博丽灵梦 / 雾雨魔理沙）
- 丰富的弹幕模式（自机狙、N-WAY、环形、螺旋等）
- Boss 战系统（多阶段、符卡、奖励机制）
- 东方风格的游戏机制（擦弹、PoC、死亡炸弹）
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
├── controller/
│   └── game_controller.py         # 主循环，系统调用顺序
│
├── model/                         # 逻辑层（ECS 核心）
│   ├── actor.py                   # Actor 容器（add/get/has）
│   ├── components.py              # 所有组件定义（50+）
│   ├── game_state.py              # 世界状态 + 工厂函数
│   ├── game_config.py             # 配置类（CollectConfig, GrazeConfig 等）
│   ├── collision_events.py        # 碰撞事件类型
│   ├── registry.py                # 通用注册表基础设施
│   ├── bullet_patterns.py         # 弹幕模式系统（5 种）
│   ├── bomb_handlers.py           # 炸弹类型处理器（2 种）
│   ├── shot_handlers.py           # 射击类型处理器（2 种）
│   ├── item_effects.py            # 道具效果系统（4 种）
│   ├── movement_path.py           # 敌人移动路径库
│   ├── enemies.py                 # 敌人工厂（小妖精/大妖精/中Boss）
│   ├── stage.py                   # 关卡事件定义
│   │
│   ├── character/                 # 角色预设系统
│   │   └── __init__.py            # CharacterId, CharacterPreset
│   │
│   ├── bosses/                    # Boss 工厂
│   │   ├── __init__.py
│   │   └── stage1_boss.py         # Stage 1 Boss: 妖精大王
│   │
│   ├── stages/                    # 关卡脚本
│   │   └── stage1.py              # 第一关时间表
│   │
│   └── systems/                   # 逻辑系统（26 个）
│       ├── player_movement.py     # 玩家移动
│       ├── player_shoot.py        # 玩家射击
│       ├── enemy_shoot.py         # 敌人射击
│       ├── movement.py            # 通用移动 + 路径跟随
│       ├── collision.py           # 碰撞检测
│       ├── collision_damage_system.py  # 伤害结算
│       ├── bomb_hit_system.py     # 炸弹命中
│       ├── bomb_system.py         # 炸弹激活
│       ├── graze_system.py        # 擦弹系统
│       ├── item_pickup.py         # 道具拾取
│       ├── item_autocollect.py    # 道具自动吸取
│       ├── player_damage.py       # 玩家受伤/死亡炸
│       ├── enemy_death.py         # 敌人死亡 + 掉落
│       ├── boss_phase_system.py   # Boss 阶段管理
│       ├── boss_movement_system.py # Boss 移动
│       ├── boss_hud_system.py     # Boss HUD 数据聚合
│       ├── task_system.py         # Task 协程系统（关卡/敌人行为脚本）
│       ├── motion_program_system.py # 子弹运动指令系统
│       ├── poc_system.py          # PoC 状态计算
│       ├── gravity.py             # 重力系统
│       ├── lifetime.py            # 生命周期清理
│       ├── boundary_system.py     # 边界处理
│       ├── death_effect.py        # 死亡效果（清弹/重生）
│       ├── render_hint_system.py  # 渲染提示
│       ├── hud_data_system.py     # HUD 数据聚合
│       └── stats_system.py        # 实体统计
│
└── view/                          # 渲染层
    ├── assets.py                  # 资源加载（占位图形）
    └── renderer.py                # 渲染器 + HUD + Boss HUD
```

## 核心架构

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
player_move_system          # 玩家移动
player_shoot_system         # 玩家射击
enemy_shoot_system          # 敌人射击
    ↓
poc_system                  # PoC 状态计算
gravity_system              # 重力
item_autocollect_system     # 道具自动吸取
    ↓
task_system                 # Task 协程系统（关卡/敌人行为脚本）
motion_program_system       # 子弹运动指令系统
boss_movement_system        # Boss 移动
movement_system             # 通用位移更新
boundary_system             # 边界处理
lifetime_system             # 生命周期清理
    ↓
collision_detection_system  # 碰撞检测 → 写入 CollisionEvents
boss_phase_system           # Boss 阶段管理
collision_damage_system     # 伤害结算
bomb_hit_system             # 炸弹命中
graze_system                # 擦弹
item_pickup_system          # 道具拾取
    ↓
player_damage_system        # 玩家受伤/死亡炸判断
bomb_system                 # 炸弹激活
enemy_death_system          # 敌人死亡 + 掉落
player_respawn_visual_system # 重生闪烁
    ↓
render_hint_system          # 渲染提示
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
| `PlayerDamageState` | 受伤/无敌/死亡炸状态 |
| `PlayerRespawnState` | 重生闪烁状态 |
| `ShotConfig` | 射击配置 |
| `BombConfigData` | 炸弹配置 |
| `Shooting` | 射击冷却 |

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
| `BulletGrazeState` | 是否已被擦过 |
| `PlayerBulletTag` | 玩家子弹标记 |
| `EnemyBulletTag` | 敌弹标记 |
| `BombFieldTag` | 炸弹场标记 |
| `Item` | 道具类型 + 数值 |
| `ItemTag` | 道具标记 |

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
| 博丽灵梦 A | 广角扩散弹 + 圆形炸弹 |
| 雾雨魔理沙 A | 窄角高伤直射 + 光束炸弹 |

角色预设包含：移动速度、碰撞半径、射击配置、炸弹配置、初始残机/炸弹等。

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
        shot=ShotConfig(...),
        bomb=BombConfigData(...),
        ...
    )
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
- **Boss 快速测试**：修改 `stage1.py` 中 Boss 出场时间

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

## License

MIT
