# Architecture — System Design

Flet Node System separates **visual editing** from **computation execution**, enabling headless testing and independent UI/runtime evolution.

## Layer Overview

- **UI Layer**: Renders nodes, handles interactions, emits events (Flutter + Flet)
- **Graph Layer**: Stores nodes and connections independently of UI (Pure Python)
- **Executor**: Validates and executes graph asynchronously (Async Python engine)
  - the primary executor is pull‑based and evaluates DATA dependencies
  - a secondary **control‑flow executor** walks EXEC edges and handles loops
    (including re‑entrant ForEach) and conditionals

## How Execution Works

**Example Graph**: A → B → C (each node's output connects to the next)

For flow‑mode graphs the “edges” may be execution tokens instead of
value wires; the control‑flow executor simply follows those EXEC links in
sequence, allowing nodes to dynamically choose the next target.

**Process**: `execute(node_C)`

1. Executor validates: no cycles, required inputs connected
2. Executor sees C needs B's output
3. Executor recursively executes B, which needs A's output
4. Executor runs A's logic class → result cached
5. Executor runs B's logic using A's cached result → result cached
6. Executor runs C's logic using B's cached result → result cached
7. Returns C's outputs

**Concurrency**: Independent branches run in parallel. If A1 and A2 both feed B, they execute concurrently.

**Caching**: Results cached within execution session. Query same node again → returns cache. Call `clear_cache()` to refresh.

## Error Handling

- `CyclicDependencyError`: Graph has cycle (A→B→A). Solution: remove connection.
- `MissingRequiredInputError`: Node missing required input with no default. Solution: connect port or add default.
- `ExecutionError`: Node logic raised exception. Solution: check logic code and inputs.

All errors include node ID and traceback for debugging.
