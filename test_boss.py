import pygame
import model.stages.stage1
from typing import Generator

# 1. 定义一个只有 Boss 的测试剧本
def boss_only_script(ctx) -> Generator[int, None, None]:
    print(">>> 测试模式：直接进入 Boss 战 <<<")
    width = ctx.state.width
    center_x = width / 2
    top_y = 120
    
    # yield 60  # Short wait
    yield from ctx.wait(3.0)
    
    # Run Dialogue
    yield from model.stages.stage1.run_dialogue(ctx)
    
    # Cut-in (Removed per request)
    # ctx.state.cutin.start(name="boss_cutin", control_bgm=True)
    # yield from ctx.wait(2.0)
    
    try:
        # 直接生成 Boss (Stage 1 Boss)
        boss = ctx.spawn_boss(
            "stage1_boss",
            x=center_x,
            y=top_y,
        )
        
        # 循环直到 Boss 脚本结束
        from model.scripting.task import TaskRunner
        runner = boss.get(TaskRunner)
        while runner and runner.has_active_tasks():
            yield 1
            
    except ValueError as e:
        print(f"Boss 生成失败: {e}")
        
    # Wait a bit
    yield from ctx.wait(1.0)
    
    # Run Post-Battle Dialogue
    yield from model.stages.stage1.run_post_battle_dialogue(ctx)
    
    # Remove boss & Spawn Items
    if 'boss' in locals() and boss:
        from model.components import Position
        pos = boss.get(Position)
        bx, by = (pos.x, pos.y) if pos else (center_x, top_y)
        
        ctx.state.remove_actor(boss)
        model.stages.stage1.spawn_stage_clear_items(ctx, bx, by)
        ctx.play_sound("explosion")

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