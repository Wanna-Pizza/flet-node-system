# Introduction

FletNodes for Flet.

## Examples

```
import flet as ft

from flet_nodes import FletNodes


def main(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(

                ft.Container(height=150, width=300, alignment = ft.Alignment.CENTER, bgcolor=ft.Colors.PURPLE_200, content=FletNodes(
                    tooltip="My new FletNodes Control tooltip",
                    value = "My new FletNodes Flet Control", 
                ),),

    )


ft.run(main)
```

## Classes

[FletNodes](FletNodes.md)


