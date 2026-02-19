import flet as ft

from flet_nodes import (
    NodesField, NodeSelectedEvent, InputSpec, OutputSpec,
    register_all_example_logic, ExecutionError
)

class main:
    def __init__(self, page: ft.Page):
        self.page = page

        # Register example node logic
        register_all_example_logic()

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
            expand=True,
            content=ft.Column([
                ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                ft.Text("Select a node and click 'Execute Selected' to run it.", color=ft.Colors.GREY_500)
            ])
        )
        self.selected_node_id = None

        self.main_content = ft.Column([
            ft.Row([
                ft.ElevatedButton("Demo Nodes", on_click=self.create_demo_nodes),
                ft.PopupMenuButton("Add Node", items=[
                    ft.PopupMenuItem(content=ft.Text("Value A"), on_click=self._create_value_a),
                    ft.PopupMenuItem(content=ft.Text("Value B"), on_click=self._create_value_b),
                    ft.PopupMenuItem(content=ft.Text("Add"), on_click=self._create_add_node),
                    ft.PopupMenuItem(content=ft.Text("Multiply"), on_click=self._create_multiply_node),
                    ft.PopupMenuItem(content=ft.Text("Debug Print"), on_click=self._create_debug_print),
                    ft.PopupMenuItem(content=ft.Text("Bool Node"), on_click=self._create_bool_node),
                    ft.PopupMenuItem(content=ft.Text("Compare"), on_click=self._create_compare_node),
                    ft.PopupMenuItem(content=ft.Text("If Else"), on_click=self._create_ifelse_node),
                ]),
                ft.ElevatedButton("Clear Nodes", on_click=self.clear_nodes),
                ft.ElevatedButton("Execute Selected", on_click=self.execute_selected, bgcolor=ft.Colors.GREEN_700),
            ]),
            self.nodes_field,
        ], expand=True)

        self.page.add(ft.Row([
            self.main_content, 
            ft.Column([
                self.node_controls_preview,
                ft.Divider(),
                self.execution_output
            ], expand=True)
        ], expand=True))

    async def create_demo_nodes(self, e):
        # ensure types are registered
        # await self.register_types(e)

        # create a demo showing execution flow
        x = 100
        y = 100

        try:
            # Create demo nodes via helper functions
            await self._create_value_a(None)
            await self._create_value_b(None)
            await self._create_add_node(None)
            await self._create_debug_print(None)
            await self._create_bool_node(None)
            await self._create_ifelse_node(None)
            await self._create_multiply_node(None)

            print('Demo nodes created - connect them in the UI and execute!')
        except Exception as ex:
            print(f"ERROR creating demo nodes: {ex}")
            import traceback
            traceback.print_exc()

    # --- Individual node creation helpers ---
    async def _create_value_a(self, e):
        x = 100
        y = 100
        await self.nodes_field.add_node(
            prototype='float.value',
            x=x, y=y,
            name='Value A',
            content=ft.TextField(label="Value A", value="5"),
            inputs=[InputSpec(id='in_value', displayName='In', type='double', default=5.0)],
            outputs=[OutputSpec(id='out_value', displayName='Out', type='double')]
        )

    async def _create_value_b(self, e):
        x = 100
        y = 100
        await self.nodes_field.add_node(
            prototype='float.value',
            x=x, y=y,
            name='Value B',
            content=ft.TextField(label="Value B", value="3"),
            inputs=[InputSpec(id='in_value', displayName='In', type='double', default=3.0)],
            outputs=[OutputSpec(id='out_value', displayName='Out', type='double')]
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

    async def _create_debug_print(self, e):
        x = 100
        y = 100
        await self.nodes_field.add_node(
            prototype='debug.print',
            x=x, y=y,
            name='Debug Print',
            inputs=[InputSpec(id='value', displayName='A', type='string', default="Nope!")],
            outputs=[OutputSpec(id='out_value', displayName='Out', type='string')]
        )

    async def _create_bool_node(self, e):
        x = 100
        y = 100
        await self.nodes_field.add_node(
            prototype='bool.node',
            x=x, y=y,
            content=ft.Checkbox(label="Bool Node", value=True),
            name='Bool Node',
            inputs=[InputSpec(id='bool_in', displayName='A', type='bool', default=True)],
            outputs=[OutputSpec(id='bool_out', displayName='Out', type='bool')]
        )

    async def _create_ifelse_node(self, e):
        x = 100
        y = 100
        await self.nodes_field.add_node(
            prototype='ifelse.node',
            x=x, y=y,
            name='If Else',
            inputs=[
                InputSpec(id='condition', displayName='Condition', type='bool', default=False),
                InputSpec(id='true_value', displayName='True Value', type='any', default=None),
                InputSpec(id='false_value', displayName='False Value', type='any', default=None)
            ],
            outputs=[OutputSpec(id='value', displayName='Value', type='any')]
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

    async def clear_nodes(self, e):
        await self.nodes_field.clear_nodes()
    
    async def execute_selected(self, e):
        """Execute the currently selected node."""
        if self.selected_node_id is None:
            self.execution_output.content = ft.Column([
                ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                ft.Text("No node selected!", color=ft.Colors.RED_500)
            ])
            return
        
        try:
            # Validate graph first
            is_valid, error_msg = self.nodes_field.validate_graph()
            if not is_valid:
                self.execution_output.content = ft.Column([
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
            
            self.execution_output.content = ft.Column(result_controls)
            
        except ExecutionError as ex:
            self.execution_output.content = ft.Column([
                ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                ft.Text(f"Execution failed:", color=ft.Colors.RED_500),
                ft.Text(str(ex), color=ft.Colors.RED_300)
            ])
        except Exception as ex:
            self.execution_output.content = ft.Column([
                ft.Text("Execution Output", weight=ft.FontWeight.BOLD),
                ft.Text(f"Unexpected error:", color=ft.Colors.RED_500),
                ft.Text(str(ex), color=ft.Colors.RED_300)
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