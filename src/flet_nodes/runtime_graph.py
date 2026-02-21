"""
Runtime Graph Model - Independent of UI Layer

This module provides the core runtime data structures for node-based execution,
completely separated from the UI/rendering layer.
"""

from typing import Any, Optional, Dict, List, Set
from dataclasses import dataclass, field
from enum import Enum


class ExecutionState(Enum):
    """Execution state of a node."""
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class SocketKind(Enum):
    """Kind of socket - determines what flows through the connection."""
    DATA = "data"  # carries values
    EXEC = "exec"  # controls execution order


@dataclass
class InputSocket:
    """Input socket on a runtime node."""
    id: str
    display_name: str
    kind: SocketKind = SocketKind.DATA  # socket kind (DATA or EXEC)
    type: Optional[str] = None
    default: Any = None
    connected_from: Optional['OutputSocket'] = None  # link to source output
    
    def get_value(self) -> Any:
        """Get current value (from connection or default)."""
        if self.connected_from is not None:
            return self.connected_from.value
        return self.default


@dataclass
class OutputSocket:
    """Output socket on a runtime node."""
    id: str
    display_name: str
    kind: SocketKind = SocketKind.DATA  # socket kind (DATA or EXEC)
    type: Optional[str] = None
    value: Any = None  # computed value after execution
    connected_to: List['InputSocket'] = field(default_factory=list)  # downstream inputs


@dataclass
class Connection:
    """Represents a connection between two nodes."""
    from_node: str  # node id
    from_port: str  # output socket id
    to_node: str    # node id
    to_port: str    # input socket id
    kind: SocketKind = SocketKind.DATA  # connection kind (DATA or EXEC)
    
    def __hash__(self):
        return hash((self.from_node, self.from_port, self.to_node, self.to_port, self.kind))
    
    def __eq__(self, other):
        if not isinstance(other, Connection):
            return False
        return (self.from_node == other.from_node and 
                self.from_port == other.from_port and
                self.to_node == other.to_node and 
                self.to_port == other.to_port and
                self.kind == other.kind)


class RuntimeNode:
    """
    Runtime representation of a node, independent of UI.
    
    Stores execution state, sockets, logic reference, and optional UI content.
    """
    
    def __init__(
        self,
        id: str,
        prototype: str,
        inputs: Optional[Dict[str, InputSocket]] = None,
        outputs: Optional[Dict[str, OutputSocket]] = None,
        ui_content: Any = None,  # ft.Control reference (optional)
    ):
        self.id = id
        self.prototype = prototype
        self.inputs = inputs or {}
        self.outputs = outputs or {}
        self.ui_content = ui_content
        self.logic = None  # assigned by logic registry
        self.state = ExecutionState.IDLE
        self.cached_result: Optional[Dict[str, Any]] = None
        self.error: Optional[Exception] = None
    
    def set_state(self, state: ExecutionState):
        """Update execution state."""
        self.state = state
    
    def cache_result(self, result: Dict[str, Any]):
        """Cache execution result."""
        self.cached_result = result
        self.state = ExecutionState.DONE
    
    def clear_cache(self):
        """Clear cached result and reset output socket values."""
        self.cached_result = None
        self.state = ExecutionState.IDLE
        self.error = None
        # clear any previously stored output socket values to avoid stale reads
        for out in self.outputs.values():
            try:
                out.value = None
            except Exception:
                pass
    
    def get_input_value(self, input_id: str) -> Any:
        """Get value from input socket."""
        if input_id in self.inputs:
            return self.inputs[input_id].get_value()
        return None
    
    def set_output_value(self, output_id: str, value: Any):
        """Set value on output socket."""
        if output_id in self.outputs:
            self.outputs[output_id].value = value
    
    def get_dependencies(self) -> List[str]:
        """Get list of upstream node IDs this node depends on."""
        deps = []
        for inp in self.inputs.values():
            if inp.connected_from is not None:
                # need to track which node owns this output
                # we'll handle this in Graph
                pass
        return deps


class Graph:
    """
    Runtime graph containing nodes and connections.
    
    This is the central data structure for execution, completely independent
    of the UI layer.
    """
    
    def __init__(self):
        self.nodes: Dict[str, RuntimeNode] = {}
        self.connections: List[Connection] = []
        self._connection_map: Dict[str, Dict[str, Connection]] = {}  # to_node -> {to_port: Connection}
    
    def add_node(self, node: RuntimeNode):
        """Add a runtime node to the graph."""
        self.nodes[node.id] = node
    
    def remove_node(self, node_id: str):
        """Remove a node and all its connections."""
        if node_id in self.nodes:
            # remove connections involving this node
            self.connections = [
                c for c in self.connections 
                if c.from_node != node_id and c.to_node != node_id
            ]
            del self.nodes[node_id]
            self._rebuild_connection_map()
    
    def add_connection(self, connection: Connection):
        """Add a connection between two nodes."""
        # validate nodes exist
        if connection.from_node not in self.nodes:
            raise ValueError(f"Source node {connection.from_node} not found")
        if connection.to_node not in self.nodes:
            raise ValueError(f"Target node {connection.to_node} not found")
        
        from_node = self.nodes[connection.from_node]
        to_node = self.nodes[connection.to_node]
        
        # validate ports exist
        if connection.from_port not in from_node.outputs:
            raise ValueError(f"Output port {connection.from_port} not found on node {connection.from_node}")
        if connection.to_port not in to_node.inputs:
            raise ValueError(f"Input port {connection.to_port} not found on node {connection.to_node}")
        
        # check for duplicate
        if connection in self.connections:
            return  # already exists
        
        self.connections.append(connection)
        
        # wire up socket references
        output_socket = from_node.outputs[connection.from_port]
        input_socket = to_node.inputs[connection.to_port]
        
        input_socket.connected_from = output_socket
        output_socket.connected_to.append(input_socket)
        
        self._rebuild_connection_map()
    
    def remove_connection(self, connection: Connection):
        """Remove a connection."""
        if connection in self.connections:
            # unwire sockets
            if connection.from_node in self.nodes and connection.to_node in self.nodes:
                from_node = self.nodes[connection.from_node]
                to_node = self.nodes[connection.to_node]
                
                if connection.from_port in from_node.outputs:
                    output_socket = from_node.outputs[connection.from_port]
                    if connection.to_port in to_node.inputs:
                        input_socket = to_node.inputs[connection.to_port]
                        input_socket.connected_from = None
                        if input_socket in output_socket.connected_to:
                            output_socket.connected_to.remove(input_socket)
            
            self.connections.remove(connection)
            self._rebuild_connection_map()
    
    def _rebuild_connection_map(self):
        """Rebuild internal connection lookup map."""
        self._connection_map.clear()
        for conn in self.connections:
            if conn.to_node not in self._connection_map:
                self._connection_map[conn.to_node] = {}
            self._connection_map[conn.to_node][conn.to_port] = conn
    
    def get_dependencies(self, node_id: str, kind: Optional["SocketKind"] = None) -> List[str]:
        """Get list of node IDs that feed into this node.

        If `kind` is provided, only connections of that SocketKind are
        considered (useful to distinguish DATA vs EXEC dependencies).
        """
        if node_id not in self._connection_map:
            return []
        
        deps = set()
        for conn in self._connection_map[node_id].values():
            if kind is None or conn.kind == kind:
                deps.add(conn.from_node)
        return list(deps)
    
    def get_dependents(self, node_id: str) -> List[str]:
        """Get list of node IDs that depend on this node."""
        dependents = set()
        for conn in self.connections:
            if conn.from_node == node_id:
                dependents.add(conn.to_node)
        return list(dependents)
    
    def get_exec_target(self, node_id: str, output_id: str) -> Optional[str]:
        """
        Find execution target for a given output socket on a node.
        
        Returns the node_id of the connected node via an EXEC connection,
        or None if no EXEC connection exists.
        """
        for conn in self.connections:
            if (conn.from_node == node_id and 
                conn.from_port == output_id and 
                conn.kind == SocketKind.EXEC):
                return conn.to_node
        return None
    
    def has_cycle(self, kind: Optional[SocketKind] = None) -> bool:
        """
        Check if graph contains cycles using DFS.
        
        Args:
            kind: If specified, only check cycles in connections of this kind.
                  If None, check all DATA connections (EXEC cycles are allowed).
        """
        if kind is None:
            kind = SocketKind.DATA  # default: check DATA cycles only
        
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            # only follow connections of the specified kind
            for conn in self.connections:
                if conn.from_node == node_id and conn.kind == kind:
                    dep = conn.to_node
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True
        return False
    
    def clear_all_caches(self):
        """Clear cached results from all nodes."""
        for node in self.nodes.values():
            node.clear_cache()
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate graph structure.
        
        Rules:
        - DATA connections must not create cycles
        - EXEC connections are allowed to have cycles
        - All connections must reference valid nodes/ports
        - Socket kinds must match (DATA to DATA, EXEC to EXEC)
        
        Returns:
            (is_valid, error_message)
        """
        # check for DATA cycles (EXEC cycles are allowed)
        if self.has_cycle(SocketKind.DATA):
            return False, "Graph contains DATA cycles (not allowed)"
        
        # check that all connections reference valid nodes/ports
        for conn in self.connections:
            if conn.from_node not in self.nodes:
                return False, f"Connection references missing node: {conn.from_node}"
            if conn.to_node not in self.nodes:
                return False, f"Connection references missing node: {conn.to_node}"
            
            from_node = self.nodes[conn.from_node]
            to_node = self.nodes[conn.to_node]
            
            if conn.from_port not in from_node.outputs:
                return False, f"Connection references missing output port: {conn.from_port}"
            if conn.to_port not in to_node.inputs:
                return False, f"Connection references missing input port: {conn.to_port}"
            
            # check socket kinds match
            from_socket = from_node.outputs[conn.from_port]
            to_socket = to_node.inputs[conn.to_port]
            
            if from_socket.kind != conn.kind:
                return False, f"Output socket {conn.from_port} kind {from_socket.kind} doesn't match connection kind {conn.kind}"
            if to_socket.kind != conn.kind:
                return False, f"Input socket {conn.to_port} kind {to_socket.kind} doesn't match connection kind {conn.kind}"
        
        return True, None
