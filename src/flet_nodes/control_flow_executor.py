"""
Control Flow Executor - Imperative execution engine

This module implements an alternative executor that follows EXEC connections
instead of pulling data dependencies. It drives "flow mode" graphs where each
node may decide what to execute next by returning a ``next_exec`` value.

The executor maintains an :class:`ExecutionContext` for variables, loop stacks
and shared state. It is re-entrant so that nested ForEach loops (and other
recursive constructs) can re‑enter without resetting the global history or
context.

Optimizations include:

* fast lookup of connections via ``graph._connection_map`` (O(1) per socket)
* special handling for ``foreach.item`` and ``foreach.index`` nodes that reads
  values directly from ``ExecutionContext`` rather than evaluating upstream
  data nodes
* debug tracing built with simple ``print()`` calls rather than wrapped in
  ``try/except`` blocks (failures would be silent anyway)

The implementation also detects runaway execution (infinite loops) and keeps
both a simple history list and a detailed step log for diagnostics.

Usage:

    executor = ControlFlowExecutor(graph)
    context = ExecutionContext()
    await executor.run(start_node_id, context)
"""
import asyncio
from typing import Any, Dict, Optional
from .runtime_graph import Graph, RuntimeNode, ExecutionState, SocketKind
from .node_logic import get_node_logic
from .execution_context import ExecutionContext, BreakException, ContinueException


class ControlFlowExecutionError(Exception):
    """Raised when control flow execution fails."""
    pass


class InfiniteExecutionError(ControlFlowExecutionError):
    """Raised when execution appears to be infinite."""
    pass


class ControlFlowExecutor:
    """
    Imperative execution engine for control flow graphs.
    
    Features:
    - Follows EXEC connections for execution order
    - Maintains ExecutionContext for variables and loop state
    - Supports nested loops with Break/Continue
    - Detects infinite execution (safety limit)
    - Integrates with existing node logic system
    - Re-entrant execution for ForEach loops
    - Optimised input handling (connection map, ForEach fast path)
    
    Usage:
        executor = ControlFlowExecutor(graph)
        context = ExecutionContext()
        await executor.run(start_node_id, context)
    """
    
    # Safety limit to prevent infinite loops
    MAX_EXECUTION_STEPS = 100000
    
    def __init__(self, graph: Graph):
        self.graph = graph
        self._execution_count = 0
        self._execution_history = []  # for debugging (node ids)
        self._detailed_history = []   # detailed per-step records (dicts)
        self._depth = 0  # re-entrant depth tracking
    
    async def run(
        self, 
        start_node_id: str, 
        context: Optional[ExecutionContext] = None,
        max_steps: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute the graph starting from a given node, following EXEC connections.
        
        Args:
            start_node_id: ID of the start node
            context: ExecutionContext to use (creates new if not provided)
            max_steps: Maximum execution steps (default: MAX_EXECUTION_STEPS)
        
        Returns:
            Final execution context's variables
        
        Raises:
            ControlFlowExecutionError: If execution fails
            InfiniteExecutionError: If max_steps exceeded
        """
        if context is None:
            context = ExecutionContext()
        
        if max_steps is None:
            max_steps = self.MAX_EXECUTION_STEPS
        
        if start_node_id not in self.graph.nodes:
            raise ControlFlowExecutionError(f"Start node {start_node_id} not found")
        
        # clear caches if any UI nodes exist (values may have changed since last run)
        if any(getattr(n, 'ui_content', None) is not None for n in self.graph.nodes.values()):
            self.graph.clear_all_caches()
        
        # validate graph
        is_valid, error_msg = self.graph.validate()
        if not is_valid:
            raise ControlFlowExecutionError(f"Graph validation failed: {error_msg}")
        
        # Only reset history for root-level execution (not re-entrant)
        if self._depth == 0:
            self._execution_count = 0
            self._execution_history = []
        
        self._depth += 1
        
        try:
            current_node_id = start_node_id
            
            while current_node_id is not None:
                # safety check
                self._execution_count += 1
                if self._execution_count > max_steps:
                    raise InfiniteExecutionError(
                        f"Execution exceeded {max_steps} steps. Possible infinite loop. "
                        f"Call stack: {' -> '.join(self._execution_history[-10:])}"
                    )
                
                        # track execution history (ids)
                self._execution_history.append(current_node_id)

                # get the node; dict.get avoids a second membership test
                node = self.graph.nodes.get(current_node_id)
                if node is None:
                    raise ControlFlowExecutionError(f"Node {current_node_id} not found during execution")

                # verbose console trace for debugging
                print(f"ControlFlowExecutor: -> executing {node.id} (prototype={node.prototype})")

                # execute the node
                try:
                    next_node_id = await self._execute_node(node, context)
                except (BreakException, ContinueException):
                    # these should be caught/handled within node execution
                    raise ControlFlowExecutionError(
                        f"Unhandled break/continue in node {current_node_id}"
                    )

                # move to next node
                current_node_id = next_node_id
            
            return context.variables
            
        except ControlFlowExecutionError:
            raise
        except Exception as e:
            raise ControlFlowExecutionError(f"Execution failed: {str(e)}") from e
        finally:
            self._depth -= 1
    
    async def _execute_node(
        self, 
        node: RuntimeNode, 
        context: ExecutionContext
    ) -> Optional[str]:
        """
        Execute a single node and return the next node to execute.
        
        Returns:
            Node ID to execute next, or None if execution should stop
        """
        node.set_state(ExecutionState.RUNNING)
        
        try:
            # get node logic
            logic = get_node_logic(node.prototype)
            
            if logic is None:
                # no logic - just follow the exec flow
                # look for exec_out socket
                return self._get_next_exec_node(node, "exec_out")
            
            # gather input values (only DATA sockets). we rely on the graph's
            # internal connection map for constant‑time lookup rather than
            # scanning self.graph.connections on every iteration.
            input_values: dict[str, Any] = {}
            socket_data = SocketKind.DATA
            conn_map = getattr(self.graph, '_connection_map', {}).get(node.id, {})

            for input_id, input_socket in node.inputs.items():
                # only DATA sockets participate in value gathering; EXEC
                # sockets control ordering and are ignored here
                if input_socket.kind != socket_data:
                    continue

                if input_socket.connected_from is None:
                    # unconnected input uses default value
                    input_values[input_id] = input_socket.default
                    continue

                # lookup connection from cached map; ``src_node_id`` may
                # be ``None`` for unconnected inputs (handled above)
                conn = conn_map.get(input_id)
                src_node_id = conn.from_node if conn is not None else None

                # fast path for foreach helper nodes; these are essentially
                # dynamic inputs whose value is stored in the execution context.
                if src_node_id is not None:
                    src_node = self.graph.nodes.get(src_node_id)
                    proto = getattr(src_node, 'prototype', None)
                    if proto == 'foreach.item':
                        val = context.get_variable('item')
                        # keep runtime node output in sync for inspection
                        try:
                            src_node.set_output_value('item', val)
                        except Exception:
                            pass
                        input_values[input_id] = val
                        continue
                    if proto == 'foreach.index':
                        idx = context.get_variable('loop_index')
                        try:
                            src_node.set_output_value('index', idx)
                        except Exception:
                            pass
                        input_values[input_id] = idx
                        continue

                # if upstream output hasn't been produced yet we may need to
                # evaluate the source node. this only occurs in rare cases such
                # as when the value depends on the context and hasn't been
                # computed by a previous execution (e.g. inside a loop body).
                if input_socket.connected_from.value is None and src_node_id is not None:
                    src_node = self.graph.nodes.get(src_node_id)
                    proto = getattr(src_node, 'prototype', None)
                    if proto not in ('foreach.item', 'foreach.index'):
                        try:
                            from .executor import AsyncGraphExecutor
                            age = AsyncGraphExecutor(self.graph)
                            # force fresh evaluation (context may change between iterations)
                            res_up = await age.execute(src_node_id, clear_cache=True, context=context)
                            # diagnostic printing may help track down unexpected
                            # re-evaluations
                            val = input_socket.connected_from.value
                            print(f"ControlFlowExecutor: computing upstream data node {src_node_id} for {node.id}.{input_id}")
                            print(f"ControlFlowExecutor: upstream node {src_node_id} returned: {res_up}")
                            print(f"ControlFlowExecutor: after compute, connected output value = {val}")
                        except Exception as e:
                            print(f"ControlFlowExecutor: failed while trying to compute upstream data: {e}")

                # finally read the value (may have been populated above)
                input_values[input_id] = input_socket.connected_from.value

            # debug: print input snapshot
            print(f"ControlFlowExecutor:   inputs for {node.id} = {input_values}")

            # validate inputs if logic provides validation
            is_valid, error_msg = await logic.validate_inputs(node, **input_values)
            if not is_valid:
                raise ControlFlowExecutionError(
                    f"Input validation failed for node {node.id}: {error_msg}"
                )

            # execute with context
            result = await logic.execute(node, context=context, **input_values)

            # update output sockets with values
            for output_id, value in result.items():
                if output_id in node.outputs:
                    node.set_output_value(output_id, value)

            node.set_state(ExecutionState.DONE)

            # record detailed step for diagnostics
            try:
                self._detailed_history.append({
                    'node_id': node.id,
                    'prototype': node.prototype,
                    'inputs': input_values,
                    'result': result,
                })
            except Exception:
                pass

            # debug: print result and next exec target
            next_exec_output = result.get("next_exec", "exec_out")
            next_target = self._get_next_exec_node(node, next_exec_output)
            print(f"ControlFlowExecutor:   result for {node.id} = {result} -> following '{next_exec_output}' to {next_target}")

            # return earlier-computed target
            return next_target
            
        except Exception as e:
            node.set_state(ExecutionState.ERROR)
            node.error = e
            raise
    
    def _get_next_exec_node(self, node: RuntimeNode, output_id: str) -> Optional[str]:
        """
        Get the next node to execute via an EXEC connection.
        
        Args:
            node: Current node
            output_id: Output socket ID to follow
        
        Returns:
            Next node ID, or None if no connection
        """
        return self.graph.get_exec_target(node.id, output_id)
    
    def get_execution_history(self) -> list[str]:
        """Get the history of executed nodes (IDs)."""
        return self._execution_history.copy()

    def get_detailed_history(self) -> list[dict]:
        """Get detailed per-step execution records.

        Each entry is a dict: { node_id, prototype, inputs, result }
        """
        return self._detailed_history.copy()

