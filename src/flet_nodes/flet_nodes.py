# enum not used
from typing import Any, Optional, Union
from dataclasses import dataclass, field

import flet as ft

# Import runtime graph and execution modules
from .runtime_graph import Graph, RuntimeNode, InputSocket, OutputSocket, Connection, ExecutionState
from .executor import AsyncGraphExecutor, ExecutionError, CyclicDependencyError
from .node_logic import BaseNodeLogic, register_node_logic, get_node_logic, get_registry

__all__ = [
    "NodesField", "Node", "NodeSelectedEvent", "LinkCreatedEvent", "LinkRemovedEvent",
    "InputSpec", "OutputSpec",
    # Runtime graph
    "Graph", "RuntimeNode", "InputSocket", "OutputSocket", "Connection", "ExecutionState",
    # Executor
    "AsyncGraphExecutor", "ExecutionError", "CyclicDependencyError",
    # Logic system
    "BaseNodeLogic", "register_node_logic", "get_node_logic", "get_registry",
]


class TypeRegistry:
    def __init__(self):
        self._registry = {}

    def register_type(self, type_id: str, py_type: type, serializer=None, deserializer=None):
        self._registry[type_id] = {
            "py_type": py_type,
            "serializer": serializer or (lambda v: v),
            "deserializer": deserializer or (lambda v: v),
        }

    def serialize(self, value, type_id: Optional[str] = None):
        if type_id and type_id in self._registry:
            return self._registry[type_id]["serializer"](value)
        return value

    def deserialize(self, payload, type_id: Optional[str] = None):
        if type_id and type_id in self._registry:
            return self._registry[type_id]["deserializer"](payload)
        return payload


# global registry instance with basic types
_type_registry = TypeRegistry()
_type_registry.register_type("int", int)
_type_registry.register_type("double", float)
_type_registry.register_type("str", str)
_type_registry.register_type("bool", bool)
_type_registry.register_type("dynamic", object)


@dataclass(kw_only=True)
class InputSpec:
    id: str
    displayName: Optional[str] = None
    type: Optional[str] = None
    default: Any = None
    meta: Optional[dict] = None


@dataclass(kw_only=True)
class OutputSpec:
    id: str
    displayName: Optional[str] = None
    type: Optional[str] = None
    default: Any = None
    meta: Optional[dict] = None

@dataclass(kw_only=True)
class NodeSelectedEvent(ft.Event[ft.EventControlType]):
    id: Optional[str] = field(default=None, metadata={"data_field": "id"})
    ids: Optional[list[str]] = field(default=None, metadata={"data_field": "ids"})

@dataclass(kw_only=True)
class LinkCreatedEvent(ft.Event[ft.EventControlType]):
    from_node: str = field(default="", metadata={"data_field": "from_node"})
    from_port: str = field(default="", metadata={"data_field": "from_port"})
    to_node: str = field(default="", metadata={"data_field": "to_node"})
    to_port: str = field(default="", metadata={"data_field": "to_port"})
    link_id: Optional[str] = field(default=None, metadata={"data_field": "link_id"})

@dataclass(kw_only=True)
class LinkRemovedEvent(ft.Event[ft.EventControlType]):
    from_node: str = field(default="", metadata={"data_field": "from_node"})
    from_port: str = field(default="", metadata={"data_field": "from_port"})
    to_node: str = field(default="", metadata={"data_field": "to_node"})
    to_port: str = field(default="", metadata={"data_field": "to_port"})
    link_id: Optional[str] = field(default=None, metadata={"data_field": "link_id"})

@ft.control("NodesField")
class NodesField(ft.LayoutControl):
    """
    NodesField Control description.

    Supports `nodes` slot (list of child `Node` controls). Also exposes
    `invoke_method` API for Python to add/remove/clear nodes:
      - add_node(prototype: str = 'simple.value', x: float = 0, y: float = 0)
      - remove_node(id: str)
      - clear_nodes()
      - execute(node_id: str)
    
    Maintains a runtime graph for execution, separate from UI.
    You can optionally handle link_created/link_removed events.
    """
    expand: Optional[Union[bool, int]] = True # Dont change
    nodes: Optional[ft.Control] = None
    on_node_selected: Optional[ft.EventHandler[NodeSelectedEvent["NodesField"]]] = None
    on_link_created: Optional[ft.EventHandler[LinkCreatedEvent["NodesField"]]] = None
    on_link_removed: Optional[ft.EventHandler[LinkRemovedEvent["NodesField"]]] = None
    # internal mapping: node_id -> {'name': name, 'content': ft.Control}
    _nodes: dict = field(default_factory=dict, init=False, repr=False)
    # runtime graph for execution
    _graph: Optional[Graph] = field(default=None, init=False, repr=False)
    
    def _get_graph(self) -> Graph:
        """Lazy initialization of runtime graph."""
        if self._graph is None:
            self._graph = Graph()
        return self._graph

    async def add_node(self, prototype: str = "simple.value", x: float = 0.0, y: float = 0.0, name: Optional[str] = None, content: Optional[ft.Control] = None, inputs: Optional[list] = None, outputs: Optional[list] = None):
        """Add a node to the field.

        inputs/outputs: optional list of port specs. Each spec may be either a string (port id)
        or a dict with keys: `id` (or `idName`), `displayName`, `type` (string type id), `default`, `meta`.
        """
        def _normalize_ports(specs):
            if not specs:
                return []
            normalized = []
            for s in specs:
                # accept dataclass instances directly
                if isinstance(s, (InputSpec, OutputSpec)):
                    entry = {"id": s.id}
                    if s.displayName is not None:
                        entry["displayName"] = s.displayName
                    if s.type is not None:
                        entry["type"] = s.type
                    if s.default is not None:
                        entry["default"] = _type_registry.serialize(s.default, s.type)
                    if s.meta is not None:
                        entry["meta"] = s.meta
                    normalized.append(entry)
                    continue

                # short form string
                if isinstance(s, str):
                    normalized.append({"id": s})
                    continue

                # dict form
                if isinstance(s, dict):
                    pid = s.get("id") or s.get("idName")
                    entry = {"id": pid}
                    if "displayName" in s:
                        entry["displayName"] = s["displayName"]
                    if "type" in s:
                        entry["type"] = s["type"]
                    if "default" in s:
                        entry["default"] = _type_registry.serialize(s["default"], s.get("type"))
                    if "meta" in s:
                        entry["meta"] = s["meta"]
                    normalized.append(entry)
                    continue

                # unknown form: ignore
                continue

            return normalized

        norm_inputs = _normalize_ports(inputs)
        norm_outputs = _normalize_ports(outputs)

        payload = {"prototype": prototype, "x": x, "y": y}
        if norm_inputs:
            payload["inputs"] = norm_inputs
        if norm_outputs:
            payload["outputs"] = norm_outputs

        res = await self._invoke_method("add_node", payload)
        try:
            node_id = res.get("id") if isinstance(res, dict) else None
        except Exception:
            node_id = None
        if node_id is not None:
            if not hasattr(self, '_nodes') or self._nodes is None:
                self._nodes = {}
            self._nodes[node_id] = {"name": name, "content": content}
            # save port metadata for Python-side inspection
            try:
                self._nodes[node_id]["ports"] = {"inputs": norm_inputs, "outputs": norm_outputs}
            except Exception:
                pass
            
            # Create RuntimeNode and add to graph
            try:
                # create input/output sockets
                input_sockets = {}
                for inp in norm_inputs:
                    input_sockets[inp["id"]] = InputSocket(
                        id=inp["id"],
                        display_name=inp.get("displayName", inp["id"]),
                        type=inp.get("type"),
                        default=inp.get("default")
                    )
                
                output_sockets = {}
                for outp in norm_outputs:
                    output_sockets[outp["id"]] = OutputSocket(
                        id=outp["id"],
                        display_name=outp.get("displayName", outp["id"]),
                        type=outp.get("type")
                    )
                
                # create runtime node
                runtime_node = RuntimeNode(
                    id=node_id,
                    prototype=prototype,
                    inputs=input_sockets,
                    outputs=output_sockets,
                    ui_content=content
                )
                
                # assign logic from registry
                logic = get_node_logic(prototype)
                if logic is not None:
                    runtime_node.logic = logic
                    logic.on_node_created(runtime_node)
                
                # add to graph
                self._get_graph().add_node(runtime_node)
                
            except Exception as e:
                print(f"Warning: Failed to create RuntimeNode for {node_id}: {e}")
        
        return res

    async def register_type(self, type_id: str, dart_type: Optional[str] = None):
        """Register a type id with the frontend (Dart) runtime.

        `type_id` is an arbitrary string used in port specs (e.g. 'double', 'int', 'myapp.Point').
        `dart_type` is an optional hint string for the Dart side (for example 'double', 'int', 'String').
        """
        try:
            # store in python-side registry as alias for convenience
            # best-effort mapping for common names
            alias_map = {
                'int': int,
                'double': float,
                'str': str,
                'bool': bool,
                'dynamic': object,
            }
            if type_id in alias_map:
                _type_registry.register_type(type_id, alias_map[type_id])

            payload = {'type_id': type_id}
            if dart_type is not None:
                payload['dart_type'] = dart_type

            res = await self._invoke_method('register_type', payload)
            return res
        except Exception:
            return False

    async def remove_node(self, id: str):
        res = await self._invoke_method("remove_node", {"id": id})
        try:
            if hasattr(self, '_nodes') and id in self._nodes:
                del self._nodes[id]
            # remove from graph
            graph = self._get_graph()
            if id in graph.nodes:
                # call on_node_removed callback if logic exists
                node = graph.nodes[id]
                if node.logic is not None:
                    node.logic.on_node_removed(node)
                graph.remove_node(id)
        except Exception:
            pass
        return res

    async def clear_nodes(self):
        res = await self._invoke_method("clear_nodes", {})
        try:
            if hasattr(self, '_nodes'):
                self._nodes.clear()
            # clear graph
            graph = self._get_graph()
            # call on_node_removed for all nodes
            for node in list(graph.nodes.values()):
                if node.logic is not None:
                    node.logic.on_node_removed(node)
            graph.nodes.clear()
            graph.connections.clear()
        except Exception:
            pass
        return res
    
    def _on_link_created(self, e: LinkCreatedEvent):
        """Internal handler for link creation events from Flutter."""
        try:
            connection = Connection(
                from_node=e.from_node,
                from_port=e.from_port,
                to_node=e.to_node,
                to_port=e.to_port
            )
            self._get_graph().add_connection(connection)
            print(f"Connection added: {e.from_node}.{e.from_port} -> {e.to_node}.{e.to_port}")
        except Exception as ex:
            print(f"Error adding connection: {ex}")
    
    def _on_link_removed(self, e: LinkRemovedEvent):
        """Internal handler for link removal events from Flutter."""
        try:
            connection = Connection(
                from_node=e.from_node,
                from_port=e.from_port,
                to_node=e.to_node,
                to_port=e.to_port
            )
            self._get_graph().remove_connection(connection)
            print(f"Connection removed: {e.from_node}.{e.from_port} -> {e.to_node}.{e.to_port}")
        except Exception as ex:
            print(f"Error removing connection: {ex}")
    
    async def execute(self, node_id: str, clear_cache: bool = False) -> dict:
        """
        Execute a node and return its outputs.
        
        Args:
            node_id: ID of the node to execute
            clear_cache: If True, clear all cached results before execution
        
        Returns:
            Dict mapping output socket ids to their values
            
        Raises:
            ExecutionError: If node execution fails
        """
        graph = self._get_graph()
        
        if node_id not in graph.nodes:
            raise ExecutionError(f"Node {node_id} not found in runtime graph")
        
        executor = AsyncGraphExecutor(graph)
        return await executor.execute(node_id, clear_cache=clear_cache)
    
    def get_graph(self) -> Graph:
        """Get the runtime graph for inspection or advanced usage."""
        return self._get_graph()
    
    def validate_graph(self) -> tuple[bool, Optional[str]]:
        """
        Validate the runtime graph.
        
        Returns:
            (is_valid, error_message)
        """
        return self._get_graph().validate()


    def get_node_content(self, id: str):
        try:
            return getattr(self, '_nodes', {}).get(id, {}).get('content')
        except Exception:
            return None


@ft.control("Node")
class Node(ft.LayoutControl):
    """
    Node Control description.
    """

