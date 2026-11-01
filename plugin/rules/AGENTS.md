# Bambu Studio & 3D Manufacturing Handoff Directives

- **Single Combined 3MF Delivery:** For multi-part/multi-body assemblies, deliver ONLY the single combined `.3mf` file (with components, colors, and extruder configs embedded). Never emit separate `.3mf` files per piece or list individual piece `.stl` files in chat.
- **Interactive Card Delivery:** Always accompany any delivered `.stl` or `.3mf` file with the GenUI Bambu Launcher card:
  1. Run: `python3 ~/.local/bin/bambu-card.py <model_path> <artifact_dir> [preview_img]`
     *(where `<artifact_dir>` is your conversation's active artifact directory path from `<user_information>`)*.
  2. Embed the card using the exact line printed by the script:
     `<agent-embed src="file:///<artifact_dir>/bambu_<name>.html"></agent-embed>`
  3. **CRITICAL `<agent-embed>` RULE:** The `src` attribute MUST be an absolute URI starting with `file:///` (e.g. `src="file:///Users/.../bambu_model.html"`). Never use relative paths like `src="bambu_model.html"` and never omit `file:///`. Standard `file:///` markdown links to the model may also be included.
- **True Aspect Ratio in 3D Previews:** When generating 3D previews with Matplotlib (`Axes3D`), Matplotlib defaults to a 1:1:1 cubic box which severely distorts proportions (stretching shallow parts by 10x along Z). You MUST ALWAYS call `ax.set_box_aspect((x_span, y_span, z_span))` matching the physical bounding box dimensions `(max_x - min_x, max_y - min_y, max_z - min_z)`.
