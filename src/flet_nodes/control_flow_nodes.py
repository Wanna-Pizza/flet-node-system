"""
Control Flow Node Logic - Implementations of control flow nodes

This module provides the logic for all control flow node types:
- Start: Entry point
- If: Conditional branching
- ForEach: Loop over items (includes the functionality formerly
  provided by a separate Sequence node)
- While: Conditional loop
- Break: Exit loop
- Continue: Skip to next iteration

The old "flow.sequence" node has been deprecated and its behavior
is effectively no‑op; ForEach now connects body and iterator directly.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from .node_logic import BaseNodeLogic
from .execution_context import ExecutionContext, BreakException, ContinueException

if TYPE_CHECKING:
    from .runtime_graph import RuntimeNode


class StartNodeLogic(BaseNodeLogic):
    """
    Start node - Entry point for execution.
    
    No inputs.
    Outputs: exec_out (EXEC)
    """
    
    async def execute(
        self, 
        node: 'RuntimeNode',
        context: Optional[ExecutionContext] = None,
        **inputs
    ) -> Dict[str, Any]:
        """Execute start node - just passes through."""
        return {}


# SequenceNodeLogic is retained for backward compatibility but is not
# registered by default. The node has no behavior and is effectively a
# no-op; its purpose has been superseded by simplifying flows such as
# ForEach which can be connected directly without a separate sequence node.
#
# class SequenceNodeLogic(BaseNodeLogic):
#     """
#     Sequence node - Execute a sequence of connected nodes.
#     
#     Inputs: exec_in (EXEC)
#     Outputs: exec_out (EXEC)
#     
#     The sequence node doesn't do computation itself - it just coordinates
#     the execution order of its connected nodes.
#     """
#     
#     async def execute(
#         self, 
#         node: 'RuntimeNode',
#         context: Optional[ExecutionContext] = None,
#         **inputs
#     ) -> Dict[str, Any]:
#         """Execute sequence node."""
#         return {}

class IfNodeLogic(BaseNodeLogic):
    """
    If node - Conditional branching.
    
    Inputs: 
    - exec_in (EXEC)
    - condition (DATA: bool)
    
    Outputs:
    - exec_true (EXEC): executed if condition is True
    - exec_false (EXEC): executed if condition is False
    """
    
    async def execute(
        self,
        node: 'RuntimeNode',
        context: Optional[ExecutionContext] = None,
        condition: Any = False,
        **inputs
    ) -> Dict[str, Any]:
        """
        Execute if node - return which branch to follow.
        
        Returns {'next_exec': 'exec_true'} or {'next_exec': 'exec_false'}
        """
        # evaluate condition
        should_execute_true = bool(condition)
        
        if should_execute_true:
            return {'next_exec': 'exec_true'}
        else:
            return {'next_exec': 'exec_false'}


class ForEachNodeLogic(BaseNodeLogic):
    """
    ForEach node - Loop over items (with automatic iteration management).
    
    Inputs:
    - exec_in (EXEC)
    - items (DATA: list)
    
    Outputs:
    - loop_body (EXEC): executed for each item
    - completed (EXEC): executed after all items
    
    Sets context.variables['item'] to current item in each iteration.
    
    Note: After loop_body, connect to foreach.iterator which manages iterations.
    """
    
    async def execute(
        self,
        node: 'RuntimeNode',
        context: Optional[ExecutionContext] = None,
        items: Any = None,
        **inputs
    ) -> Dict[str, Any]:
        """
        Initialize ForEach loop.
        
        Returns signal to follow loop_body for first iteration.
        Iteration management is handled by foreach.iterator node.
        """
        if context is None:
            context = ExecutionContext()
        
        if items is None:
            items = []
        
        # ensure items is iterable
        try:
            items = list(items)
        except (TypeError, ValueError):
            # if not iterable, treat as single-item list
            items = [items]
        
        # if no items, skip to completed
        if not items:
            return {'next_exec': 'completed'}
        
        # push loop onto stack
        context.push_loop(node.id)
        
        # store items for iteration
        context.set_shared_state(f"{node.id}:items", items)
        context.set_shared_state(f"{node.id}:index", 0)
        
        # set first item and index
        context.set_variable('item', items[0])
        context.set_variable('loop_index', 0)
        
        return {'next_exec': 'loop_body'}


class WhileNodeLogic(BaseNodeLogic):
    """
    While node - Conditional loop.
    
    Inputs:
    - exec_in (EXEC)
    - condition (DATA: bool)
    
    Outputs:
    - loop_body (EXEC): executed while condition is True
    - completed (EXEC): executed after loop exits
    """
    
    async def execute(
        self,
        node: 'RuntimeNode',
        context: Optional[ExecutionContext] = None,
        condition: Any = False,
        **inputs
    ) -> Dict[str, Any]:
        """
        Execute while node.
        
        Returns {'next_exec': 'loop_body'} or {'next_exec': 'completed'}
        """
        if context is None:
            context = ExecutionContext()
        
        # evaluate condition
        should_continue = bool(condition)
        
        if should_continue:
            # push loop if first iteration
            if node.id not in context.loop_stack:
                context.push_loop(node.id)
            return {'next_exec': 'loop_body'}
        else:
            # pop loop if we're exiting
            if context.get_current_loop() == node.id:
                context.pop_loop()
            return {'next_exec': 'completed'}


class BreakNodeLogic(BaseNodeLogic):
    """
    Break node - Exit the current loop.
    
    Inputs: exec_in (EXEC)
    Outputs: none
    
    Raises BreakException to signal loop exit.
    The ControlFlowExecutor handles this by jumping to the loop's completed output.
    """
    
    async def execute(
        self,
        node: 'RuntimeNode',
        context: Optional[ExecutionContext] = None,
        **inputs
    ) -> Dict[str, Any]:
        """Execute break node - request exit from current loop."""
        if context is None:
            context = ExecutionContext()
        
        if not context.is_in_loop():
            raise RuntimeError("Break outside of loop")
        
        context.request_break()
        
        # return to loop completion
        current_loop_id = context.get_current_loop()
        return {'next_exec': f'loop_{current_loop_id}_completed'}


class ContinueNodeLogic(BaseNodeLogic):
    """
    Continue node - Skip to next loop iteration.
    
    Inputs: exec_in (EXEC)
    Outputs: none
    
    Raises ContinueException to signal loop continuation.
    The ControlFlowExecutor handles this by jumping to the loop start.
    """
    
    async def execute(
        self,
        node: 'RuntimeNode',
        context: Optional[ExecutionContext] = None,
        **inputs
    ) -> Dict[str, Any]:
        """Execute continue node - request next iteration."""
        if context is None:
            context = ExecutionContext()
        
        if not context.is_in_loop():
            raise RuntimeError("Continue outside of loop")
        
        context.request_continue()
        
        # return to loop start
        current_loop_id = context.get_current_loop()
        return {'next_exec': f'loop_{current_loop_id}_start'}
