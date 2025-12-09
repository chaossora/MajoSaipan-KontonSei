# model/bosses/__init__.py
"""
Boss 工厂函数模块。
每个 Boss 使用装饰器注册到 boss_registry。
"""
from .stage1_boss import spawn_stage1_boss

__all__ = ["spawn_stage1_boss"]
