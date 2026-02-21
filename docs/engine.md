# Async Node Execution Engine

## What You'll Learn Here

This document details the async execution engine powering Flet Node System. It covers:

- How the three-layer architecture works in practice
- Pull-based recursive evaluation and concurrency
- Result caching and optimization
- Graph validation and error detection
- Connection synchronization between UI (Dart) and Runtime (Python)

**TL;DR**: The executor runs your node graph asynchronously, evaluates dependencies in parallel, and caches results to avoid redundant work.

## Core Features

* ✅ **Decoupled Runtime**: UI and execution are independent (headless execution supported)
* ✅ **Async Pull-Based Evaluation**: Nodes execute recursively on-demand, not pushed
* ✅ **Parallel Execution**: Independent dependencies run concurrently with `asyncio.gather()`
* ✅ **Smart Caching**: Results stored per-session to avoid redundant computation
* ✅ **Graph Validation**: Automatic cycle detection and input checking
* ✅ **Auto-Sync**: Connections between Dart UI and Python runtime stay in sync
* ✅ **Modular Logic**: New node types added by registering Python classes
* ✅ **Control Flow Support**: A secondary executor follows EXEC edges to drive
  loops, conditionals and re‑entrant ForEach semantics

## Core Components

### 1. Runtime Graph Model (`runtime_graph.py`)

In-memory representation of your graph:

- **RuntimeNode**: Computation unit with id, prototype, input/output sockets, cached outputs
- **InputSocket/OutputSocket**: Typed data ports tracking connections to peer sockets
- **Connection**: Directed edge from `(node_id, output_id)` → `(node_id, input_id)`
- **RuntimeGraph**: Container holding all nodes and connections

**Key insight**: Graph is pure Python—knows nothing about Flutter or Flet.

### 2. Node Logic System (`node_logic.py`)

Pluggable behavior for each node type:

- **BaseNodeLogic**: Abstract base class with async `execute(node, **inputs)` method
- **NodeLogicRegistry**: Global registry mapping prototype IDs (e.g., `'math.add'`) to logic classes
- **register_node_logic(prototype_id, LogicClass)**: Register a new node type

When executor runs a node, it looks up the registered logic class and calls its `execute()` method.

### 3. Async Executor (`executor.py`)

The execution engine:

- **AsyncGraphExecutor**: Main class that runs your graph
  - `execute(target_node_id)`: Execute target node (recursively evaluates dependencies)
  - `validate_graph()`: Check for cycles and missing required inputs
  - `clear_cache()`: Force fresh re-execution
  - `get_execution_order(node_id)`: Return execution order for debugging

Execution is **pull-based**: executor walks backwards from target, pulling inputs from dependencies as needed.

### 4. Integration (`flet_nodes.py`)

Bridges UI and runtime:

- **NodesField** maintains both UI state and RuntimeGraph in sync
- Listens for `link_created`/`link_removed` events from Dart
- Auto-creates RuntimeNodes when UI nodes are added
- Provides `execute()` method for users to trigger execution
- Handles error reporting back to UI

## Step-by-Step: Register → Create → Execute

### Step 1: Register Node Logic

Define what your node does:

```python
from flet_nodes import BaseNodeLogic, register_node_logic

class AddNodeLogic(BaseNodeLogic):
    """Adds two numbers."""
    async def execute(self, node, **inputs):
        a = inputs.get('a', 0)
        b = inputs.get('b', 0)
        return {'result': a + b}

# Register with prototype ID
register_node_logic('math.add', AddNodeLogic)
```

**Key points**:

- Inherit from `BaseNodeLogic`
- Implement async `execute(node, **inputs)`
- Return dict with output socket IDs as keys
- Register with unique prototype ID (e.g., domain.operation)

### Step 2: Create Nodes in UI

```python
from flet_nodes import NodesField, InputSpec, OutputSpec

nodes_field = NodesField(expand=True)

await nodes_field.add_node(
    prototype='math.add',      # Must match registered ID
    x=100, y=100,              # Canvas position
    name='Add Numbers',        # Display name
    inputs=[
        InputSpec(id='a', displayName='Number A', type='double', default=0.0),
        InputSpec(id='b', displayName='Number B', type='double', default=0.0)
    ],
    outputs=[
        OutputSpec(id='result', displayName='Sum', type='double')
    ]
)
```

### Step 3: Execute from Python

After user connects nodes:

```python
# Execute a target node (auto-evaluates dependencies)
result = await nodes_field.execute('node_id')
print(result)  # {'result': 42}

# Check graph validity first
is_valid, error = nodes_field.validate_graph()
if not is_valid:
    print(f"Graph error: {error}")

# Force fresh execution (clear cache)
result = await nodes_field.execute('node_id', clear_cache=True)
```

## Accessing UI Content in Logic

Nodes can read from UI controls as input fallbacks:

```python
import flet as ft
from flet_nodes import BaseNodeLogic

class TextInputLogic(BaseNodeLogic):
    async def execute(self, node, **inputs):
        # Read from UI control if it exists
        if node.ui_content and isinstance(node.ui_content, ft.TextField):
            value = node.ui_content.value
        else:
            # Fallback to connected input
            value = inputs.get('input', '')
      
        return {'output': value.upper()}
```

## How Execution Works
### The Pull-Based Algorithm

When you call `executor.execute('target_node_id')`:

1. **Validate**: Check graph for cycles and required inputs
2. **Recursive walk**: Start at target node
3. **Check inputs**: For each input socket:
   - If connected: recursively execute upstream node (unless cached)
   - If not connected: use default value or UI content
4. **Execute node**: Call the logic class's `execute()` method
5. **Cache result**: Store output in node's cache
6. **Return**: Pass outputs to downstream nodes (or to caller)

#### Example Walkthrough

Graph: `A → B → C`

```
execute('C')
├─ validate_graph()
├─ C.inputs['x'] is connected to B.output
│  └─ execute('B')  # Recursive
│     ├─ B.inputs['y'] is connected to A.output
│     │  └─ execute('A')  # Recursive
│     │     ├─ A.inputs are not connected
│     │     ├─ Use defaults
│     │     ├─ Call A's logic → result = 10
│     │     └─ Cache in A.cached_outputs
│     ├─ Get A's result from cache
│     ├─ Call B's logic with A.result → result = 20
│     └─ Cache in B.cached_outputs
├─ Get B's result from cache
├─ Call C's logic with B.result → result = 30
├─ Cache in C.cached_outputs
└─ Return result to caller
```

### Concurrency with asyncio.gather()


### Control‑Flow and ForEach Loops

In addition to the normal pull‑based evaluation described above, the
engine also provides a **control‑flow executor** used by Flow Mode graphs. In
this mode each node may return a ``next_exec`` output that tells the executor
which node to run next; the graph is traversed by following **EXEC**
connections rather than data dependencies.

The `ControlFlowExecutor` (see :mod:`control_flow_executor`) features:

* step counter with a safety limit to detect infinite loops
* re‑entrant behaviour – nested loops (especially ``flow.foreach``) push and
  pop a loop stack without clearing the overall history or context
* fast‑path input handling for ``foreach.item`` and ``foreach.index`` nodes,
  which simply read the current value directly from the shared
  :class:`ExecutionContext` rather than evaluating an upstream node
* optional debug traces printed to stdout to aid development

A typical ForEach pattern looks like:

```
    flow.foreach ─  ─┐
                    ├── loop_body -> … -> foreach.iterator ─┐
                    │                                       │
                    └───────── completed <───────────────── ┘
```

The ``foreach.iterator`` node advances the loop index and either jumps back to
``loop_body`` (for the next item) or returns ``completed`` when the list is
finished. See ``example_logic.py`` and
``FOREACH_REENTRANT_EXECUTION.md`` for the full algorithm.

This hybrid execution model allows dataflow graphs to include imperative
constructs without giving up async evaluation or caching semantics.

When multiple nodes are independent, they execute in parallel:

```
execute('C')
├─ C needs X from B and Y from A₁ and A₂
│  ├─ execute('B') → parallel
│  │  └─ execute('A₁') ← parallel
│  │  └─ execute('A₂') ← parallel
│  └─ [asyncio.gather(all three)]
├─ Wait for all to complete
├─ Call C's logic with all inputs
└─ Return result
```

This means independent branches run **at the same time**, speeding up complex graphs.

### Caching: Avoid Redundant Work

Once a node executes, its outputs are cached **within one execution session**:

```python
# Same execute() call tree reuses cache
result = await executor.execute('C')
# If C calls B which calls A, and later B calls A again,
# A's cached result is reused—not executed twice

# Clear cache to force fresh execution
await executor.clear_cache()
result = await executor.execute('C')  # Now A runs again
```

This is powerful for expensive operations (API calls, file I/O, computations).

## Advanced Techniques

### Input Validation in Logic

```python
class ValidatedLogic(BaseNodeLogic):
    async def execute(self, node, **inputs):
        value = inputs.get('value', 0)
        if value < 0:
            raise ValueError("Value must be positive")
        return {'output': value * 2}
```

Raising exceptions in logic aborts execution and reports error to user.

### Execution Order Inspection

```python
executor = AsyncGraphExecutor(nodes_field.get_graph())
order = executor.get_execution_order('target_node_id')
print(order)  # ['node_a', 'node_b', 'node_c']
```

Useful for debugging complex graphs.

### Async Operations in Logic

```python
import asyncio

class HTTPLogic(BaseNodeLogic):
    async def execute(self, node, **inputs):
        url = inputs.get('url', '')
        # Can use await since execute() is async!
        response = await fetch_url_async(url)  
        return {'response': response.text}
```

Your node logic can do async I/O—perfect for APIs, database queries, etc.

### Selective Cache Clearing

```python
# Execute with fresh cache (ignore previous results)
result = await nodes_field.execute('node_id', clear_cache=True)

# Or manually clear
executor.clear_cache()
```

## Error Handling

The executor detects three main problems:

| Error                         | Cause                                    | Solution                               |
| ----------------------------- | ---------------------------------------- | -------------------------------------- |
| `CyclicDependencyError`     | Graph has a cycle (A→B→A)              | Remove a connection to break cycle     |
| `MissingRequiredInputError` | Input not connected and no default value | Connect the port or set a default      |
| `ExecutionError`            | Logic method raised an exception         | Check your logic code and input values |

Example error handling:

```python
from flet_nodes import ExecutionError, CyclicDependencyError

try:
    result = await nodes_field.execute('node_id')
except CyclicDependencyError as e:
    print(f"Graph has a cycle: {e}")
except ExecutionError as e:
    print(f"Node failed: {e}")
```

All errors include:

- Node ID where error occurred
- Human-readable message
- Full traceback for debugging

## Testing Node Logic

### Unit Test Example

```python
import pytest
from flet_nodes import RuntimeNode, BaseNodeLogic

class TestAddLogic:
    def setup_method(self):
        from flet_nodes import BaseNodeLogic
      
        class AddLogic(BaseNodeLogic):
            async def execute(self, node, **inputs):
                return {'result': inputs.get('a', 0) + inputs.get('b', 0)}
      
        self.logic = AddLogic()
  
    @pytest.mark.asyncio
    async def test_add_numbers(self):
        node = RuntimeNode(id='test', prototype='math.add')
        result = await self.logic.execute(node, a=5, b=3)
        assert result['result'] == 8
```

### Integration Test: Full Graph

```bash
# Run the demo app
cd examples/flet_nodes_example
uv run --active flet -r src/main.py
```

Then:

1. Click "Register Types" to load example logic
2. Click "Demo Nodes" to create example nodes
3. Connect nodes by dragging ports
4. Click "Execute Selected" to run the graph
5. Check console for output

## Design Philosophy

The engine is built around these principles:

✅ **Separation of Concerns**

- UI stays in Flutter (rendering, events)
- Logic lives in Python (computation)
- No execution code touches Dart

✅ **Headless Execution**

- Executor doesn't depend on Flutter/Flet
- Run graphs on servers, workers, or in tests
- Pure Python asyncio—portable and scalable

✅ **Extensibility**

- Add new node types by registering logic classes
- No UI changes needed
- Each node type is a simple Python class

✅ **Performance**

- Parallel execution for independent branches
- Aggressive caching to avoid redundant work
- Lazy evaluation (pull-based, not push-based)

✅ **Reliability**

- Graph validation before execution
- Clear error messages with full context
- Type hints and structured data

## Files in the Engine

Key files in the implementation:

- `src/flet_nodes/runtime_graph.py` → Graph data structures (nodes, connections)
- `src/flet_nodes/node_logic.py` → Logic base class and registry
- `src/flet_nodes/executor.py` → Execution algorithm (pull-based evaluation)
- `src/flet_nodes/flet_nodes.py` → UI ↔ Runtime integration
- `src/flet_nodes/example_logic.py` → Example node implementations (Add, Multiply, etc.)
- `src/flutter/flet_nodes/lib/src/NodesField.dart` → Dart UI component
- `examples/flet_nodes_example/src/main.py` → Demo app using the engine

For more on how to extend, see [Development](development.md).

## Future Enhancements

Possible extensions to the engine:

- [ ] **Persist graphs to JSON/YAML**: Save and load graphs from files
- [ ] **Type checking at connection time**: Warn when incompatible types connect
- [ ] **Execution visualization**: Animate data flow through nodes
- [ ] **Breakpoints and debugging**: Step through node execution
- [ ] **Performance profiling**: Measure execution time per node
- [ ] **Distributed execution**: Run subgraphs on different machines
- [ ] **Undo/redo**: Track and reverse graph modifications
- [ ] **Auto-save execution results**: Cache results to disk
- [ ] **Graph diff and merge**: Compare versions or merge branches

Contributions welcome! See [Development](development.md) for guidelines.
