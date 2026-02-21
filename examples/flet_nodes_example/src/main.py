import flet as ft
import asyncio

from flet_nodes import (
    NodesField, NodeSelectedEvent, InputSpec, OutputSpec,
    register_all_example_logic, register_all_control_flow_logic, ExecutionError,
    ControlFlowExecutor, ExecutionContext, SocketKind, ControlFlowExecutionError, InfiniteExecutionError,
    Connection
)

class main:
    def __init__(self, page: ft.Page):
        self.page = page

        register_all_example_logic()
        register_all_control_flow_logic()

        self.nodes_field = NodesField(
            expand=True, 
            on_node_selected=self._on_node_event,
            on_link_created=self._on_link_created,
            on_link_removed=self._on_link_removed
        )
        self.node_controls_preview = ft.Container(
            expand=True, 
            content=ft.Text("Node controls will appear here")
        )
        self.execution_output = ft.Container(
            height=600,
            alignment=ft.Alignment.TOP_LEFT,
            content=ft.Column([
                ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                ft.Text("Select a node and click 'Execute Selected' to run it.", color=ft.Colors.GREY_500)
            ], scroll=ft.ScrollMode.AUTO)
        )

        def _set_execution_output_controls(controls: list[ft.Control]):
            try:
                col = self.execution_output.content
                if not isinstance(col, ft.Column):
                    col = ft.Column([], scroll=ft.ScrollMode.AUTO)
                    self.execution_output.content = col
                col.controls.clear()
                col.controls.extend(controls)
                try:
                    self.execution_output.update()
                except Exception:
                    pass
            except Exception:
                self.execution_output.content = ft.Column(controls, scroll=ft.ScrollMode.AUTO, height=300)

        self._set_execution_output_controls = _set_execution_output_controls
        self.selected_node_id = None
        self.execution_mode = "data"

        self.main_content = ft.Column([
            ft.Row([
                ft.ElevatedButton("Demo Nodes", on_click=self.create_demo_nodes),
                ft.PopupMenuButton("Data Types", items=[
                    ft.PopupMenuItem(content=ft.Text("Number"), on_click=self._create_number_node),
                    ft.PopupMenuItem(content=ft.Text("Boolean"), on_click=self._create_bool_node),
                    ft.PopupMenuItem(content=ft.Text("Create List"), on_click=self._create_list_node),
                    ft.PopupMenuItem(content=ft.Text("Create Dict"), on_click=self._create_dict_node),
                ]),
                ft.PopupMenuButton("Math", items=[
                    ft.PopupMenuItem(content=ft.Text("Add"), on_click=self._create_add_node),
                    ft.PopupMenuItem(content=ft.Text("Multiply"), on_click=self._create_multiply_node),
                    ft.PopupMenuItem(content=ft.Text("Compare"), on_click=self._create_compare_node),
                ]),
                ft.PopupMenuButton("Conditions", items=[
                    ft.PopupMenuItem(content=ft.Text("Debug Print"), on_click=self._create_debug_print),
                ]),
                ft.PopupMenuButton("Flow Control", items=[
                    ft.PopupMenuItem(content=ft.Text("Start"), on_click=self._create_start_node),
                    ft.PopupMenuItem(content=ft.Text("If"), on_click=self._create_if_node),
                    ft.PopupMenuItem(content=ft.Text("ForEach"), on_click=self._create_foreach_node),
                    ft.PopupMenuItem(content=ft.Text("While"), on_click=self._create_while_node),
                    ft.PopupMenuItem(content=ft.Text("Break"), on_click=self._create_break_node),
                    ft.PopupMenuItem(content=ft.Text("Continue"), on_click=self._create_continue_node),
                ]),
                ft.PopupMenuButton("Loop Helpers", items=[
                    ft.PopupMenuItem(content=ft.Text("Loop Item"), on_click=self._create_loop_item_node),
                    ft.PopupMenuItem(content=ft.Text("Loop Index"), on_click=self._create_loop_index_node),
                    ft.PopupMenuItem(content=ft.Text("Loop Iterator"), on_click=self._create_loop_iterator_node),
                    ft.PopupMenuItem(content=ft.Text("List Builder"), on_click=self._create_list_builder_node),
                    ft.PopupMenuItem(content=ft.Text("Item Transform"), on_click=self._create_item_transform_node),
                    ft.PopupMenuItem(content=ft.Text("Item Filter"), on_click=self._create_item_filter_node),
                ]),
                ft.ElevatedButton("Clear All", on_click=self.clear_nodes),
                ft.ElevatedButton("Execute (Data)", on_click=self.execute_selected, bgcolor=ft.Colors.GREEN_700),
                ft.ElevatedButton("Execute (Flow)", on_click=self.execute_flow_mode, bgcolor=ft.Colors.ORANGE_700),
            ]),
            self.nodes_field,
        ], expand=2)

        self.page.add(ft.Row([
            self.main_content, 
            ft.Column([
                self.node_controls_preview,
                ft.Divider(),
                self.execution_output
            ], expand=1)
        ], expand=True))

    async def create_demo_nodes(self, e):
        """Simplified demo graph for ForEach iteration, with automatic links."""
        try:
            await self.clear_nodes(None)
            start_id = await self._create_start_node(None, x=80, y=120)
            list_id = await self._create_list_node(None, x=80, y=260)
            foreach_id = await self._create_foreach_node(None, x=320, y=190)
            item_id = await self._create_loop_item_node(None, x=560, y=120)
            print_id = await self._create_debug_print(None, x=560, y=260)
            iterator_id = await self._create_loop_iterator_node(None, x=800, y=190)
            list_builder_id = await self._create_list_builder_node(None, x=1040, y=190)

            # make sure nothing failed silently
            if None in (start_id, list_id, foreach_id, item_id, print_id, iterator_id, list_builder_id):
                return

            # connect the flow/data wires
            await self._ensure_link(start_id, 'exec_out', foreach_id, 'exec_in')
            await self._ensure_link(list_id, 'list_out', foreach_id, 'items')
            # connect foreach body and iterator directly to print node
            await self._ensure_link(foreach_id, 'loop_body', print_id, 'exec_in')
            await self._ensure_link(iterator_id, 'loop_body', print_id, 'exec_in')
            await self._ensure_link(item_id, 'item', print_id, 'value')
            # connect print -> iterator normally, but also insert builder between them
            await self._ensure_link(print_id, 'exec_out', list_builder_id, 'exec_in')
            await self._ensure_link(list_builder_id, 'exec_out', iterator_id, 'exec_in')
            # wire builder data input
            await self._ensure_link(item_id, 'item', list_builder_id, 'item')

            # keep the remaining examples (if/else) untouched for now

            print('✓ Demo created — ForEach only.')
        except Exception as ex:
            print(f"ERROR creating demo nodes: {ex}")
            import traceback
            traceback.print_exc()
        except Exception as ex:
            print(f"ERROR creating demo nodes: {ex}")
            import traceback
            traceback.print_exc()
    # --- Individual node creation helpers ---

    async def _ensure_link(self, from_node: str, from_port: str, to_node: str, to_port: str):
        """Attempt to add a UI link; ignore errors silently."""
        try:
            await self.nodes_field.add_link(from_node=from_node, from_port=from_port, to_node=to_node, to_port=to_port)
            await asyncio.sleep(0.02)
        except Exception:
            pass
    async def _create_number_node(self, e):
        """Create a generic Number node."""
        await self.nodes_field.add_node(
            prototype='float.value',
            x=100, y=100,
            name='Number',
            content=ft.TextField(label="Value", value="0", width=150),
            inputs=[InputSpec(id='in_value', displayName='In', type='double', default=0.0)],
            outputs=[OutputSpec(id='out_value', displayName='Out', type='double')]
        )

    async def _create_list_node(self, e, x: float = 100, y: float = 100):
        """Create a List node that returns a list of integers."""
        res = await self.nodes_field.add_node(
            prototype='list.create',
            x=x, y=y,
            name='Create List',
            content=ft.TextField(label="Items (comma-separated)", value="1, 2, 3", width=200),
            inputs=[InputSpec(id='items', displayName='Items', type='list')],
            outputs=[
                OutputSpec(id='list_out', displayName='List[int]', type='list'),
                OutputSpec(id='length', displayName='Length', type='int')
            ]
        )
        try:
            return res.get('id') if isinstance(res, dict) else None
        except Exception:
            return None

    async def _create_dict_node(self, e):
        """Create a Dict node that returns a dictionary."""
        await self.nodes_field.add_node(
            prototype='dict.create',
            x=100, y=100,
            name='Create Dict',
            content=ft.TextField(label="Dict", value='{"key": "value"}', width=200),
            inputs=[InputSpec(id='dict_in', displayName='Dict', type='dict', default={})],
            outputs=[OutputSpec(id='dict_out', displayName='Dict', type='dict')]
        )

    async def _create_add_node(self, e):
        x = 100
        y = 100
        await self.nodes_field.add_node(
            prototype='math.add',
            x=x, y=y,
            name='Add',
            inputs=[InputSpec(id='a', displayName='A', type='double', default=0.0),
                    InputSpec(id='b', displayName='B', type='double', default=0.0)],
            outputs=[OutputSpec(id='result', displayName='Result', type='double')]
        )

    async def _create_debug_print(self, e, x: float = 100, y: float = 100):
        res = await self.nodes_field.add_node(
            prototype='debug.print',
            x=x, y=y,
            name='Debug Print',
            content=ft.TextField(label="Value to print", value=None, width=200),
            inputs=[
                InputSpec(id='exec_in', displayName='In', type='exec'),
                InputSpec(id='value', displayName='Value', type='any', default="Nope!")
            ],
            outputs=[
                OutputSpec(id='out_value', displayName='Out', type='any'),
                OutputSpec(id='exec_out', displayName='Out (exec)', type='exec')
            ]
        )
        try:
            return res.get('id') if isinstance(res, dict) else None
        except Exception:
            return None

    async def _create_bool_node(self, e, x: float = 100, y: float = 100):
        """Create a Boolean value node."""
        await self.nodes_field.add_node(
            prototype='bool.node',
            x=x, y=y,
            content=ft.Checkbox(label="Value", value=True),
            name='Boolean',
            inputs=[InputSpec(id='bool_in', displayName='In', type='bool', default=True)],
            outputs=[OutputSpec(id='bool_out', displayName='Out', type='bool')]
        )

    async def _create_multiply_node(self, e):
        x = 100
        y = 100
        await self.nodes_field.add_node(
            prototype='math.multiply',
            x=x, y=y,
            name='Multiply',
            inputs=[InputSpec(id='a', displayName='A', type='double', default=1.0),
                    InputSpec(id='b', displayName='B', type='double', default=2.0)],
            outputs=[OutputSpec(id='result', displayName='Result', type='double')]
        )

    async def _create_compare_node(self, e):
        x = 100
        y = 100
        await self.nodes_field.add_node(
            prototype='compare.node',
            x=x, y=y,
            name='Compare',
            inputs=[InputSpec(id='a', displayName='A', type='double', default=0.0),
                    InputSpec(id='b', displayName='B', type='double', default=0.0)],
            outputs=[OutputSpec(id='is_equal', displayName='Equal', type='bool')]
        )

    # --- Control Flow Nodes ---
    async def _create_start_node(self, e, x: float = 100, y: float = 100):
        res = await self.nodes_field.add_node(
            prototype='flow.start',
            x=x, y=y,
            name='Start',
            inputs=[],
            outputs=[OutputSpec(id='exec_out', displayName='Out', type='exec')]
        )
        try:
            return res.get('id') if isinstance(res, dict) else None
        except Exception:
            return None

    async def _create_if_node(self, e):
        await self.nodes_field.add_node(
            prototype='flow.if',
            x=100, y=100,
            name='If',
            inputs=[
                InputSpec(id='exec_in', displayName='In', type='exec'),
                InputSpec(id='condition', displayName='Condition', type='bool', default=True)
            ],
            outputs=[
                OutputSpec(id='exec_true', displayName='True', type='exec'),
                OutputSpec(id='exec_false', displayName='False', type='exec')
            ]
        )

    async def _create_foreach_node(self, e, x: float = 100, y: float = 100):
        res = await self.nodes_field.add_node(
            prototype='flow.foreach',
            x=x, y=y,
            name='ForEach',
            inputs=[
                InputSpec(id='exec_in', displayName='In', type='exec'),
                InputSpec(id='items', displayName='Items', type='list', default=[])
            ],
            outputs=[
                OutputSpec(id='loop_body', displayName='Body', type='exec'),
                OutputSpec(id='completed', displayName='Done', type='exec')
            ]
        )
        try:
            return res.get('id') if isinstance(res, dict) else None
        except Exception:
            return None

    async def _create_while_node(self, e):
        await self.nodes_field.add_node(
            prototype='flow.while',
            x=100, y=100,
            name='While',
            inputs=[
                InputSpec(id='exec_in', displayName='In', type='exec'),
                InputSpec(id='condition', displayName='Condition', type='bool', default=True)
            ],
            outputs=[
                OutputSpec(id='loop_body', displayName='Body', type='exec'),
                OutputSpec(id='completed', displayName='Done', type='exec')
            ]
        )

    async def _create_break_node(self, e):
        await self.nodes_field.add_node(
            prototype='flow.break',
            x=100, y=100,
            name='Break',
            inputs=[InputSpec(id='exec_in', displayName='In', type='exec')],
            outputs=[]
        )

    async def _create_continue_node(self, e):
        await self.nodes_field.add_node(
            prototype='flow.continue',
            x=100, y=100,
            name='Continue',
            inputs=[InputSpec(id='exec_in', displayName='In', type='exec')],
            outputs=[]
        )

    # --- ForEach Support Nodes ---
    async def _create_loop_item_node(self, e, x: float = 100, y: float = 100):
        """Create 'Loop Item' node - reads current loop item from context."""
        res = await self.nodes_field.add_node(
            prototype='foreach.item',
            x=x, y=y,
            name='Loop Item',
            inputs=[],
            outputs=[OutputSpec(id='item', displayName='Item', type='any')]
        )
        try:
            return res.get('id') if isinstance(res, dict) else None
        except Exception:
            return None

    async def _create_loop_index_node(self, e):
        """Create 'Loop Index' node - reads current loop iteration index."""
        await self.nodes_field.add_node(
            prototype='foreach.index',
            x=100, y=100,
            name='Loop Index',
            inputs=[],
            outputs=[OutputSpec(id='index', displayName='Index', type='int')]
        )

    async def _create_loop_iterator_node(self, e, x: float = 100, y: float = 100):
        """Create 'Loop Iterator' node - advances to next loop iteration."""
        res = await self.nodes_field.add_node(
            prototype='foreach.iterator',
            x=x, y=y,
            name='Loop Iterator',
            inputs=[InputSpec(id='exec_in', displayName='In', type='exec')],
            outputs=[
                OutputSpec(id='loop_body', displayName='Next', type='exec'),
                OutputSpec(id='completed', displayName='Done', type='exec')
            ]
        )
        try:
            return res.get('id') if isinstance(res, dict) else None
        except Exception:
            return None



    async def _create_list_builder_node(self, e, x: float = 100, y: float = 100):
        """Create 'List Builder' node - accumulates values into a list.

        This node participates in the flow executor, so it has EXEC ports
        that must be wired when using it inside a loop body.
        """
        res = await self.nodes_field.add_node(
            prototype='list.builder',
            x=x, y=y,
            name='List Builder',
            inputs=[
                InputSpec(id='exec_in', displayName='In', type='exec'),
                InputSpec(id='item', displayName='Item', type='any', default=None),
                InputSpec(id='list', displayName='List', type='list', default=[])
            ],
            outputs=[
                OutputSpec(id='list', displayName='List', type='list'),
                OutputSpec(id='exec_out', displayName='Out', type='exec')
            ]
        )
        try:
            return res.get('id') if isinstance(res, dict) else None
        except Exception:
            return None

    async def _create_item_transform_node(self, e, x: float = 100, y: float = 100):
        """Create 'Item Transform' node - transforms loop items."""
        await self.nodes_field.add_node(
            prototype='foreach.transform',
            x=x, y=y,
            name='Item Transform',
            inputs=[
                InputSpec(id='multiplier', displayName='Multiplier', type='double', default=1.0),
                InputSpec(id='offset', displayName='Offset', type='double', default=0.0)
            ],
            outputs=[OutputSpec(id='result', displayName='Result', type='any')]
        )

    async def _create_item_filter_node(self, e, x: float = 100, y: float = 100):
        """Create 'Item Filter' node - filters loop items by condition."""
        await self.nodes_field.add_node(
            prototype='foreach.filter',
            x=x, y=y,
            name='Item Filter',
            inputs=[
                InputSpec(id='threshold', displayName='Threshold', type='double', default=0.0)
            ],
            outputs=[OutputSpec(id='passes', displayName='Passes', type='bool')]
        )

    async def clear_nodes(self, e):
        await self.nodes_field.clear_nodes()
    
    async def execute_selected(self, e):
        """Execute the currently selected node."""
        if self.selected_node_id is None:
            self._set_execution_output_controls([
                ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                ft.Text("No node selected!", color=ft.Colors.RED_500)
            ])
            return
        
        try:
            # Validate graph first
            is_valid, error_msg = self.nodes_field.validate_graph()
            if not is_valid:
                self._set_execution_output_controls([
                    ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Graph validation failed:", color=ft.Colors.RED_500),
                    ft.Text(error_msg, color=ft.Colors.RED_300)
                ])
                return
            
            # Execute the node
            result = await self.nodes_field.execute(self.selected_node_id, clear_cache=True)
            
            # Display result
            result_controls = [
                ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                ft.Text(f"Node ID: {self.selected_node_id}", color=ft.Colors.BLUE_300),
                ft.Text("Result:", color=ft.Colors.GREEN_500),
            ]
            
            for key, value in result.items():
                result_controls.append(
                    ft.Text(f"  {key}: {value}", font_family="Courier")
                )
            
            self._set_execution_output_controls(result_controls)
            
        except ExecutionError as ex:
            self._set_execution_output_controls([
                ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                ft.Text(f"Execution failed:", color=ft.Colors.RED_500),
                ft.Text(str(ex), color=ft.Colors.RED_300)
            ])
        except Exception as ex:
            self._set_execution_output_controls([
                ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                ft.Text(f"Unexpected error:", color=ft.Colors.RED_500),
                ft.Text(str(ex), color=ft.Colors.RED_300)
            ])

    async def execute_flow_mode(self, e):
        """Execute the graph in flow mode (imperative execution)."""
        try:
            # Validate graph first
            is_valid, error_msg = self.nodes_field.validate_graph()
            if not is_valid:
                self._set_execution_output_controls([
                    ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Flow Mode - Graph validation failed:", color=ft.Colors.RED_500),
                    ft.Text(error_msg, color=ft.Colors.RED_300)
                ])
                return
            
            # Execute using ControlFlowExecutor
            graph = self.nodes_field._get_graph()
            
            # Find the Start node (flow.start prototype)
            start_node_id = None
            for node_id, node in graph.nodes.items():
                if node.prototype == 'flow.start':
                    start_node_id = node_id
                    break
            
            if start_node_id is None:
                self._set_execution_output_controls([
                    ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Flow Mode - No Start node found!", color=ft.Colors.RED_500),
                    ft.Text("Add a Start node and try again.", color=ft.Colors.RED_300)
                ])
                return
            
            executor = ControlFlowExecutor(graph)
            context = ExecutionContext()
            
            result = await executor.run(start_node_id, context)

            # Display result – only show debug.print outputs
            detailed = executor.get_detailed_history()
            result_controls = [
                ft.Text("Execution Output (Flow Mode)", weight=ft.FontWeight.BOLD),
                ft.Text(f"Mode: Imperative", color=ft.Colors.BLUE_300),
            ]

            # collect debug.print values in order
            printed = []
            for step in detailed:
                if step.get('prototype') == 'debug.print':
                    out = step.get('result', {})
                    # prefer the out_value field
                    printed.append(out.get('out_value'))

            if printed:
                result_controls.append(ft.Text("debug.print values:", color=ft.Colors.GREEN_500))
                for val in printed:
                    result_controls.append(ft.Text(f"  {val}", font_family="Courier"))
            else:
                result_controls.append(ft.Text("<no debug.print output>", color=ft.Colors.GRAY))

            self._set_execution_output_controls(result_controls)
            
        except InfiniteExecutionError as ex:
            self._set_execution_output_controls([
                ft.Text("Execution Output (Flow Mode)", weight=ft.FontWeight.BOLD),
                ft.Text(f"Infinite execution detected:", color=ft.Colors.RED_500),
                ft.Text(str(ex), color=ft.Colors.RED_300)
            ])
        except ControlFlowExecutionError as ex:
            self._set_execution_output_controls([
                ft.Text("Execution Output (Flow Mode)", weight=ft.FontWeight.BOLD),
                ft.Text(f"Flow execution failed:", color=ft.Colors.RED_500),
                ft.Text(str(ex), color=ft.Colors.RED_300)
            ])
        except Exception as ex:
            self._set_execution_output_controls([
                ft.Text("Execution Output (Flow Mode)", weight=ft.FontWeight.BOLD),
                ft.Text(f"Unexpected error:", color=ft.Colors.RED_500),
                ft.Text(str(ex), color=ft.Colors.RED_300),
                ft.Text(f"Type: {type(ex).__name__}", color=ft.Colors.ORANGE_300)
            ])

    def _on_node_event(self, e: NodeSelectedEvent):
        print('Node event:', e)
        if e.id:
            node_id = e.id
            self.selected_node_id = node_id
            content = self.nodes_field.get_node_content(node_id)
            if content is not None:
                self.node_controls_preview.content = content
            else:
                self.node_controls_preview.content = ft.Text(f"Selected: {node_id} (no content)")
        elif e.ids:
            self.selected_node_id = e.ids[0] if e.ids else None
            controls = []
            for node_id in e.ids:
                content = self.nodes_field.get_node_content(node_id)
                controls.append(ft.Column([ft.Text(node_id), content]))
            self.node_controls_preview.content = ft.Column(controls)

        else:
            self.selected_node_id = None
            self.node_controls_preview.content = ft.Text("Node controls will appear here")
    
    def _on_link_created(self, e):
        """Handle link creation - delegate to NodesField internal handler."""
        self.nodes_field._on_link_created(e)
    
    def _on_link_removed(self, e):
        """Handle link removal - delegate to NodesField internal handler."""
        self.nodes_field._on_link_removed(e)

ft.run(main)