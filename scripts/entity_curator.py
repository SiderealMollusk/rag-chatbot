import gradio as gr
import yaml
import json
import os
import re
import argparse
import random
import time
from datetime import datetime
import shutil

# --- Global State ---
CANDIDATES = {}
CONTENT = []
ASIN = None
CURRENT_VERSION = 1
META_INFO = {}

# --- Data Management ---

def get_base_dir(asin):
    return os.path.join(os.getcwd(), "kindle-ai-export", "out", asin)

def load_file(asin, filename):
    """Loads a specific YAML file, migrating old formats if needed."""
    global CANDIDATES, CURRENT_VERSION, META_INFO, ASIN
    ASIN = asin
    filepath = os.path.join(get_base_dir(asin), filename)
    
    if not os.path.exists(filepath):
        return f"Error: {filename} not found."

    with open(filepath, 'r') as f:
        data = yaml.safe_load(f) or {}

    # Handle Meta Block
    if 'meta' in data:
        META_INFO = data['meta']
        CURRENT_VERSION = META_INFO.get('version', 1)
        raw_cats = data.get('entities', {}) # New structure
    else:
        # Legacy/Raw Candidate format migration
        META_INFO = {"source": asin, "version": 1}
        CURRENT_VERSION = 1
        raw_cats = data # Old structure was just root keys
        
    # Flatten candidates
    CANDIDATES = {}
    for cat, items in raw_cats.items():
        if cat == 'meta': continue 
        if items:
            for item in items:
                name = item['name']
                CANDIDATES[name] = {
                    "frequency": item['frequency'],
                    "category": cat,
                    "aliases": item.get('aliases', [])
                }
    
    return f"Loaded v{CURRENT_VERSION}: {len(CANDIDATES)} entities from {filename}"

def load_content(asin):
    global CONTENT
    content_path = os.path.join(get_base_dir(asin), "content.json")
    if os.path.exists(content_path):
        with open(content_path, 'r') as f:
            CONTENT = json.load(f)

def save_data(asin, increment_version=False):
    global CURRENT_VERSION
    
    if increment_version:
        CURRENT_VERSION += 1
    
    # Re-nest
    entities_block = {
        "CHARACTER": [], "FACTION": [], "LOCATION": [], "SHIP": [], 
        "UNCATEGORIZED": [], "TRASH": []
    }
    
    for name, data in CANDIDATES.items():
        cat = data.get('category', 'UNCATEGORIZED')
        if cat not in entities_block: entities_block[cat] = []
        entities_block[cat].append({
            "name": name,
            "frequency": data['frequency'],
            "aliases": data['aliases']
        })
    
    # Sort
    for cat in entities_block:
        entities_block[cat].sort(key=lambda x: x['frequency'], reverse=True)

    # Payload
    payload = {
        "meta": {
            "source": asin,
            "version": CURRENT_VERSION,
            "last_updated": datetime.now().isoformat()
        },
        "entities": entities_block
    }

    base_dir = get_base_dir(asin)
    
    # Main File: entities_manual.yaml
    main_path = os.path.join(base_dir, "entities_manual.yaml")
    
    # Versioned File: entities_vX.yaml
    version_path = os.path.join(base_dir, "backups", f"entities_v{CURRENT_VERSION}.yaml")
    os.makedirs(os.path.dirname(version_path), exist_ok=True)
    
    with open(main_path, 'w') as f:
        yaml.dump(payload, f, sort_keys=False)
        
    # Copy to versioned backup
    shutil.copy(main_path, version_path)
    
    return f"Saved v{CURRENT_VERSION}", list_versions(asin)

def list_versions(asin):
    """Returns list of (display_name, filename)"""
    base_dir = get_base_dir(asin)
    backup_dir = os.path.join(base_dir, "backups")
    
    choices = []
    
    # Check main file
    if os.path.exists(os.path.join(base_dir, "entities_manual.yaml")):
        choices.append(("Latest (entities_manual.yaml)", "entities_manual.yaml"))
    
    # Check candidates (Source)
    if os.path.exists(os.path.join(base_dir, "entities_candidates.yaml")):
         choices.append(("Original Source (entities_candidates.yaml)", "entities_candidates.yaml"))

    # Check backups
    if os.path.exists(backup_dir):
        files = [f for f in os.listdir(backup_dir) if f.startswith("entities_v")]
        # Sort by version number
        def get_v(name):
            try:
                 return int(re.search(r'v(\d+)', name).group(1))
            except: return 0
        
        files.sort(key=get_v, reverse=True)
        for f in files:
            v_num = get_v(f)
            choices.append((f"Version {v_num}", os.path.join("backups", f)))
            
    return choices


# --- Helpers ---

def get_checkbox_choices(cat_filter):
    # Sort by frequency
    items = []
    for name, info in CANDIDATES.items():
        if cat_filter == "ALL" or info['category'] == cat_filter:
            items.append((name, info['frequency']))
    
    items.sort(key=lambda x: x[1], reverse=True)
    
    # Return formatted strings for CheckboxGroup
    # Limit 100
    return [f"{n} ({f})" for n, f in items[:100]]

def apply_bulk_move(selected_strs, target_cat, current_filter):
    if not selected_strs: return "No selection", get_checkbox_choices(current_filter)
    
    count = 0
    for s in selected_strs:
        # Extract name: "Name (123)" -> "Name"
        # Be careful if name has parens. Regex from end.
        match = re.match(r'^(.*) \(\d+\)$', s)
        if match:
            name = match.group(1)
            if name in CANDIDATES:
                CANDIDATES[name]['category'] = target_cat
                count += 1
                
    return f"Moved {count} to {target_cat}", get_checkbox_choices(current_filter)

def get_context(name_input):
    # Clean input if copied from list "Name (123)"
    match = re.match(r'^(.*) \(\d+\)$', name_input)
    clean_name = match.group(1) if match else name_input
    
    print(f"[DEBUG] Searching content for: '{clean_name}'")
    
    excerpts = []
    # Use simple string search first to find the page, then extract sentence
    # This avoids regex complexity with weird characters
    
    chunks = list(CONTENT)
    random.shuffle(chunks)
    
    count = 0
    for chunk in chunks:
        text = chunk['text']
        if clean_name in text:
            # Find index
            start_idx = text.find(clean_name)
            # Grab a window around it
            window_start = max(0, start_idx - 100)
            window_end = min(len(text), start_idx + len(clean_name) + 100)
            snippet = text[window_start:window_end]
            
            # Highlight
            snippet = snippet.replace(clean_name, f"**{clean_name}**")
            snippet = snippet.replace("\n", " ")
            
            excerpts.append(f"> ...{snippet}...")
            count += 1
            if count >= 5: break
            
    if not excerpts:
        print(f"[DEBUG] No matches found for '{clean_name}' in {len(chunks)} pages.")
        return "No context found."
            
    return "\n\n".join(excerpts)

# --- UI Definition ---

with gr.Blocks(title="Curator v2", css="footer {display: none}") as demo:
    
    # Header
    with gr.Row():
        gr.Markdown("# Entity Curator v2")
        version_display = gr.Textbox(label="Status", value="Ready", interactive=False)

    # Loader
    with gr.Row(variant="panel"):
        with gr.Column(scale=3):
            file_selector = gr.Dropdown(label="Load Version", choices=[])
        with gr.Column(scale=1):
            btn_load = gr.Button("📂 Load")
    
    gr.Markdown("---")
    
    # Main Work Area
    with gr.Row():
        # Left: List & Filters
        with gr.Column(scale=1):
            filter_radio = gr.Radio(["UNCATEGORIZED", "ALL", "TRASH"], label="Filter", value="UNCATEGORIZED")
            selection_list = gr.CheckboxGroup(label="Candidates (Top 100)", interactive=True)
            
            with gr.Row():
                btn_trash = gr.Button("🗑️ Trash Selected", variant="stop")
            
            with gr.Row():
                btn_chr = gr.Button("👤 Char")
                btn_loc = gr.Button("🌍 Loc")
                btn_fac = gr.Button("🏴 Fact")
                btn_shp = gr.Button("🚀 Ship")

        # Right: Tools & Save
        with gr.Column(scale=1):
            # Save Controls
            with gr.Group():
                gr.Markdown("### Saving")
                with gr.Row():
                    btn_save_curr = gr.Button("💾 Save")
                    btn_save_new = gr.Button("✨ Save as New Version")
            
            gr.Markdown("---")
            
            # Context Tool
            gr.Markdown("### Context Check")
            ctx_input = gr.Textbox(label="Paste Name")
            ctx_output = gr.Markdown("...")


    # Auto-Context on Selection
    def on_select_change(selected_list, evt: gr.SelectData): 
        if evt.selected:
             # Strip "Name (123)" -> "Name"
             # Handling names with parens inside them? Unlikely for now.
             # The format is f"{name} ({freq})"
             # Let's split by " (" from the right
             value = evt.value
             try:
                 clean = value.rsplit(" (", 1)[0]
             except:
                 clean = value
             
             print(f"[DEBUG] Context Request for: '{clean}' (Original: '{value}')")
             return get_context(clean)
        return gr.Markdown(value="...")

    # Wiring
    selection_list.select(fn=on_select_change, inputs=[selection_list], outputs=ctx_output)
    
    # Load Logic
    def on_load(fname):
        msg = load_file(ASIN, fname)
        # Update file list in case they loaded a new file manually? No need.
        return msg, get_checkbox_choices("UNCATEGORIZED")
        
    btn_load.click(on_load, inputs=file_selector, outputs=[version_display, selection_list])
    
    # Filter Logic
    filter_radio.change(lambda f: get_checkbox_choices(f), inputs=filter_radio, outputs=selection_list)
    
    # Bulk Actions
    # Return: Status, List
    def wrap_move(s, t, f): return apply_bulk_move(s, t, f)
    
    btn_trash.click(wrap_move, [selection_list, gr.State("TRASH"), filter_radio], [version_display, selection_list])
    btn_chr.click(wrap_move, [selection_list, gr.State("CHARACTER"), filter_radio], [version_display, selection_list])
    btn_loc.click(wrap_move, [selection_list, gr.State("LOCATION"), filter_radio], [version_display, selection_list])
    btn_fac.click(wrap_move, [selection_list, gr.State("FACTION"), filter_radio], [version_display, selection_list])
    btn_shp.click(wrap_move, [selection_list, gr.State("SHIP"), filter_radio], [version_display, selection_list])
    
    # Manual Context (Keep this too)
    ctx_input.submit(get_context, ctx_input, ctx_output)
    
    # Save
    def on_save(inc):
        msg, choices = save_data(ASIN, increment_version=inc)
        # Update dropdown choices with new version
        return msg, gr.Dropdown(choices=choices) 
        
    btn_save_curr.click(lambda: on_save(False), outputs=[version_display, file_selector])
    btn_save_new.click(lambda: on_save(True), outputs=[version_display, file_selector])

    # Startup
    def startup_sequence():
        # 1. Load defaults
        files = list_versions("B000FBJAGO") # Hardcoded for now or use args if we can pass them
        msg = "Ready"
        choices = []
        
        if files:
            # Load the first file into backend
            msg = load_file("B000FBJAGO", files[0][1])
            # Get the list items for frontend
            choices = get_checkbox_choices("UNCATEGORIZED")
            
        return gr.Dropdown(choices=files, value=files[0][1] if files else None), msg, gr.CheckboxGroup(choices=choices)

    demo.load(startup_sequence, outputs=[file_selector, version_display, selection_list])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--asin", default="B000FBJAGO")
    args, unknown = parser.parse_known_args()
    ASIN = args.asin # Set global
    
    # We rely on demo.load to do the heavy lifting on page open
    demo.launch(server_name="0.0.0.0", server_port=7860)
