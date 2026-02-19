"""
Node Logic System - Prototype-based execution logic

This module provides the base class for node logic and a registry
for mapping prototypes to logic implementations.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .runtime_graph import RuntimeNode


class BaseNodeLogic(ABC):
    """
    Base class for all node logic implementations.
    
    Each node prototype should have a corresponding logic class that
    inherits from this base and implements the execute method.
    """
    
    @abstractmethod
    async def execute(self, node: 'RuntimeNode', **inputs) -> Dict[str, Any]:
        """
        Execute the node logic.
        
        Args:
            node: The RuntimeNode instance (provides access to ui_content if needed)
            **inputs: Input values keyed by input socket id
        
        Returns:
            Dict mapping output socket ids to their computed values
            
        Example:
            async def execute(self, node, **inputs):
                value_a = inputs.get('input_a', 0)
                value_b = inputs.get('input_b', 0)
                return {'output': value_a + value_b}
        """
        raise NotImplementedError(f"Logic not implemented for {self.__class__.__name__}")
    
    async def validate_inputs(self, node: 'RuntimeNode', **inputs) -> tuple[bool, Optional[str]]:
        """
        Optional: Validate inputs before execution.
        
        Returns:
            (is_valid, error_message)
        """
        return True, None
    
    def on_node_created(self, node: 'RuntimeNode'):
        """Optional: Called when node is first created."""
        pass
    
    def on_node_removed(self, node: 'RuntimeNode'):
        """Optional: Called when node is removed."""
        pass


class NodeLogicRegistry:
    """
    Registry for mapping node prototypes to logic implementations.
    
    Usage:
        registry = NodeLogicRegistry()
        registry.register('math.add', AddNodeLogic)
        
        logic = registry.get_logic('math.add')
        result = await logic.execute(node, a=5, b=3)
    """
    
    def __init__(self):
        self._registry: Dict[str, type[BaseNodeLogic]] = {}
        self._instances: Dict[str, BaseNodeLogic] = {}  # cached instances
    
    def register(self, prototype: str, logic_class: type[BaseNodeLogic]):
        """
        Register a logic class for a prototype.
        
        Args:
            prototype: Node prototype string (e.g. 'simple.value', 'math.add')
            logic_class: Class inheriting from BaseNodeLogic
        """
        if not issubclass(logic_class, BaseNodeLogic):
            raise TypeError(f"{logic_class} must inherit from BaseNodeLogic")
        
        self._registry[prototype] = logic_class
        print(f"Registered logic for prototype '{prototype}': {logic_class.__name__}")
    
    def unregister(self, prototype: str):
        """Remove a prototype from the registry."""
        if prototype in self._registry:
            del self._registry[prototype]
        if prototype in self._instances:
            del self._instances[prototype]
    
    def has_logic(self, prototype: str) -> bool:
        """Check if logic is registered for a prototype."""
        return prototype in self._registry
    
    def get_logic(self, prototype: str) -> Optional[BaseNodeLogic]:
        """
        Get logic instance for a prototype.
        
        Returns cached instance if available, otherwise creates new one.
        """
        if prototype not in self._registry:
            return None
        
        # return cached instance
        if prototype in self._instances:
            return self._instances[prototype]
        
        # create new instance
        logic_class = self._registry[prototype]
        instance = logic_class()
        self._instances[prototype] = instance
        return instance
    
    def get_registered_prototypes(self) -> list[str]:
        """Get list of all registered prototypes."""
        return list(self._registry.keys())
    
    def clear(self):
        """Clear all registered logic."""
        self._registry.clear()
        self._instances.clear()


# Global registry instance
_global_registry = NodeLogicRegistry()


def register_node_logic(prototype: str, logic_class: type[BaseNodeLogic]):
    """
    Convenience function to register logic with the global registry.
    
    Usage:
        register_node_logic('math.add', AddNodeLogic)
    """
    _global_registry.register(prototype, logic_class)


def get_node_logic(prototype: str) -> Optional[BaseNodeLogic]:
    """
    Convenience function to get logic from the global registry.
    
    Usage:
        logic = get_node_logic('math.add')
    """
    return _global_registry.get_logic(prototype)


def get_registry() -> NodeLogicRegistry:
    """Get the global registry instance."""
    return _global_registry
