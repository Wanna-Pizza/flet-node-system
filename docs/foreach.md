# ForEach Re-entrant Execution Architecture

> **Note:** the control flow executor now precomputes a connection map and
> provides a fast path for `foreach.item` and `foreach.index` nodes by reading
> values directly from the shared `ExecutionContext`. These optimisations
> eliminate redundant graph scans and keep loop helpers in sync automatically.

## Problem Statement

Initially, ForEach loops were not executing their loop body for each iteration. The execution flow stopped immediately after entering the ForEach node:

```
start → foreach [completed]
Total steps: 2
```

**Expected behavior:** Loop body should execute for each item in the list.

### Root Causes

1. **No iteration management** - ForEach returned `'next_exec': 'loop_body'` once and then executor moved to `completed`
2. **No execution history** - Without proper re-entrant execution, `executor.get_execution_history()` didn't capture nested iterations
3. **Naive iterator approach** - Separate `foreach.iterator` node existed but wasn't connected to the graph
4. **Non-reentrant executor** - `ControlFlowExecutor.run()` didn't support nested calls without resetting state

# ForEach — re‑entrant execution (updated)

## Overview

This document describes the current, working ForEach execution pattern implemented in the project.
It reflects the recent fixes and improvements so that Flow Mode reliably iterates a loop body for every item and preserves correct values for `foreach.item` / `foreach.index`.

Files to review:
- `src/flet_nodes/control_flow_executor.py` (re‑entrant executor + upstream DATA evaluation)
- `src/flet_nodes/executor.py` (async executor now accepts `context`)
- `src/flet_nodes/example_logic.py` (ForEach/Iterator/Item logic)
- `examples/flet_nodes_example/src/main.py` (demo + UI helpers)
- `test_control_flow_foreach.py` (automated test)

---

## Key ideas (what changed)

- Re‑entrant executor: `ControlFlowExecutor` tracks nesting (`_depth`) and **does not** reset execution history on iterator re‑entry — history now covers all iterations.
- Iterator node pattern remains: `foreach` initializes loop state; `foreach.iterator` advances the loop and returns `loop_body` to re‑enter the body.
- On‑demand DATA evaluation: if a Flow node needs a DATA input whose upstream output is missing or stale, the executor will run that upstream DATA node using `AsyncGraphExecutor(..., context=...)` with `clear_cache=True`.
- Fast path for `foreach.item` / `foreach.index`: these are populated directly from `ExecutionContext` when used inside the loop body (avoids stale cache or extra evaluation).
- `AsyncGraphExecutor.execute(..., context=...)` now passes the `ExecutionContext` into node logic that expects it.

---

## Graph pattern (must follow)

- Connect the ForEach body start (first node in the body) to both:
  - `foreach.loop_body` (first iteration), and
  - `iterator.loop_body` (re‑entry for subsequent iterations).

- Important: iterator.loop_body must point to the *body start node*, not to the `foreach` node.

Example connection pattern (conceptual):

```
foreach.loop_body   -> body_start.exec_in
iterator.loop_body  -> body_start.exec_in   # re-entry
iterator.completed  -> after_loop.exec_in
```

---

## Execution behaviour (detailed)

1. `flow.foreach` executes and:
   - pushes loop id on `ExecutionContext` stack,
   - stores items and index in `shared_state`,
   - sets `context.variables['item']` and `context.variables['loop_index']` for the first item,
   - returns `{'next_exec': 'loop_body'}`.

2. Executor follows `loop_body` to body start. For each node in the body:
   - If a DATA input is connected and its upstream output is missing, `ControlFlowExecutor` will attempt to compute that upstream node with `AsyncGraphExecutor(..., context)` (fresh evaluation).
   - If the upstream node is `foreach.item` or `foreach.index`, `ControlFlowExecutor` **directly reads** values from `ExecutionContext` and populates the runtime output (fast path).
   - Node logic is executed with the current `context` (when supported).

3. Body nodes return exec flows that eventually reach `foreach.iterator`.
   - `foreach.iterator` updates index/item in `ExecutionContext` and returns `loop_body` to re‑enter or `completed` to exit.

4. Execution history records every visit — call `executor.get_execution_history()` to inspect the full path across all iterations.

---

## Runtime traces (what you will see)

- When executor computes upstream DATA nodes:
  - `ControlFlowExecutor: computing upstream data node <id> for <node>.<input>`
- When `foreach.item` is populated from context:
  - `ControlFlowExecutor: populated <node_id>.item from context -> <value>`
- When debug nodes run in the body:
  - `[Debug] <value>` (from `debug.print`)

These traces are helpful when validating graph wiring and context propagation.

---

## Common pitfalls & tips

- `debug.print` (or any node you want executed in Flow Mode) must have `exec_in` connected to the flow. DATA connections alone (e.g. `length -> value`) do **not** trigger execution in Flow Mode.
- If you want a DATA‑only check outside Flow Mode, use **Execute (Data)** on that node — it runs the pull/eval executor.
- Always wire `iterator.loop_body` back to the **first node** of the body for re‑entry.

### Using `list.builder` inside the loop

`list.builder` is a stateful accumulator that keeps a running list of
items for the duration of a single flow execution. The state is kept in the
`ExecutionContext.shared_state` under a key derived from the node id, so
re-running the flow (or creating a fresh context) clears the list
automatically. You don’t need a feedback wire or any DATA cycle – just wire
the exec and item inputs.

1. Connect `list.builder.exec_in` to your loop body (e.g. `foreach.loop_body`).
2. Feed `foreach.item` → `list.builder.item`.
3. After the loop you can read the accumulated list from
   `list.builder.list` or attach it to another node; running the flow again
   will start from an empty list.

Example wiring:

```
start → **foreach.loop_body** → **list.builder.exec_in** → … → iterator
               │
               └──────────▶ list.builder.item  (connected from foreach.item)
```

Because the node stores the list internally, there’s no need for any
feedback links or extra connections; the control‑flow executor simply
passes the exec token along via `exec_out`.

---

## Example: ForEach over [1,2,3]

Path (simplified):

```
start → foreach → body_print → iterator → body_print → iterator → body_print → iterator → done
```