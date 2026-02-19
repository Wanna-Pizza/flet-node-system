"""
Simple test to verify async execution engine functionality
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from flet_nodes.runtime_graph import Graph, RuntimeNode, InputSocket, OutputSocket, Connection
from flet_nodes.node_logic import BaseNodeLogic, register_node_logic
from flet_nodes.executor import AsyncGraphExecutor


# Define test logic
class AddLogic(BaseNodeLogic):
    async def execute(self, node, **inputs):
        a = inputs.get('a', 0)
        b = inputs.get('b', 0)
        result = a + b
        print(f"AddLogic: {a} + {b} = {result}")
        return {'result': result}


class ValueLogic(BaseNodeLogic):
    async def execute(self, node, **inputs):
        value = inputs.get('value', 0)
        print(f"ValueLogic: returning {value}")
        return {'value': value}


async def test_execution():
    print("=== Testing Async Execution Engine ===\n")
    
    # Register logic
    register_node_logic('value', ValueLogic)
    register_node_logic('add', AddLogic)
    
    # Create graph
    graph = Graph()
    
    # Create value nodes
    node1 = RuntimeNode(
        id='value1',
        prototype='value',
        inputs={'value': InputSocket(id='value', display_name='Value', default=5)},
        outputs={'value': OutputSocket(id='value', display_name='Value')}
    )
    node1.logic = ValueLogic()
    
    node2 = RuntimeNode(
        id='value2',
        prototype='value',
        inputs={'value': InputSocket(id='value', display_name='Value', default=3)},
        outputs={'value': OutputSocket(id='value', display_name='Value')}
    )
    node2.logic = ValueLogic()
    
    # Create add node
    add_node = RuntimeNode(
        id='add1',
        prototype='add',
        inputs={
            'a': InputSocket(id='a', display_name='A', default=0),
            'b': InputSocket(id='b', display_name='B', default=0)
        },
        outputs={'result': OutputSocket(id='result', display_name='Result')}
    )
    add_node.logic = AddLogic()
    
    # Add nodes to graph
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(add_node)
    
    # Create connections
    graph.add_connection(Connection(
        from_node='value1',
        from_port='value',
        to_node='add1',
        to_port='a'
    ))
    
    graph.add_connection(Connection(
        from_node='value2',
        from_port='value',
        to_node='add1',
        to_port='b'
    ))
    
    print("Graph structure:")
    print(f"  Nodes: {list(graph.nodes.keys())}")
    print(f"  Connections: {len(graph.connections)}")
    for conn in graph.connections:
        print(f"    {conn.from_node}.{conn.from_port} → {conn.to_node}.{conn.to_port}")
    
    # Validate
    is_valid, error = graph.validate()
    print(f"\nGraph valid: {is_valid}")
    if not is_valid:
        print(f"  Error: {error}")
        return
    
    # Execute
    print("\n--- Executing add1 ---")
    executor = AsyncGraphExecutor(graph)
    result = await executor.execute('add1')
    
    print(f"\nFinal result: {result}")
    print(f"Expected: {{'result': 8}}")
    print(f"Success: {result == {'result': 8}}")
    
    # Test execution order
    print("\n--- Execution Order ---")
    order = executor.get_execution_order('add1')
    print(f"Order: {order}")
    
    # Test caching
    print("\n--- Testing Cache ---")
    print("Executing again (should use cache):")
    result2 = await executor.execute('add1')
    print(f"Cached result: {result2}")
    
    # Clear cache and re-execute
    print("\nClearing cache and re-executing:")
    result3 = await executor.execute('add1', clear_cache=True)
    print(f"Fresh result: {result3}")
    
    print("\n=== Test Complete ===")


if __name__ == '__main__':
    asyncio.run(test_execution())
