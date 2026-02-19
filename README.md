# Async Node Execution Engine

## Overview

This implementation adds a complete async execution engine to flet_nodes, enabling pull-based evaluation of node graphs with the following features:

- **Separate Runtime Layer**: UI rendering and execution logic are fully decoupled
- **Async Pull-Based Evaluation**: Nodes are executed recursively on-demand
- **Parallel Execution**: Dependencies are evaluated in parallel using asyncio.gather
- **Result Caching**: Executed nodes cache their results to avoid redundant computation
- **Graph Validation**: Cycle detection and input validation before execution
- **Connection Tracking**: Automatic synchronization of connections between Dart and Python
- **Modular Logic System**: Node behavior is defined by pluggable logic classes

## Architecture

### Layer Separation

```
┌─────────────────────────────────────┐
│      UI Layer (Flutter + Flet)      │
│  - Visual rendering                 │
│  - User interaction                 │
│  - Emits connection events          │
└──────────────┬──────────────────────┘
               │
               │ Events (link_created, link_removed)
               ▼
┌─────────────────────────────────────┐
│   Runtime Graph Layer (Python)      │
│  - Node and connection storage      │
│  - Independent of Flutter           │
│  - Maintains execution state        │
└──────────────┬──────────────────────┘
               │
               │ Graph access
               ▼
┌─────────────────────────────────────┐
│   Execution Layer (Async Executor)  │
│  - Pull-based evaluation            │
│  - Parallel async execution         │
│  - Result caching/memoization       │
└─────────────────────────────────────┘
```

## Core Components

### 1. Runtime Graph Model (`runtime_graph.py`)

Contains the execution-time data structures:

- **RuntimeNode**: Execution state, sockets, logic, and optional UI reference
- **InputSocket/OutputSocket**: Data flow connectors with type information
- **Connection**: Links between nodes (from_node.port → to_node.port)
- **Graph**: Container for nodes and connections with validation

### 2. Node Logic System (`node_logic.py`)

Defines how nodes behave:

- **BaseNodeLogic**: Abstract base class for node execution
- **NodeLogicRegistry**: Maps prototypes to logic implementations
- **register_node_logic()**: Convenience function for registration

### 3. Async Executor (`executor.py`)

Executes the graph:

- **AsyncGraphExecutor**: Main execution engine
- Pull-based recursive evaluation
- Parallel dependency execution
- Result caching and state tracking

### 4. NodesField Integration (`flet_nodes.py`)

Connects everything:

- Maintains runtime graph alongside UI nodes
- Handles link_created/link_removed events from Dart
- Provides `execute()` method for running nodes
- Auto-creates RuntimeNodes when UI nodes are added

## Usage

### 1. Register Node Logic

Define how your nodes execute:

```python
from flet_nodes import BaseNodeLogic, register_node_logic

class AddNodeLogic(BaseNodeLogic):
    async def execute(self, node, **inputs):
        a = inputs.get('a', 0)
        b = inputs.get('b', 0)
        return {'result': a + b}

# Register with prototype
register_node_logic('math.add', AddNodeLogic)
```

### 2. Create Nodes

```python
from flet_nodes import NodesField, InputSpec, OutputSpec

nodes_field = NodesField(expand=True)

await nodes_field.add_node(
    prototype='math.add',
    x=100, y=100,
    name='Add',
    inputs=[
        InputSpec(id='a', displayName='A', type='double', default=0.0),
        InputSpec(id='b', displayName='B', type='double', default=0.0)
    ],
    outputs=[
        OutputSpec(id='result', displayName='Result', type='double')
    ]
)
```

### 3. Execute Nodes

After connecting nodes in the UI:

```python
# Execute a specific node (automatically evaluates dependencies)
result = await nodes_field.execute('node_id')
print(result)  # {'result': 42}

# Validate graph before execution
is_valid, error = nodes_field.validate_graph()
if is_valid:
    result = await nodes_field.execute('node_id', clear_cache=True)
```

### 4. Access UI Content in Logic

Nodes can read from their UI controls:

```python
class TextNodeLogic(BaseNodeLogic):
    async def execute(self, node, **inputs):
        # Access UI control
        if isinstance(node.ui_content, ft.TextField):
            value = node.ui_content.value
            return {'output': value}
        
        # Fallback to input
        return {'output': inputs.get('input', '')}
```

## Example Logic Implementations

The package includes several example implementations in `example_logic.py`:

- **SimpleValueLogic**: Reads from TextField or passes through input
- **BoolNodeLogic**: Boolean value node with Checkbox support
- **IfElseLogic**: Conditional branching
- **MathAddLogic**: Add two numbers
- **MathMultiplyLogic**: Multiply two numbers
- **PrintLogic**: Debug output node

Register all examples:

```python
from flet_nodes import register_all_example_logic

register_all_example_logic()
```

## Execution Flow

1. **User triggers execution** on a target node
2. **Graph validation** checks for cycles and invalid connections
3. **Recursive pull**: Executor walks backwards from target
4. **Parallel evaluation**: Dependencies execute concurrently
5. **Input gathering**: Values collected from connected outputs
6. **Logic execution**: Node's `execute()` method runs
7. **Result caching**: Output stored to avoid recomputation
8. **Return**: Final result bubbles back to caller

## Connection Synchronization

Dart emits events when users create/remove connections:

```python
# Automatic - handled internally
NodesField.on_link_created  → updates Graph.connections
NodesField.on_link_removed  → removes from Graph.connections
```

The runtime graph stays synchronized with UI connections automatically.

## Advanced Features

### Custom Logic Validation

```python
class ValidatedLogic(BaseNodeLogic):
    async def validate_inputs(self, node, **inputs):
        if inputs.get('value', 0) < 0:
            return False, "Value must be positive"
        return True, None
    
    async def execute(self, node, **inputs):
        return {'output': inputs['value'] * 2}
```

### Lifecycle Callbacks

```python
class LifecycleLogic(BaseNodeLogic):
    def on_node_created(self, node):
        print(f"Node {node.id} created")
    
    def on_node_removed(self, node):
        print(f"Node {node.id} removed")
    
    async def execute(self, node, **inputs):
        return {'output': 42}
```

### Execution Order Analysis

```python
executor = AsyncGraphExecutor(nodes_field.get_graph())
order = executor.get_execution_order('target_node_id')
print(f"Will execute in order: {order}")
```

### Selective Cache Clearing

```python
# Clear cache for a node and all dependents
executor.clear_downstream_cache('node_id')

# Execute with fresh cache
result = await nodes_field.execute('node_id', clear_cache=True)
```

## Error Handling

```python
from flet_nodes import ExecutionError, CyclicDependencyError

try:
    result = await nodes_field.execute('node_id')
except CyclicDependencyError as e:
    print(f"Graph contains cycle: {e}")
except ExecutionError as e:
    print(f"Execution failed: {e}")
```

## Testing

Run the example:

```bash
cd examples/flet_nodes_example
uv run --active flet -r src/main.py
```

1. Click "Register Types" to register basic types
2. Click "Demo Nodes" to create example nodes
3. Connect nodes by dragging from output → input ports
4. Select a node
5. Click "Execute Selected" to run it

## Design Principles

✅ **UI stays presentation-only** - No execution logic in Flutter  
✅ **Runtime is framework-independent** - Can run headless  
✅ **Executor doesn't depend on Flutter** - Pure Python async  
✅ **Logic is modular** - Easy to add new node types  
✅ **Graph supports headless execution** - Can run without UI

## Files Created

- `src/flet_nodes/runtime_graph.py` - Core graph data structures
- `src/flet_nodes/node_logic.py` - Logic system and registry
- `src/flet_nodes/executor.py` - Async execution engine
- `src/flet_nodes/example_logic.py` - Example implementations
- Updated `src/flet_nodes/flet_nodes.py` - Integration
- Updated `src/flutter/flet_nodes/lib/src/NodesField.dart` - Connection events
- Updated `examples/flet_nodes_example/src/main.py` - Demo

## Future Enhancements

Possible extensions:

- [ ] Persist graph to JSON/file
- [ ] Undo/redo for graph modifications
- [ ] Execution visualization (animated flow)
- [ ] Breakpoints and step-through debugging
- [ ] Performance profiling per node
- [ ] Distributed execution across multiple processes
- [ ] Type checking at connection time
- [ ] Auto-save execution results
- [ ] Graph diff and merge

## License

Same as flet_nodes parent project.
