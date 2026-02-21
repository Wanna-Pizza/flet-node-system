"""
Async Graph Executor - Pull-based evaluation engine

This module implements the async execution engine that evaluates nodes
using recursive pull-based evaluation with result caching.
"""

import asyncio
from typing import Any, Dict, Optional, Set
from .runtime_graph import Graph, RuntimeNode, ExecutionState, SocketKind
from .node_logic import get_node_logic


class ExecutionError(Exception):
    """Raised when node execution fails."""
    pass


class CyclicDependencyError(ExecutionError):
    """Raised when a cycle is detected during execution."""
    pass


class AsyncGraphExecutor:
    """
    Async graph executor using pull-based evaluation.
    
    Features:
    - Recursive async execution
    - Result caching (memoization)
    - Parallel dependency evaluation
    - Cycle detection
    - Error handling and state tracking
    
    Usage:
        executor = AsyncGraphExecutor(graph)
        result = await executor.execute('node_id')
    """
    
    def __init__(self, graph: Graph):
        self.graph = graph
        self._execution_stack: Set[str] = set()  # for cycle detection during execution
        self._history: list[tuple[str, Dict[str, Any]]] = []  # record (node_id, result) in order
    
    async def execute(self, node_id: str, clear_cache: bool = False, context: Optional[object] = None) -> Dict[str, Any]:
        """
        Execute a node and return its outputs.

        Args:
            node_id: ID of the node to execute
            clear_cache: If True, clear all cached results before execution
            context: Optional execution context passed to node logic (if supported)

        Returns:
            Dict mapping output socket ids to their values

        Raises:
            ExecutionError: If node execution fails
            CyclicDependencyError: If a cycle is detected
        """
        # automatically invalidate caches if any UI-backed node exists
        if clear_cache or any(getattr(n, 'ui_content', None) is not None for n in self.graph.nodes.values()):
            self.graph.clear_all_caches()

        if node_id not in self.graph.nodes:
            raise ExecutionError(f"Node {node_id} not found in graph")

        # validate graph before execution
        is_valid, error_msg = self.graph.validate()
        if not is_valid:
            raise ExecutionError(f"Graph validation failed: {error_msg}")

        try:
            result = await self._execute_node(node_id, context=context)
            return result
        except Exception as e:
            # mark node as error
            if node_id in self.graph.nodes:
                self.graph.nodes[node_id].state = ExecutionState.ERROR
                self.graph.nodes[node_id].error = e
            raise
        finally:
            self._execution_stack.clear()

    def get_execution_history(self) -> list[tuple[str, Dict[str, Any]]]:
        """Return the recorded history of node executions (node_id, result)."""
        return list(self._history)
    
    async def _execute_node(self, node_id: str, context: Optional[object] = None) -> Dict[str, Any]:
        """
        Internal recursive execution method.
        
        Algorithm:
        1. Check if result is cached -> return it
        2. Check for cycles
        3. Mark node as RUNNING
        4. Collect dependencies
        5. Execute dependencies in parallel
        6. Gather input values
        7. Execute node logic
        8. Cache result
        9. Update output sockets
        10. Mark as DONE
        11. Return result
        """
        node = self.graph.nodes[node_id]
        
        # Step 1: Return cached result if available
        if node.cached_result is not None and node.state == ExecutionState.DONE:
            return node.cached_result
        
        # Step 2: Cycle detection
        if node_id in self._execution_stack:
            raise CyclicDependencyError(f"Cyclic dependency detected involving node {node_id}")
        
        self._execution_stack.add(node_id)
        
        try:
            # Step 3: Mark as running
            node.set_state(ExecutionState.RUNNING)
            
            # Step 4: Collect DATA dependencies only (ignore EXEC connections)
            dependencies = self.graph.get_dependencies(node_id, kind=SocketKind.DATA)
            
            # Step 5: Execute DATA dependencies in parallel using asyncio.gather
            if dependencies:
                await asyncio.gather(*[self._execute_node(dep_id, context=context) for dep_id in dependencies])
            
            # Step 6: Gather input values from connected outputs
            input_values = {}
            for input_id, input_socket in node.inputs.items():
                if input_socket.connected_from is not None:
                    # retrieve value from connected output socket
                    input_values[input_id] = input_socket.connected_from.value
                else:
                    # use default value
                    input_values[input_id] = input_socket.default
            
            # Step 7: Execute node logic
            logic = get_node_logic(node.prototype)
            
            if logic is None:
                # no logic registered - return empty result (stub node)
                result = {}
            else:
                # validate inputs if logic provides validation
                is_valid, error_msg = await logic.validate_inputs(node, **input_values)
                if not is_valid:
                    raise ExecutionError(f"Input validation failed for node {node_id}: {error_msg}")
                
                # execute (pass context if provided; some node logic expects it)
                if context is not None:
                    result = await logic.execute(node, context=context, **input_values)
                else:
                    result = await logic.execute(node, **input_values)
            
            # Step 8: Cache result
            node.cache_result(result)
            
            # record history and print to console
            try:
                self._history.append((node_id, result))
                print(f"{node_id}: {result}")
            except Exception:
                pass
            
            # Step 9: Update output sockets
            for output_id, value in result.items():
                if output_id in node.outputs:
                    node.set_output_value(output_id, value)
            
            # Step 10: Mark as done (already done by cache_result)
            
            # Step 11: Return result
            return result
            
        finally:
            # Remove from execution stack
            self._execution_stack.discard(node_id)
    
    async def execute_multiple(self, node_ids: list[str], clear_cache: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Execute multiple nodes in parallel.
        
        Args:
            node_ids: List of node IDs to execute
            clear_cache: If True, clear cache before execution
        
        Returns:
            Dict mapping node_id to its result dict
        """
        # clear caches explicitly or when any UI content present
        if clear_cache or any(getattr(n, 'ui_content', None) is not None for n in self.graph.nodes.values()):
            self.graph.clear_all_caches()
        
        # validate graph once
        is_valid, error_msg = self.graph.validate()
        if not is_valid:
            raise ExecutionError(f"Graph validation failed: {error_msg}")
        
        # execute in parallel
        results = await asyncio.gather(*[self.execute(nid, clear_cache=False) for nid in node_ids])
        
        return {node_ids[i]: results[i] for i in range(len(node_ids))}
    
    def get_execution_order(self, node_id: str) -> list[str]:
        """
        Get topological execution order for a node (DFS post-order).
        
        This shows which nodes would be executed and in what order.
        Useful for debugging and visualization.
        """
        if node_id not in self.graph.nodes:
            return []
        
        visited = set()
        order = []
        
        def dfs(nid: str):
            if nid in visited:
                return
            visited.add(nid)
            
            # visit dependencies first
            for dep in self.graph.get_dependencies(nid, kind=SocketKind.DATA):
                dfs(dep)
            
            order.append(nid)
        
        dfs(node_id)
        return order
    
    def clear_downstream_cache(self, node_id: str):
        """
        Clear cached results for a node and all its dependents.
        
        Useful when a node's inputs change and downstream needs recomputation.
        """
        if node_id not in self.graph.nodes:
            return
        
        # clear this node
        self.graph.nodes[node_id].clear_cache()
        
        # recursively clear dependents
        for dependent in self.graph.get_dependents(node_id):
            self.clear_downstream_cache(dependent)
