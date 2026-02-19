# Building and Running (English)

Quick start — run the demo application

```bash
cd examples/flet_nodes_example
uv run --active flet -r src/main.py
```

What to do in the demo UI:

- Click `Register Types` to register example types used by nodes (if present).
- Click `Demo Nodes` to spawn example nodes (Value A, Value B, Add, Multiply, etc.).
- Connect outputs to inputs by dragging ports in the UI.
- Select a node and click `Execute Selected` to run the runtime on that node.

Serve the documentation locally

```bash
mkdocs serve
```

Testing

- Unit tests for the engine live near `test_execution_engine.py`. Run with:

```bash
python3 test_execution_engine.py
```

Notes and tips

- If you modify runtime code, restart the demo app to pick up changes.
- To debug execution, add logging in `executor.py` and `example_logic.py` to inspect input/outputs and execution order.

Build artifacts

The repo includes example build artifacts for macOS in `build/` and `examples/.../build/`. These are demo outputs and not required to run the engine.
