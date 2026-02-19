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
    
    Evaluates a condition and outputs to either true or false port.
    """
    
    async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
        """
        Execute if-else logic.
        
        Inputs:
            condition: boolean condition to evaluate
            true_value: value to output if condition is True
            false_value: value to output if condition is False
        
        Outputs:
            value: value from true_value if condition is True, else from false_value
        """
        condition = inputs.get('condition', False)
        true_value = inputs.get('true_value', None)
        false_value = inputs.get('false_value', None)
        

        if condition:
            return {
                "value": true_value
            }
        else:
            return {
                "value": false_value
            }


class MathAddLogic(BaseNodeLogic):
    """
    Logic for 'math.add' node prototype.
    
    Adds two numeric values.
    """
    
    async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
        """Add two numbers."""
        a = inputs.get("a", 0)
        b = inputs.get("b", 0)
        print(f"MathAddLogic: Received inputs a={a}, b={b}")
        
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
    """
    
    async def execute(self, node: RuntimeNode, **inputs) -> Dict[str, Any]:
        """Print value and pass through."""
        value = inputs.get("value", "")
        label = inputs.get("label", "Debug")
        
        print(f"[{label}] {value}")
        
        return {"out_value": value}


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
    # Compare node: compares two numeric inputs and returns boolean flags

    register_node_logic("compare.node", CompareLogic)
    
