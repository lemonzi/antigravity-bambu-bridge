#!/usr/bin/env python3
"""
antigravity-bambu-bridge: Generative UI card generator for 3D models.
Produces self-contained, responsive HTML cards with inlined base64 previews
and a 1-click Bambu Studio launch button (0 LLM tokens on click).
"""

import os
import sys
import zipfile
import base64
import subprocess

PORT = int(os.environ.get("BAMBU_BRIDGE_PORT", 48921))

def generate_bambu_card(model_path: str, artifact_dir: str, preview_img: str = None) -> str:
    """
    Generates an approved, compact, responsive GenUI Bambu Studio launcher card
    for a given .3mf or .stl file, writing the HTML artifact into artifact_dir.
    Returns the absolute path to the generated HTML file.
    """
    model_path = os.path.abspath(os.path.expanduser(model_path))
    file_name = os.path.basename(model_path)
    is_3mf = model_path.lower().endswith('.3mf')
    badge_text = "3MF" if is_3mf else "STL"

    file_size_bytes = os.path.getsize(model_path)
    if file_size_bytes > 1024 * 1024:
        file_size_str = f"{file_size_bytes / (1024 * 1024):.1f} MB"
    else:
        file_size_str = f"{file_size_bytes / 1024:.1f} KB"

    b64_img = ""

    # 1. Extract thumbnail for 3MF from native slice render
    if is_3mf:
        try:
            with zipfile.ZipFile(model_path, 'r') as z:
                for candidate in ['Metadata/plate_1.png', 'Metadata/plate_1_small.png', '3D/Metadata/plate_1.png']:
                    if candidate in z.namelist():
                        b64_img = base64.b64encode(z.read(candidate)).decode('utf-8')
                        break
        except Exception:
            pass

    # 2. Locate or convert thumbnail for STL
    if not b64_img:
        candidate_paths = []
        if preview_img and os.path.exists(preview_img):
            candidate_paths.append(preview_img)

        base_no_ext = os.path.splitext(model_path)[0]
        candidate_paths.extend([
            f"{base_no_ext}_preview.png",
            f"{base_no_ext}.png",
            os.path.join(os.path.dirname(model_path), "preview.png")
        ])

        found_img = None
        for cp in candidate_paths:
            if os.path.exists(cp):
                found_img = cp
                break

        if found_img:
            tmp_thumb = f"/tmp/thumb_{os.getpid()}.png"
            try:
                subprocess.run(['sips', '-Z', '400', found_img, '--out', tmp_thumb], check=True, capture_output=True)
                with open(tmp_thumb, 'rb') as f:
                    b64_img = base64.b64encode(f.read()).decode('utf-8')
                os.remove(tmp_thumb)
            except Exception:
                with open(found_img, 'rb') as f:
                    b64_img = base64.b64encode(f.read()).decode('utf-8')

    img_tag = f'<img src="data:image/png;base64,{b64_img}" alt="Preview" class="w-full h-auto max-h-56 object-contain p-1" />' if b64_img else '<div class="text-xs text-[var(--muted-foreground)] p-8 text-center">No preview available</div>'

    html_content = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
</head>
<body class="bg-transparent text-[var(--foreground)] antialiased p-2">
  <div class="bg-[var(--card)] text-[var(--foreground)] border border-[var(--border)] rounded-xl p-3 shadow-sm max-w-lg mx-auto">
    
    <!-- Top Row: Title + Size + Badge + Button -->
    <div class="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-[var(--border)] mb-2.5">
      <div class="flex items-center gap-2 min-w-0 flex-1">
        <div class="min-w-0">
          <h3 class="font-semibold text-xs text-[var(--foreground)] truncate" title="{file_name}">{file_name}</h3>
          <p class="text-[12px] text-[var(--muted-foreground)]">{file_size_str}</p>
        </div>
        <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex-shrink-0">{badge_text}</span>
      </div>

      <!-- Action Button (next to title, wraps if narrow or long title) -->
      <button id="openBtn" onclick="launchBambu()" class="flex-shrink-0 flex items-center justify-center space-x-1.5 bg-[#00ae42] hover:bg-[#009b3b] text-white font-medium py-1.5 px-3 rounded-lg transition-all duration-150 shadow-sm active:scale-[0.98] cursor-pointer">
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
        </svg>
        <span id="btnText" class="text-xs">Open in Bambu Studio</span>
      </button>
    </div>

    <!-- Preview Below (large, full-width) -->
    <div class="relative rounded-lg overflow-hidden border border-[var(--border)] bg-black/40 flex items-center justify-center max-h-56">
      {img_tag}
    </div>

    <!-- Error notice: hidden unless bridge is down -->
    <div id="bridgeError" class="hidden text-[11px] text-amber-400 pt-1.5 flex items-center justify-between">
      <span>Bridge unavailable</span>
      <a id="directLink" href="#" target="_blank" class="underline hover:text-amber-300">Open directly</a>
    </div>
  </div>

  <script>
    const TARGET_FILE = "{model_path}";
    const BRIDGE_URL = "http://127.0.0.1:{PORT}/open?file=" + encodeURIComponent(TARGET_FILE);
    let isLaunching = false;

    async function launchBambu() {{
      if (isLaunching) return;
      isLaunching = true;

      const btn = document.getElementById("openBtn");
      const btnText = document.getElementById("btnText");
      const err = document.getElementById("bridgeError");
      const link = document.getElementById("directLink");

      btnText.innerText = "Opening...";
      btn.style.opacity = "0.75";
      err.classList.add("hidden");

      try {{
        await fetch(BRIDGE_URL, {{ mode: 'no-cors' }});
        btnText.innerText = "Opened in Bambu Studio ✓";
        btn.classList.remove("bg-[#00ae42]");
        btn.classList.add("bg-emerald-600");
        setTimeout(() => {{
          btnText.innerText = "Open in Bambu Studio";
          btn.style.opacity = "1";
          btn.classList.add("bg-[#00ae42]");
          btn.classList.remove("bg-emerald-600");
          isLaunching = false;
        }}, 2000);
      }} catch (e) {{
        btnText.innerText = "Open in Bambu Studio";
        btn.style.opacity = "1";
        link.href = BRIDGE_URL;
        err.classList.remove("hidden");
        isLaunching = false;
      }}
    }}
  </script>
</body>
</html>'''

    clean_name = os.path.splitext(file_name)[0]
    out_file = os.path.join(artifact_dir, f"bambu_{clean_name}.html")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return out_file

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: bambu-card.py <model_path> <artifact_dir> [preview_img]")
        sys.exit(1)
    model = sys.argv[1]
    art_dir = sys.argv[2]
    prev = sys.argv[3] if len(sys.argv) > 3 else None
    card_path = generate_bambu_card(model, art_dir, prev)
    print(card_path)
