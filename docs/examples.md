# Examples

## Quick Demo

### Run It

```bash
cd examples/flet_nodes_example
uv run --active flet -r src/main.py
```

### What You'll See

1. **Register Types** button → loads example node logic
2. **Demo Nodes** button → creates nodes on the canvas
3. A node editor with draggable nodes and connectable ports
4. **Execute Selected** button → runs the graph

### What the Example Includes

| Node Type | What It Does |
|-----------|-------------|
| Value A, Value B | Input nodes with text fields |
| Add | Adds two numbers |
| Multiply | Multiplies two numbers |
| Print | Outputs to console |
| If/Else | Conditional branching |

## Common Patterns

### 1. Input Node with UI Fallback

```python
class InputLogic(BaseNodeLogic):
    async def execute(self, node, **inputs):
        # Use UI textfield if no connected input
        if node.ui_content and hasattr(node.ui_content, 'value'):
            return {'value': node.ui_content.value}
        return {'value': inputs.get('default', '')}
```

### 2. Processing Pipeline

```
[Input A] ──→ [Add] ──→ [Multiply] ──→ [Print]
[Input B] ──→ [  +  ]                
```

Connect ports to wire data through the pipeline, then execute the final node.

### 3. Conditional Logic

```python
class IfElseLogic(BaseNodeLogic):
    async def execute(self, node, **inputs):
        condition = bool(inputs.get('condition', False))
        if condition:
            return {'result': inputs.get('true_val', None)}
        else:
            return {'result': inputs.get('false_val', None)}
```

### 4. Node with Side Effects

```python
class SaveToFileLogic(BaseNodeLogic):
    async def execute(self, node, **inputs):
        data = inputs.get('data', '')
        filepath = inputs.get('path', 'output.txt')
        
        with open(filepath, 'w') as f:
            f.write(str(data))
        
        return {'status': 'saved'}
```

## Tips for Building Graphs

- **Start simple**: Create a few nodes, connect them, execute to see flow
- **Debug with Print**: Insert `PrintLogic` nodes to inspect intermediate values
- **Check types**: Ensure output types match input expectations
- **Avoid cycles**: The engine detects them, but graphs won't execute
- **Test independently**: Unit-test logic classes before using them in graphs

## Example Files

- `examples/flet_nodes_example/src/main.py` — Demo UI app
- `src/flet_nodes/example_logic.py` — Logic implementations (Add, Multiply, Print, etc.)
- `test_execution_engine.py` — Unit test examples