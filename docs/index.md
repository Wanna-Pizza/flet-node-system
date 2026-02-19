# Flet Node System

## What is Flet Node System?

Flet Node System is a **visual node editor + async Python runtime** for building dataflow-based applications. It lets you:

1. **Design node graphs visually** using a Flutter-based editor in Flet
2. **Execute them asynchronously** with a pure Python runtime
3. **Extend with custom nodes** by writing simple Python classes

## Key Features

- **Separation of Concerns**: UI layer is completely independent from execution layer
- **Concurrent Execution**: Dependencies are evaluated in parallel; results are cached
- **Type Safety**: Optional type hints for inputs/outputs
- **Cycle Detection**: Automatic validation of node graphs
- **Easy Extensibility**: Add new node types without touching UI code

## Documentation Structure

- **[Interface](interface.md)** — how to define nodes and specs
- **[Architecture](architecture.md)** — deep dive into layers and execution flow
- **[Development](development.md)** — extending with custom node logic
- **[Examples](examples.md)** — runnable demos and patterns
- **[Building](building.md)** — setup and running
- **[Engine](engine.md)** — advanced execution details

## Start Here

New to Flet Node System? Check out [Examples](examples.md) for a quick demo.
