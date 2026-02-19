# Development — Adding Custom Node Logic

## Step 1: Define Logic

Create a subclass of `BaseNodeLogic` with async `execute()` method:

```python
from flet_nodes import BaseNodeLogic

class DoubleLogic(BaseNodeLogic):
    """Multiplies input by 2."""
    
    async def execute(self, node, **inputs):
        value = inputs.get('value', 0)
        return {'result': value * 2}
```

**Key points:**
- `execute()` is async—use `await` for I/O operations
- `**inputs` contains values from connected ports (or defaults)
- Return a dict with output IDs as keys
- Raise exceptions to signal errors

## Step 2: Register

Register the logic class with a prototype ID:

```python
from flet_nodes import register_node_logic

register_node_logic('math.double', DoubleLogic)
```

Now users can create nodes with prototype `'math.double'` in the UI.

## Step 3: Test

### Unit Test

```python
import pytest
from flet_nodes import RuntimeNode, InputSocket
from your_module import DoubleLogic

@pytest.mark.asyncio
async def test_double_logic():
    logic = DoubleLogic()
    node = RuntimeNode(id='test', prototype='math.double')
    
    result = await logic.execute(node, value=5)
    assert result['result'] == 10
```

### Integration Test

Run the example app:
```bash
cd examples/flet_nodes_example
uv run --active flet -r src/main.py
```

Then:
1. Click "Register Types"
2. Click "Demo Nodes"
3. Connect and execute nodes to verify behavior

## Tips

- **Use `node.ui_content`** to read fallback values from UI controls
- **Cache expensive operations** if nodes might execute multiple times
- **Log execution**: Add `print()` or `logging` to debug dataflow
- **Type hints**: Add return type hints for IDE support

## Example: Node with UI Input

```python
class InputLogic(BaseNodeLogic):
    async def execute(self, node, **inputs):
        # Read from UI control if no input connected
        if node.ui_content and hasattr(node.ui_content, 'value'):
            value = node.ui_content.value
        else:
            value = inputs.get('fallback', '')
        
        return {'output': value}
```