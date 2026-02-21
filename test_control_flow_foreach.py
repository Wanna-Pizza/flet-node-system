import asyncio
import sys
from pathlib import Path

# ensure src on path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from flet_nodes.runtime_graph import Graph, RuntimeNode, InputSocket, OutputSocket, Connection, SocketKind
from flet_nodes.node_logic import register_node_logic
from flet_nodes import (
    register_all_example_logic, register_all_control_flow_logic,
    ControlFlowExecutor, ExecutionContext
)

# register example logic
register_all_example_logic()
register_all_control_flow_logic()


async def test_foreach_flow():
    g = Graph()

    # start node
    start = RuntimeNode(
        id='start',
        prototype='flow.start',
        inputs={},
        outputs={'exec_out': OutputSocket(id='exec_out', display_name='Out', kind=SocketKind.EXEC)}
    )

    # list.create node (provides list)
    list_node = RuntimeNode(
        id='list1',
        prototype='list.create',
        inputs={'items': InputSocket(id='items', display_name='Items', kind=SocketKind.DATA, default=[1,2,3])},
        outputs={'list_out': OutputSocket(id='list_out', display_name='List', kind=SocketKind.DATA), 'length': OutputSocket(id='length', display_name='Length', kind=SocketKind.DATA)}
    )

    # foreach node
    foreach = RuntimeNode(
        id='foreach1',
        prototype='flow.foreach',
        inputs={'exec_in': InputSocket(id='exec_in', display_name='In', kind=SocketKind.EXEC), 'items': InputSocket(id='items', display_name='Items', kind=SocketKind.DATA)},
        outputs={'loop_body': OutputSocket(id='loop_body', display_name='Body', kind=SocketKind.EXEC), 'completed': OutputSocket(id='completed', display_name='Done', kind=SocketKind.EXEC)}
    )

    # loop item node
    loop_item = RuntimeNode(
        id='item1',
        prototype='foreach.item',
        inputs={},
        outputs={'item': OutputSocket(id='item', display_name='Item', kind=SocketKind.DATA)}
    )

    # debug print node
    debug_print = RuntimeNode(
        id='print1',
        prototype='debug.print',
        inputs={'exec_in': InputSocket(id='exec_in', display_name='In', kind=SocketKind.EXEC), 'value': InputSocket(id='value', display_name='Value', kind=SocketKind.DATA)},
        outputs={'out_value': OutputSocket(id='out_value', display_name='Out', kind=SocketKind.DATA), 'exec_out': OutputSocket(id='exec_out', display_name='ExecOut', kind=SocketKind.EXEC)}
    )

    # iterator node
    iterator = RuntimeNode(
        id='iter1',
        prototype='foreach.iterator',
        inputs={'exec_in': InputSocket(id='exec_in', display_name='In', kind=SocketKind.EXEC)},
        outputs={'loop_body': OutputSocket(id='loop_body', display_name='Loop', kind=SocketKind.EXEC), 'completed': OutputSocket(id='completed', display_name='Done', kind=SocketKind.EXEC)}
    )

    # attach logic
    for n in (list_node, foreach, loop_item, debug_print, iterator, start):
        pass

    # add nodes
    for node in (start, list_node, foreach, loop_item, debug_print, iterator):
        g.add_node(node)

    # add connections
    g.add_connection(Connection(from_node='start', from_port='exec_out', to_node='foreach1', to_port='exec_in', kind=SocketKind.EXEC))
    g.add_connection(Connection(from_node='list1', from_port='list_out', to_node='foreach1', to_port='items', kind=SocketKind.DATA))
    g.add_connection(Connection(from_node='foreach1', from_port='loop_body', to_node='print1', to_port='exec_in', kind=SocketKind.EXEC))
    g.add_connection(Connection(from_node='item1', from_port='item', to_node='print1', to_port='value', kind=SocketKind.DATA))
    g.add_connection(Connection(from_node='print1', from_port='exec_out', to_node='iter1', to_port='exec_in', kind=SocketKind.EXEC))
    g.add_connection(Connection(from_node='iter1', from_port='loop_body', to_node='print1', to_port='exec_in', kind=SocketKind.EXEC))

    # run flow
    executor = ControlFlowExecutor(g)
    ctx = ExecutionContext()
    result = await executor.run('start', ctx)

    # after run, print1.out_value should be last item (3)
    final_out = g.nodes['print1'].outputs['out_value'].value
    print('final_out_value =', final_out)
    assert final_out == 3

    # ensure debug.print executed 3 times (history contains print1 at least 3 times)
    history = executor.get_execution_history()
    count = sum(1 for h in history if h == 'print1')
    print('print1 executed times =', count)
    assert count == 3

    # ------------------------------------------------------------------
    # additional scenario: use list.builder to accumulate items
    builder = RuntimeNode(
        id='builder1',
        prototype='list.builder',
        inputs={
            'exec_in': InputSocket(id='exec_in', display_name='In', kind=SocketKind.EXEC),
            'item': InputSocket(id='item', display_name='Item', kind=SocketKind.DATA),
        },
        outputs={
            'list': OutputSocket(id='list', display_name='List', kind=SocketKind.DATA),
            'exec_out': OutputSocket(id='exec_out', display_name='Out', kind=SocketKind.EXEC),
        }
    )

    # add builder and wire it into the existing graph
    g.add_node(builder)
    # insert builder between print1 and iterator for simplicity
    g.remove_connection(Connection('print1','exec_out','iter1','exec_in',kind=SocketKind.EXEC))
    g.add_connection(Connection('print1','exec_out','builder1','exec_in',kind=SocketKind.EXEC))
    g.add_connection(Connection('builder1','exec_out','iter1','exec_in',kind=SocketKind.EXEC))
    g.add_connection(Connection('item1','item','builder1','item',kind=SocketKind.DATA))

    executor2 = ControlFlowExecutor(g)
    ctx2 = ExecutionContext()
    await executor2.run('start', ctx2)

    accumulated = g.nodes['builder1'].outputs['list'].value
    print('accumulated =', accumulated)
    assert accumulated == [1, 2, 3]

    # run a second time with new context and ensure list starts empty again
    executor3 = ControlFlowExecutor(g)
    ctx3 = ExecutionContext()
    await executor3.run('start', ctx3)
    accumulated2 = g.nodes['builder1'].outputs['list'].value
    print('accumulated after second run =', accumulated2)
    assert accumulated2 == [1, 2, 3]


if __name__ == '__main__':
    asyncio.run(test_foreach_flow())
    print('test_control_flow_foreach passed')
