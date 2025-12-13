# model/boss_registry.py
"""
Boss factory registry.

Boss factory functions are registered here and can be looked up by boss_id.
Each Boss uses a decorator to register to boss_registry.

Signature: (state: GameState, x: float, y: float) -> Actor
"""
from __future__ import annotations

from .registry import Registry

# Boss 工厂注册表
# 处理函数签名：(state, x, y) -> Actor
boss_registry: Registry[str] = Registry("boss")
