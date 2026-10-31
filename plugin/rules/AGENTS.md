# Bambu Studio & 3D Manufacturing Handoff Directives

- **Single Combined 3MF Delivery:** For multi-part or multi-body assemblies, deliver ONLY the single combined `.3mf` file (with components, colors, and extruder configs embedded). Never emit separate `.3mf` files per piece or list individual piece `.stl` files in chat.
- **Interactive Card Delivery:** Always accompany any delivered `.stl` or `.3mf` file with the GenUI Bambu Launcher card. Run `python3 ~/.local/bin/bambu-card.py <model_path> <artifact_dir> [preview_img]` and embed the resulting HTML with `<agent-embed>` (standard `file:///` links may also be included).
