# model/stages/stage1.py
from __future__ import annotations

from typing import List

from ..stage import StageState, StageEvent, StageEventType, WavePattern
from ..components import EnemyKind
from ..game_state import GameState


def setup_stage1(state: GameState) -> None:
    stage = StageState()
    events: List[StageEvent] = []

    width = state.width
    height = state.height
    center_x = width / 2
    top_y = 120

    # 1. t=1.0：左侧横排小妖精（LINE）+ 慢速直线下落
    events.append(StageEvent(
        time=5.0,
        type=StageEventType.SPAWN_WAVE,
        enemy_kind=EnemyKind.FAIRY_SMALL,
        pattern=WavePattern.LINE,
        count=5,
        start_x=80.0,
        start_y=top_y,
        spacing_x=40.0,
        path_name="straight_down_slow",   # 这波用慢速下落路径
        description="第 1 波：横排 + 直线下落",
    ))

    # 2. t=4.0：右侧纵队小妖精（COLUMN）+ SINE 摇摆
    events.append(StageEvent(
        time=10.0,
        type=StageEventType.SPAWN_WAVE,
        enemy_kind=EnemyKind.FAIRY_SMALL,
        pattern=WavePattern.COLUMN,
        count=6,
        start_x=center_x,
        start_y=top_y - 40,
        spacing_y=24.0,
        path_name="sine_down",            # ★ 这波左右摇摆下落
        description="第 2 波：纵队 + 正弦摇摆下落",
    ))

    # 3. t=7.0：中间一扇形大妖精（FAN）+ 快速直线下落
    events.append(StageEvent(
        time=15.0,
        type=StageEventType.SPAWN_WAVE,
        enemy_kind=EnemyKind.FAIRY_LARGE,
        pattern=WavePattern.FAN,
        count=5,
        start_x=center_x,
        start_y=top_y + 40,
        radius=80.0,
        angle_deg=90.0,
        angle_step_deg=15.0,
        path_name="straight_down_fast",   # ★ 这波快速下落
        description="第 3 波：扇形 + 快速下落",
    ))

    # 4. t=10.0：中心螺旋一圈小妖精（SPIRAL）+ 右下斜飞
    events.append(StageEvent(
        time=20.0,
        type=StageEventType.SPAWN_WAVE,
        enemy_kind=EnemyKind.FAIRY_SMALL,
        pattern=WavePattern.SPIRAL,
        count=12,
        start_x=center_x,
        start_y=top_y + 80,
        radius=40.0,
        radius_step=6.0,
        angle_deg=0.0,
        angle_step_deg=30.0,
        path_name="diag_down_right",      # ★ 这波右下斜飞
        description="第 4 波：螺旋 + 斜飞",
    ))

    # 5. t=30.0：第一关 Boss 登场
    events.append(StageEvent(
        time=30.0,
        type=StageEventType.SPAWN_BOSS,
        boss_id="stage1_boss",
        start_x=center_x,
        start_y=top_y,
        description="第一关 Boss：妖精大王",
    ))

    events.sort(key=lambda e: e.time)
    stage.events = events
    stage.time = 0.0
    stage.cursor = 0
    stage.finished = False

    state.stage = stage
