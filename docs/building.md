# Building and Running

## Quick Start

### Prerequisites
- Python ≥ 3.10
- `uv` package manager (or `pip`)

### Run the Demo App

```bash
cd examples/flet_nodes_example
uv run --active flet -r src/main.py
```

This launches a Flet app with an embedded node editor.

### Demo Walkthrough

1. **Register Types**: Click the button to register example node logic classes
2. **Create Nodes**: Click "Demo Nodes" to spawn example nodes (Add, Multiply, etc.)
3. **Connect Ports**: Drag from output ports to input ports to form a dataflow
4. **Execute**: Select a node and click "Execute Selected" to run the graph
5. **Observe**: Check console output or node results

## Development Workflow

### View Documentation Locally

```bash
mkdocs serve
```

Then open `http://localhost:8000` in your browser. Auto-reloads when you edit `.md` files.

### Run Unit Tests

```bash
python3 test_execution_engine.py
```

Or with pytest (if installed):

```bash
pytest src/flet_nodes/ -v
```

### Debug Tips

- **Execution not working?** Add `print()` statements in `executor.py` to trace execution flow
- **Custom node not appearing?** Ensure you called `register_node_logic()` before clicking "Register Types"
- **UI changes not showing?** Restart the app—Flet requires relaunch to pick up Python code changes
- **Enable logging**:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```

## Project Structure

```
flet_nodes/
├── runtime_graph.py      # Graph model and node storage
├── node_logic.py         # Base classes and registry
├── executor.py           # Async execution engine
├── flet_nodes.py         # UI ↔ runtime bridge
├── example_logic.py      # Demo node implementations
└── __init__.py           # Public API

examples/flet_nodes_example/
├── src/main.py           # Demo app entry point
└── flutter/              # Flutter (Dart) frontend code
```

## Build Artifacts

The repo includes example macOS builds in `build/` and `examples/flet_nodes_example/build/`. These are **not required** to run the engine—they're just reference outputs.
