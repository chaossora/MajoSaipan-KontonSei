"""
Scripting module for the danmaku engine.

Provides Task-based coroutine system for stage/boss/enemy scripting.
"""
from .task import Task, TaskRunner
from .context import TaskContext
from .patterns import fire_ring, fire_fan, fire_spiral, fire_aimed
from .motion import (
    MotionInstructionKind,
    MotionInstruction,
    MotionProgram,
    MotionBuilder,
    normalize_angle,
    shortest_arc,
    angle_to_vector,
    vector_to_angle,
)
from .archetype import (
    BulletArchetype,
    register_archetype,
    get_archetype,
    clear_archetypes,
    get_all_archetypes,
    register_default_archetypes,
)
from .stage_runner import StageRunner
from .behaviors import (
    fairy_behavior_1,
    fairy_behavior_sine,
    fairy_behavior_straight,
    fairy_behavior_diagonal,
)

__all__ = [
    "Task",
    "TaskRunner",
    "TaskContext",
    "StageRunner",
    "fire_ring",
    "fire_fan",
    "fire_spiral",
    "fire_aimed",
    # Motion system
    "MotionInstructionKind",
    "MotionInstruction",
    "MotionProgram",
    "MotionBuilder",
    "normalize_angle",
    "shortest_arc",
    "angle_to_vector",
    "vector_to_angle",
    # Archetype system
    "BulletArchetype",
    "register_archetype",
    "get_archetype",
    "clear_archetypes",
    "get_all_archetypes",
    "register_default_archetypes",
    # Enemy behaviors
    "fairy_behavior_1",
    "fairy_behavior_sine",
    "fairy_behavior_straight",
    "fairy_behavior_diagonal",
]
