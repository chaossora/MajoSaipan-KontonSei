import pygame
import model.stages.stage1
from typing import Generator

# 1. 定义一个只有 Boss 的测试剧本
def boss_only_script(ctx) -> Generator[int, None, None]:
    print(">>> 测试模式：直接进入 Boss 战 <<<")
    width = ctx.state.width
    center_x = width / 2
    top_y = 120
    
    yield 60  # 短暂等待进场
    
    try:
        # 直接生成 Boss (Stage 1 Boss)
        boss = ctx.spawn_boss(
            "stage1_boss",
            x=center_x,
            y=top_y,
        )
        
        # 循环直到 Boss 死亡
        from model.components import Health
        while True:
            health = boss.get(Health)
            if health is None or health.hp <= 0:
                break
            yield 1
            
    except ValueError as e:
        print(f"Boss 生成失败: {e}")
        
    print(">>> Boss 战结束 <<<")
    ctx.state.stage.finished = True

# 2. 【关键】偷梁换柱：把 Stage 1 的原版剧本替换成我们的测试剧本
# 这一步只对本次运行生效，不会修改任何源文件
model.stages.stage1.stage1_script = boss_only_script

# 3. 正常启动游戏主程序
# 此时游戏去加载 "stage1_script" 时，其实是在运行我们的 "boss_only_script"
import main

if __name__ == "__main__":
    main.main()