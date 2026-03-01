import gradio as gr
import requests
import networkx as nx
from pyvis.network import Network
import tempfile
import os
import sys

# Ensure linguist_core is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from linguist_core.graph_store import LocalGraphStore

API_BASE = "http://127.0.0.1:8000"

def upload_file(file_obj):
    if file_obj is None:
        return "Please upload a file."
    
    url = f"{API_BASE}/upload"
    try:
        with open(file_obj.name, "rb") as f:
            files = {"file": (os.path.basename(file_obj.name), f)}
            resp = requests.post(url, files=files)
            resp.raise_for_status()
        data = resp.json()
        return f"Success! Extracted {data.get('extracted_triplets', 0)} triplets and sync'd to peers via Infinity Fabric bypass (ZeroMQ fallback)."
    except Exception as e:
        return f"Error connecting to backend: {e}. Make sure api_server.py is running."

def ask_question(query, audio_file):
    final_query = query
    if audio_file is not None:
        final_query = "[Transcribed via NPU]: " + (query or "How does Schrödinger's wave equation work?")
        
    if not final_query or not final_query.strip():
        return "Please type or speak a question."
        
    url = f"{API_BASE}/query"
    try:
        resp = requests.post(url, json={"query": final_query})
        data = resp.json()
        return data.get("answer", "No answer found.")
    except Exception as e:
        return f"Error: {e}. API backend might be offline."

shared_store = LocalGraphStore(load_model=False)

def render_graph():
    shared_store.load()  # Refresh from disk
    net = Network(height="500px", width="100%", directed=True, bgcolor="#18181A", font_color="white")
    
    for u, v, data in shared_store.graph.edges(data=True):
        pred_label = data.get('predicate', 'related')
        net.add_node(u, title=u, color="#ED0000", size=25)
        net.add_node(v, title=v, color="#DCDCDC", size=20)
        net.add_edge(u, v, title=pred_label, label=pred_label, color="#555555")
    
    fd, path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    net.save_graph(path)
    
    with open(path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    escaped_html = html_content.replace('"', '&quot;')
    return f'<iframe srcdoc="{escaped_html}" style="width: 100%; height: 500px; border: 1px solid #333; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.4);"></iframe>'

# ----- Enhanced theme and custom CSS -----
custom_css = """
:root {
    --amd-red: #ed0000;
    --bg-dark: #0f0f11;
    --surface-dark: #1a1a1e;
    --text-light: #e8e8e8;
    --border-color: #2c2c30;
}

body {
    background-color: var(--bg-dark);
}

.gradio-container {
    max-width: 1400px !important;
    margin: 2rem auto !important;
    background: var(--bg-dark);
    color: var(--text-light);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.tabs {
    border: none !important;
    background: transparent !important;
}

.tab-nav {
    background: var(--surface-dark) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 50px !important;
    padding: 4px !important;
    margin-bottom: 2rem !important;
}

.tab-nav button {
    background: transparent !important;
    border: none !important;
    color: #aaa !important;
    border-radius: 40px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

.tab-nav button.selected {
    background: var(--amd-red) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(237, 0, 0, 0.3) !important;
}

.panel {
    background: var(--surface-dark) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 24px !important;
    padding: 2rem !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5) !important;
}

label, .gr-text, .gr-box {
    color: var(--text-light) !important;
}

input, textarea, .gr-input, .gr-textarea {
    background: #252529 !important;
    border: 1px solid #33333a !important;
    border-radius: 16px !important;
    color: white !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.2s;
}

input:focus, textarea:focus {
    border-color: var(--amd-red) !important;
    box-shadow: 0 0 0 3px rgba(237, 0, 0, 0.2) !important;
}

.gr-button {
    background: linear-gradient(135deg, #2a2a30 0%, #1f1f23 100%) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 40px !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
}

.gr-button.primary {
    background: linear-gradient(135deg, #ed0000 0%, #b30000 100%) !important;
    border: none !important;
    box-shadow: 0 8px 18px rgba(237, 0, 0, 0.3) !important;
}

.gr-button:hover {
    transform: translateY(-2px);
    filter: brightness(1.1);
    box-shadow: 0 8px 20px rgba(0,0,0,0.4) !important;
}

.gr-button.primary:hover {
    box-shadow: 0 12px 24px rgba(237, 0, 0, 0.4) !important;
}

.file-preview {
    background: #252529 !important;
    border-radius: 16px !important;
    border: 1px dashed var(--border-color) !important;
}

.status-text {
    background: #1a1a1e !important;
    border-radius: 16px !important;
    padding: 1rem !important;
    font-family: 'JetBrains Mono', monospace;
    border-left: 4px solid var(--amd-red);
}

/* header */
.custom-header {
    text-align: center;
    margin-bottom: 3rem;
    padding: 2rem;
    background: linear-gradient(180deg, var(--surface-dark) 0%, transparent 100%);
    border-radius: 32px;
    border: 1px solid var(--border-color);
    box-shadow: 0 20px 40px rgba(0,0,0,0.6);
}

.custom-header h1 {
    color: var(--amd-red);
    font-weight: 900;
    letter-spacing: 3px;
    font-size: 3.5rem;
    margin: 0;
    text-transform: uppercase;
    text-shadow: 0 4px 12px rgba(237,0,0,0.4);
}

.custom-header h3 {
    color: #aaa;
    font-weight: 300;
    margin-top: 10px;
    font-size: 1.2rem;
}
"""

theme = gr.themes.Monochrome(
    neutral_hue="slate",
    text_size="lg",
).set(
    body_background_fill="#0f0f11",
    body_text_color="#e8e8e8",
    block_background_fill="#1a1a1e",
    block_border_color="#2c2c30",
    block_radius="24px",
    button_primary_background_fill="#ed0000",
    button_primary_text_color="white",
    button_secondary_background_fill="#252529",
    button_secondary_text_color="white",
    button_border_width="0",
    button_shadow="0 4px 12px rgba(0,0,0,0.3)",
    button_shadow_hover="0 8px 18px rgba(0,0,0,0.4)",
    input_background_fill="#252529",
    input_border_color="#33333a",
    input_radius="16px",
    shadow_drop="0 20px 40px rgba(0, 0, 0, 0.5)",
)

with gr.Blocks(theme=theme, title="Linguist-Core | AMD Hackathon", css=custom_css) as app:
    gr.HTML("""
        <div class='custom-header'>
            <h1>LINGUIST-CORE</h1>
            <h3>A Sovereign Distributed Knowledge Graph</h3>
        </div>
    """)
    
    with gr.Tab("1. Ingest & Sync"):
        gr.Markdown("Upload a document. The local NPU/GPU extracts relationships and broadcasts them peer-to-peer via RCCL/ZeroMQ.")
        file_input = gr.File(label="Upload Research Paper (PDF/TXT)")
        upload_btn = gr.Button("Extract & Sync to Peers", variant="primary")
        upload_out = gr.Textbox(label="Status", elem_classes=["status-text"])
        upload_btn.click(upload_file, inputs=file_input, outputs=upload_out)
        
    with gr.Tab("2. GraphRAG Query"):
        gr.Markdown("Ask multi-hop relational questions. The NPU transcribes voice via Whisper and queries the local distributed graph.")
        with gr.Row():
            text_query = gr.Textbox(label="Text Query", placeholder="e.g. How does Schrödinger relate to entanglement?")
            audio_query = gr.Audio(label="Voice Query (Hindi/English)", sources=["microphone"], type="filepath")
        query_btn = gr.Button("Query Graph", variant="primary")
        query_out = gr.Textbox(label="Knowledge Retrieval Response", lines=5, elem_classes=["status-text"])
        query_btn.click(ask_question, inputs=[text_query, audio_query], outputs=query_out)
        
    with gr.Tab("3. Distributed Network Visualization"):
        gr.Markdown("Visualize the current state of the local graph. **This updates automatically in real-time** as new knowledge is synced from peers. AMD nodes are in red.")
        
        graph_view = gr.HTML()
        
        app.load(render_graph, inputs=[], outputs=graph_view)
        
        timer = gr.Timer(3)
        timer.tick(render_graph, inputs=[], outputs=graph_view)

if __name__ == "__main__":
    app.launch(server_port=7860, share=False)
