"""
Execution Context - Maintains state during control flow execution

This module provides the ExecutionContext class that tracks loop state,
variables, and other context needed for imperative control flow execution.
"""

from typing import Any, Dict, List, Optional


class BreakException(Exception):
    """Exception raised to break out of a loop."""
    pass


class ContinueException(Exception):
    """Exception raised to continue to next loop iteration."""
    pass


class ExecutionContext:
    """
    Maintains execution state during control flow execution.
    
    Tracks:
    - Function/local variables
    - Loop stack for nested loops
    - Shared state between nodes
    - Break/Continue flow control
    """
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}  # variable storage
        self.loop_stack: List[str] = []  # stack of loop node ids
        self.shared_state: Dict[str, Any] = {}  # shared state between nodes
        self._break_requested = False
        self._continue_requested = False
    
    def set_variable(self, name: str, value: Any):
        """Set a variable value."""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable value."""
        return self.variables.get(name, default)
    
    def has_variable(self, name: str) -> bool:
        """Check if a variable exists."""
        return name in self.variables
    
    def push_loop(self, loop_node_id: str):
        """Push a loop onto the stack."""
        self.loop_stack.append(loop_node_id)
    
    def pop_loop(self) -> Optional[str]:
        """Pop a loop from the stack."""
        if self.loop_stack:
            return self.loop_stack.pop()
        return None
    
    def get_current_loop(self) -> Optional[str]:
        """Get the current (innermost) loop node id."""
        if self.loop_stack:
            return self.loop_stack[-1]
        return None
    
    def is_in_loop(self) -> bool:
        """Check if currently inside a loop."""
        return len(self.loop_stack) > 0
    
    def request_break(self):
        """Request breaking out of current loop."""
        self._break_requested = True
    
    def request_continue(self):
        """Request continuing to next loop iteration."""
        self._continue_requested = True
    
    def is_break_requested(self) -> bool:
        """Check if break was requested."""
        return self._break_requested
    
    def is_continue_requested(self) -> bool:
        """Check if continue was requested."""
        return self._continue_requested
    
    def clear_flow_control(self):
        """Clear break/continue flags."""
        self._break_requested = False
        self._continue_requested = False
    
    def set_shared_state(self, key: str, value: Any):
        """Set shared state value."""
        self.shared_state[key] = value
    
    def get_shared_state(self, key: str, default: Any = None) -> Any:
        """Get shared state value."""
        return self.shared_state.get(key, default)
    
    def clear(self):
        """Clear all context state."""
        self.variables.clear()
        self.loop_stack.clear()
        self.shared_state.clear()
        self.clear_flow_control()
