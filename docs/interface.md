# Interface — Defining Node Specs and UI

## Node Specs: Inputs and Outputs

Every node has a **prototype** that declares its interface:

```python
from flet_nodes import InputSpec, OutputSpec

inputs = [
    InputSpec(id='a', displayName='Number A', type='double', default=0.0),
    InputSpec(id='b', displayName='Number B', type='double', default=0.0)
]

outputs = [
    OutputSpec(id='result', displayName='Sum', type='double')
]
```

### InputSpec
- `id`: Internal identifier (used by logic code)
- `displayName`: Human-readable label in UI
- `type`: Optional hint—`'double'`, `'string'`, `'boolean'`, `'any'`
- `default`: Fallback value if port is not connected

### OutputSpec
- `id`: Internal identifier (must match keys returned by logic)
- `displayName`: User-facing label
- `type`: Output type hint

## Creating Nodes Programmatically

Use `NodesField` to add nodes to the editor from Python:

```python
from flet_nodes import NodesField, InputSpec, OutputSpec

nf = NodesField(expand=True)  # embedded in a Flet control
await nf.add_node(
    prototype='math.add',      # must be registered
    x=100, y=100,             # canvas position
    name='Add Numbers',        # display name in UI
    inputs=inputs,
    outputs=outputs
)
```

## UI Content as Fallback Input

Nodes can have optional UI controls that provide values when a port is not connected:

```python
from flet import TextField

ui_content = TextField(label='Value', value='42')
await nf.add_node(
    prototype='my.input',
    ui_content=ui_content,
    ...
)
```

When the node executes, logic code can read from this control if no connected input exists.

## Best Practices

1. **Keep UI concerns in Flet**: Rendering, user events, button clicks
2. **Put logic in Python classes**: All computation goes in `BaseNodeLogic.execute()`
3. **Use clear IDs**: `'math.add'`, `'string.concat'`—make it obvious what the node does
4. **Document types**: Help users understand what data flows through each port
5. **Provide sensible defaults**: So nodes work even if not fully connected