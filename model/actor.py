"""
Actor 实体类：ECS 架构中的实体容器。
"""
from __future__ import annotations

from typing import Dict, Type, TypeVar, Optional


T = TypeVar("T")


class Actor:
    """
    游戏对象实体，作为组件容器：
    - add(component): 添加组件
    - get(ComponentType): 获取组件
    - has(ComponentType): 检查是否有组件
    """

    def __init__(self) -> None:
        self._components: Dict[Type, object] = {}

    def add(self, component: object) -> None:
        """添加组件到实体"""
        self._components[type(component)] = component

    def get(self, comp_type: Type[T]) -> Optional[T]:
        """获取指定类型的组件"""
        return self._components.get(comp_type)  # type: ignore[return-value]

    def has(self, comp_type: Type) -> bool:
        """检查实体是否拥有指定类型的组件"""
        return comp_type in self._components
