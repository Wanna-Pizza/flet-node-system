# Flet Node System

**A visual node editor + async Python runtime for dataflow-based applications.**

This repository provides a complete system for building visual node-based editors in Flet, paired with a headless Python runtime that executes node graphs asynchronously.

## Quick Overview

- **Python Runtime**: Headless async executor that runs node logic independently of the UI
- **Modular Nodes**: Add new node types by writing simple Python logic classes
- **Concurrent Execution**: Nodes run in parallel when dependencies allow, with automatic caching

## Use Cases

- Rapid prototyping of dataflow pipelines (ETL, data transformations)
- Event-driven UI automation
- Visual programming for end users
- Separation of concerns: UI rendering vs. business logic execution

## Getting Started

```bash
cd examples/flet_nodes_example
uv run --active flet -r src/main.py
```

For full documentation, see the [Docs](https://Wanna-Pizza.github.io/flet-node-system/)

## Credits

This project is based on and adapts patterns from [fl_nodes](https://github.com/WilliamKarolDiCioccio/fl_nodes), including the visual design, port UX, and node interaction model.
