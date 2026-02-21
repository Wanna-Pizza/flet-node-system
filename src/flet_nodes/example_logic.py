"""
Example Node Logic Implementations

This module provides example logic implementations for common node types.
These can be used as templates for creating custom node logic.
"""

from typing import Any, Dict
import flet as ft
from .node_logic import BaseNodeLogic
from .runtime_graph import RuntimeNode

#flow based
class StringValueLogic(BaseNodeLogic):
    """
    Logic for 'string.value' node prototype.
    
    This node reads a value from a TextField in its UI content and
    outputs it. If no UI content exists, it uses the input value or default.
    """
    
    async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
        """
        Execute string value node.
        
        Priority:
        1. Value from UI TextField (if exists)
        2. Value from input (if connected)
        3. Default value
        """
        # Try to read from UI content
        if node.ui_content is not None:
            try:
                # look for TextField in content
                if isinstance(node.ui_content, ft.TextField):
                    value = node.ui_content.value or ""
                    return {"out_value": value}
                elif isinstance(node.ui_content, ft.Column):
                    # search for TextField in column
                    for control in node.ui_content.controls:
                        if isinstance(control, ft.TextField):
                            value = control.value or ""
                            return {"out_value": value}
            except Exception as e:
                print(f"StringValueLogic: Error reading UI: {e}")
        
        # Fall back to input value
        in_value = inputs.get("in_value", inputs.get("value", ""))
        return {"out_value": in_value}

class FloatValueLogic(BaseNodeLogic):
    """
    Logic for 'float.value' node prototype.
    
    This node reads a value from a TextField in its UI content and
    outputs it. If no UI content exists, it uses the input value or default.
    """
    
    async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
        """
        Execute float value node.
        
        Priority:
        1. Value from UI TextField (if exists)
        2. Value from input (if connected)
        3. Default value
        """
        # Try to read from UI content
        if node.ui_content is not None:
            try:
                # look for TextField in content
                if isinstance(node.ui_content, ft.TextField):
                    value = node.ui_content.value or "0.0"
                    try:
                        value = float(value)
                    except ValueError:
                        value = 0.0
                    return {"out_value": value}
            except Exception as e:
                print(f"FloatValueLogic: Error reading UI: {e}")
        
        # Fall back to input value
        in_value = inputs.get("in_value", inputs.get("value", 0.0))
        try:
            in_value = float(in_value) if not isinstance(in_value, (int, float)) else in_value
        except (ValueError, TypeError):
            in_value = 0.0
        return {"out_value": in_value}



class BoolNodeLogic(BaseNodeLogic):
    """
    Logic for 'bool.node' prototype.
    
    Passes through a boolean value, optionally reading from UI.
    """
    
    async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
        """Execute boolean node."""
        # Try to read from UI checkbox
        if node.ui_content is not None:
            try:
                if isinstance(node.ui_content, ft.Checkbox):
                    value = node.ui_content.value or False
                    return {"bool_out": value}
                elif isinstance(node.ui_content, ft.Switch):
                    value = node.ui_content.value or False
                    return {"bool_out": value}
            except Exception as e:
                print(f"BoolNodeLogic: Error reading UI: {e}")
        
        # Fall back to input
        bool_in = inputs.get("bool_in", False)
        return {"bool_out": bool_in}


class IfElseLogic(BaseNodeLogic):
    """
    Logic for 'ifelse.node' prototype.

    - Accepts a DATA `condition` and returns the selected `value`.
    - Works with ExecutionContext passed in (ignored unless needed by custom logic).
    - Coerces common truthy/falsy representations (bool, int, str).
    """

    async def validate_inputs(self, node: RuntimeNode, **inputs) -> tuple[bool, str | None]:
        # Accept any input that can be coerced to bool; always valid here.
        return True, None

    async def execute(self, node: RuntimeNode, context=None, **inputs) -> Dict[str, Any]:
        """
        Execute if-else logic.

        Inputs:
            condition: boolean-like condition to evaluate
            true_value: value to output if condition is True
            false_value: value to output if condition is False

        Outputs:
            value: value from true_value if condition is True, else from false_value
        """
        def to_bool(v) -> bool:
            if isinstance(v, bool):
                return v
            if v is None:
                return False
            if isinstance(v, (int, float)):
                return v != 0
            if isinstance(v, str):
                return v.strip().lower() in ("1", "true", "yes", "y", "on")
            return bool(v)

        condition = inputs.get('condition', False)
        true_value = inputs.get('true_value', None)
        false_value = inputs.get('false_value', None)

        if to_bool(condition):
            return {"value": true_value}
        else:
            return {"value": false_value}


class ListCreateLogic(BaseNodeLogic):
    """
    Logic for 'list.create' node prototype.
    
    Creates and returns a list of values.
    Can read from UI TextField or use input value.
    """
    
    async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
        """Execute list creation logic."""
        # always read current value from UI if available
        items_list = []
        text = node.ui_content.value
        if text:
            items_list = [item.strip() for item in text.split(',')]
            converted = []
            for item in items_list:
                try:
                    converted.append(float(item) if '.' in item else int(item))
                except Exception:
                    converted.append(item)
            items_list = converted

        # # fall back to input if ui did not produce anything
        # if not items_list:
        #     items_list = inputs.get("items", [])
        #     if not isinstance(items_list, list):
        #         items_list = [items_list]
        
        return {
            "list_out": items_list,
            "length": len(items_list)
        }


class DictCreateLogic(BaseNodeLogic):
    """
    Logic for 'dict.create' node prototype.
    
    Creates and returns a dictionary.
    """
    
    async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
        """Execute dict creation logic."""
        dict_value = {}
        
        # Try to read from UI content
        if node.ui_content is not None:
            try:
                if isinstance(node.ui_content, ft.TextField):
                    import json
                    text = node.ui_content.value or "{}"
                    dict_value = json.loads(text)
            except Exception as e:
                print(f"DictCreateLogic: Error reading UI: {e}")
        
        # Fall back to input
        if not dict_value:
            dict_value = inputs.get("dict_in", {})
            if not isinstance(dict_value, dict):
                dict_value = {}
        
        return {"dict_out": dict_value}


class MathAddLogic(BaseNodeLogic):
    """
    Logic for 'math.add' node prototype.
    
    Adds two numeric values.
    """
    
    async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
        """Add two numbers."""
        a = inputs.get("a", 0)
        b = inputs.get("b", 0)

        
        # ensure numeric
        try:
            a = float(a) if not isinstance(a, (int, float)) else a
            b = float(b) if not isinstance(b, (int, float)) else b
        except (ValueError, TypeError) as e:
            print(f"MathAddLogic: Error converting inputs to float: {e}")
            a = 0
            b = 0
        
        result = a + b
        return {"result": result}

class CompareLogic(BaseNodeLogic):
        """
        Logic for 'compare.node' prototype.

        Outputs:
            is_equal: True if a == b, False otherwise
        """

        async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
            a = inputs.get('a', 0)
            b = inputs.get('b', 0)
            try:
                a = float(a) if not isinstance(a, (int, float)) else a
                b = float(b) if not isinstance(b, (int, float)) else b
            except (ValueError, TypeError):
                a = 0.0
                b = 0.0

            return {
                'is_equal': a == b,
            }


class MathMultiplyLogic(BaseNodeLogic):
    """
    Logic for 'math.multiply' node prototype.
    
    Multiplies two numeric values.
    """
    
    async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
        """Multiply two numbers."""
        a = inputs.get("a", 1)
        b = inputs.get("b", 1)
        
        try:
            a = float(a) if not isinstance(a, (int, float)) else a
            b = float(b) if not isinstance(b, (int, float)) else b
        except (ValueError, TypeError):
            a = 1
            b = 1
        
        result = a * b
        return {"result": result}


class PrintLogic(BaseNodeLogic):
    """
    Logic for 'debug.print' node prototype.
    
    Prints input value to console and passes it through.
    In Flow Mode, provides EXEC output for control flow.
    """
    
    async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
        """Print value and pass through."""
        value_con = node.ui_content.value
        value = inputs.get("value", "")
        value = f"{value_con}: {value}" if value_con else value
        label = inputs.get("label", "Debug")
        
        print(f"DEBUG: [{label}] {value} | DEBUG")
        
        # Return both DATA output and EXEC output for Flow Mode
        return {
            "out_value": value,
            "exec_out": None  # EXEC passthrough for control flow
        }


# ===== ForEach Support Nodes =====

class LoopItemLogic(BaseNodeLogic):
    """
    Logic for 'foreach.item' node prototype.
    
    Reads the current loop item from execution context during ForEach iteration.
    Can only be used inside a ForEach loop body - will return None otherwise.
    """
    
    async def execute(self, node: RuntimeNode, context=None, **inputs) -> Dict[str, Any]:
        """Get current loop item from context."""
        if context is None:
            print("LoopItemLogic: no context available, returning None")
            return {"item": None}
        
        try:
            item = context.get_variable('item')
            # debug log to help diagnose context propagation
            try:
                print(f"LoopItemLogic: context.variables = {context.variables}, returning item={item}")
            except Exception:
                pass
            return {"item": item}
        except Exception as e:
            print(f"LoopItemLogic: Error reading loop item: {e}")
            return {"item": None}


class LoopIndexLogic(BaseNodeLogic):
    """
    Logic for 'foreach.index' node prototype.
    
    Reads the current loop index (0-based) from execution context.
    Can only be used inside a ForEach loop body.
    """
    
    async def execute(self, node: RuntimeNode, context=None, **inputs) -> Dict[str, Any]:
        """Get current loop index from context."""
        if context is None:
            return {"index": 0}
        
        try:
            index = context.get_variable('loop_index')
            return {"index": index if index is not None else 0}
        except Exception as e:
            print(f"LoopIndexLogic: Error reading loop index: {e}")
            return {"index": 0}


class ListBuilderLogic(BaseNodeLogic):
    """
    Logic for 'list.builder' node prototype.

    Accumulates values during a single execution run. State is stored in the
    provided :class:`ExecutionContext` (``shared_state``) so that starting a
    new run or clearing the context automatically resets the list. This
    avoids unwanted caching across invocations and makes the behavior
    deterministic when the flow is re‑executed.

    **Inputs:**
    - exec_in (EXEC) – drives execution (e.g. from loop body)
    - item (DATA) – element to append

    **Outputs:**
    - list (DATA) – entire accumulated list so far
    - exec_out (EXEC) – forwarded execution token for flow chains

    Usage inside a ForEach simply requires wiring the EXEC flow and the
    `item` value; the node keeps track of previously appended elements
    automatically using the context.
    """
    
    async def execute(self, node: RuntimeNode, context=None, **inputs) -> Dict[str, Any]:
        """Append item stored in *context* and forward exec token."""
        if context is None:
            # if no context provided, fall back to transient local state
            item = inputs.get("item", None)
            return {"list": [item], "exec_out": None}

        item = inputs.get("item", None)
        key = f"{node.id}:accumulated"
        prev_list = context.get_shared_state(key) or []
        new_list = prev_list + [item]
        context.set_shared_state(key, new_list)
        return {"list": new_list, "exec_out": None}


class ItemTransformLogic(BaseNodeLogic):
    """
    Logic for 'foreach.transform' node prototype.
    
    Transforms the current loop item using a simple function.
    Applies: result = item * multiplier + offset
    """
    
    async def execute(self, node: RuntimeNode, context=None, **inputs) -> Dict[str, Any]:
        """Transform loop item."""
        if context is None:
            return {"result": None}
        
        try:
            item = context.get_variable('item')
            multiplier = inputs.get("multiplier", 1)
            offset = inputs.get("offset", 0)
            
            if isinstance(item, (int, float)):
                result = (item * multiplier) + offset
            elif isinstance(item, str):
                # For strings, just append offset as string
                result = item + str(offset)
            else:
                result = item
            
            return {"result": result}
        except Exception as e:
            print(f"ItemTransformLogic: Error transforming item: {e}")
            return {"result": None}


class ItemFilterLogic(BaseNodeLogic):
    """
    Logic for 'foreach.filter' node prototype.
    
    Checks if loop item matches a condition (greater than threshold).
    Returns boolean: True if item > threshold, False otherwise.
    """
    
    async def execute(self, node: RuntimeNode, context=None, **inputs) -> Dict[str, Any]:
        """Filter item."""
        if context is None:
            return {"passes": False}
        
        try:
            item = context.get_variable('item')
            threshold = inputs.get("threshold", 0)
            
            if isinstance(item, (int, float)) and isinstance(threshold, (int, float)):
                passes = item > threshold
            else:
                passes = False
            
            return {"passes": passes}
        except Exception as e:
            print(f"ItemFilterLogic: Error filtering item: {e}")
            return {"passes": False}


class LoopIteratorLogic(BaseNodeLogic):
    """
    Logic for 'foreach.iterator' node prototype.
    
    Advances to the next item in a ForEach loop.
    This node should be placed after loop_body output and decides whether
    to continue (loop_body) or exit (completed).
    
    Automatically increments loop index and sets next item in context.
    """
    
    async def execute(self, node: RuntimeNode, context=None, **inputs) -> Dict[str, Any]:
        """Advance to next iteration."""
        if context is None:
            return {"next_exec": "completed"}
        
        try:
            # Determine current ForEach loop node id from loop stack
            foreach_node_id = context.get_current_loop()

            if foreach_node_id is None:
                # Not in a ForEach loop
                return {"next_exec": "completed"}

            # Get loop data stored by ForEachNodeLogic
            items = context.get_shared_state(f"{foreach_node_id}:items")
            current_index = context.get_shared_state(f"{foreach_node_id}:index") or 0

            if not items:
                return {"next_exec": "completed"}

            # Advance to next index
            next_index = (current_index or 0) + 1

            if next_index < len(items):
                # More items to process
                context.set_shared_state(f"{foreach_node_id}:index", next_index)
                context.set_variable('item', items[next_index])
                context.set_variable('loop_index', next_index)

                return {"next_exec": "loop_body"}
            else:
                # No more items
                # pop the loop from the stack
                try:
                    print(f"LoopIteratorLogic: foreach={foreach_node_id} completed")
                except Exception:
                    pass
                context.pop_loop()
                return {"next_exec": "completed"}
        
        except Exception as e:
            print(f"LoopIteratorLogic: Error advancing iteration: {e}")
            return {"next_exec": "completed"}


# Convenience function to register all example logic
def register_all_example_logic():
    """Register all example logic implementations with the global registry."""
    from .node_logic import register_node_logic
    
    register_node_logic("string.value", StringValueLogic)
    register_node_logic("float.value", FloatValueLogic)
    register_node_logic("bool.node", BoolNodeLogic)
    register_node_logic("ifelse.node", IfElseLogic)
    register_node_logic("math.add", MathAddLogic)
    register_node_logic("math.multiply", MathMultiplyLogic)
    register_node_logic("debug.print", PrintLogic)
    register_node_logic("compare.node", CompareLogic)
    
    # Data type creation nodes
    register_node_logic("list.create", ListCreateLogic)
    register_node_logic("dict.create", DictCreateLogic)
    
    # ForEach support nodes
    register_node_logic("foreach.item", LoopItemLogic)
    register_node_logic("foreach.index", LoopIndexLogic)
    register_node_logic("list.builder", ListBuilderLogic)
    register_node_logic("foreach.transform", ItemTransformLogic)
    register_node_logic("foreach.filter", ItemFilterLogic)
    register_node_logic("foreach.iterator", LoopIteratorLogic)
    

def register_all_control_flow_logic():
    """Register all control flow node logic implementations with the global registry."""
    from .node_logic import register_node_logic
    from .control_flow_nodes import (
        StartNodeLogic,
        IfNodeLogic,
        ForEachNodeLogic,
        WhileNodeLogic,
        BreakNodeLogic,
        ContinueNodeLogic,
    )
    
    register_node_logic("flow.start", StartNodeLogic)
    # Sequence node is deprecated; its functionality is trivial and merged into ForEach
    register_node_logic("flow.if", IfNodeLogic)
    register_node_logic("flow.foreach", ForEachNodeLogic)
    register_node_logic("flow.while", WhileNodeLogic)
    register_node_logic("flow.break", BreakNodeLogic)
    register_node_logic("flow.continue", ContinueNodeLogic)
    
    # Register loop iterator (manages iteration state)
    register_node_logic("foreach.iterator", LoopIteratorLogic)
