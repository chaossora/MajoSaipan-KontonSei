# model/bosses/__init__.py
"""
Boss 工厂函数模块。
每个 Boss 使用装饰器注册到 boss_registry。

Import boss_registry from model.boss_registry to register new bosses.
"""

# 导入 Boss 模块以触发注册
from model.bosses import stage1_boss

__all__: list[str] = ["stage1_boss"]
