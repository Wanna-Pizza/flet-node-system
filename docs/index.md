# Origins and Credits (English)

This project was inspired by `fl_nodes` (https://github.com/WilliamKarolDiCioccio/fl_nodes). Many UI patterns—port handling, link UX, and node interactions—draw from that work.

What we did differently

- UI layer: implemented with Flet + embedded Flutter components to render nodes and ports.
- Runtime: a separate Python async execution engine that is headless-testable and decoupled from the UI.
- Integration: events from the Flutter node editor are synchronized to the Python `Graph` so the runtime always reflects the visual state.

Acknowledgements

Thanks to the `fl_nodes` author for the reference implementation and ideas. This repository reuses concepts where appropriate but is an independent implementation tailored to Flet + Python.
