import asyncio
from pathlib import Path
import time
import streamlit as st
import inngest
from dotenv import load_dotenv
import os
import requests

load_dotenv()

# Page config with custom theme
st.set_page_config(
    page_title="RAG Document Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
    }
    
    /* Hero section */
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Card styling */
    .card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    
    /* Upload section */
    .upload-section {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
    }
    
    /* Query section */
    .query-section {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Answer box */
    .answer-box {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .answer-text {
        font-size: 1.1rem;
        line-height: 1.6;
        color: #2d3748;
    }
    
    /* Sources box */
    .sources-box {
        background: #f7fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4facfe;
        margin-top: 1rem;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .status-success {
        background: #48bb78;
        color: white;
    }
    
    .status-info {
        background: #4299e1;
        color: white;
    }
    
    /* Divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 2rem 0;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Form styling */
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
        transition: border-color 0.3s;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* File uploader */
    .uploadedFile {
        border-radius: 8px;
        border: 2px dashed #667eea;
        padding: 1rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #718096;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Cached functions (no changes)
@st.cache_resource
def get_inngest_client() -> inngest.Inngest:
    return inngest.Inngest(app_id="rag_app", is_production=False)

def save_uploaded_pdf(file) -> Path:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / file.name
    file_bytes = file.getbuffer()
    file_path.write_bytes(file_bytes)
    return file_path

async def send_rag_ingest_event(pdf_path: Path) -> None:
    client = get_inngest_client()
    await client.send(
        inngest.Event(
            name="rag/ingest_pdf",
            data={
                "pdf_path": str(pdf_path.resolve()),
                "source_id": pdf_path.name,
            },
        )
    )

def _inngest_api_base() -> str:
    return os.getenv("INNGEST_API_BASE", "http://127.0.0.1:8288/v1")

def fetch_runs(event_id: str) -> list[dict]:
    url = f"{_inngest_api_base()}/events/{event_id}/runs"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])

def wait_for_run_output(event_id: str, timeout_s: float = 120.0, poll_interval_s: float = 0.5) -> dict:
    start = time.time()
    last_status = None
    while True:
        runs = fetch_runs(event_id)
        if runs:
            run = runs[0]
            status = run.get("status")
            last_status = status or last_status
            if status in ("Completed", "Succeeded", "Success", "Finished"):
                return run.get("output") or {}
            if status in ("Failed", "Cancelled"):
                raise RuntimeError(f"Function run {status}")
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Timed out waiting for run output (last status: {last_status})")
        time.sleep(poll_interval_s)

async def send_rag_query_event(question: str, top_k: int) -> None:
    client = get_inngest_client()
    result = await client.send(
        inngest.Event(
            name="rag/query_pdf_ai",
            data={
                "question": question,
                "top_k": top_k,
            },
        )
    )
    return result[0]

# ============ UI STARTS HERE ============

# Hero Section
st.markdown("""
    <div class="hero-section">
        <div class="hero-title">🤖 RAG Document Assistant</div>
        <div class="hero-subtitle">Upload PDFs and ask intelligent questions powered by AI</div>
    </div>
""", unsafe_allow_html=True)

# Sidebar with info
with st.sidebar:
    st.markdown("### 📊 System Info")
    st.markdown("""
        <div class="metric-card">
            <div class="metric-value">✓</div>
            <div class="metric-label">System Active</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🛠️ Features")
    st.markdown("""
    - 📄 PDF Document Upload
    - 🔍 Semantic Search
    - 🤖 AI-Powered Answers
    - 📚 Multi-Document Support
    - ⚡ Fast Processing
    """)
    
    st.markdown("---")
    st.markdown("### ℹ️ How to Use")
    st.markdown("""
    1. **Upload** your PDF documents
    2. **Wait** for processing to complete
    3. **Ask** questions about your documents
    4. **Get** AI-powered answers with sources
    """)
    
    st.markdown("---")
    st.markdown("### 🔗 Quick Links")
    st.markdown("[📖 Documentation](#) | [💬 Support](#) | [⚙️ Settings](#)")

# Main content area
col1, col2 = st.columns([1, 1], gap="large")

# Left column - Upload section
with col1:
    st.markdown('<div class="section-header">📤 Upload Documents</div>', unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "Choose a PDF file to process",
        type=["pdf"],
        accept_multiple_files=False,
        help="Upload a PDF document to add it to your knowledge base"
    )
    
    if uploaded is not None:
        with st.spinner("🔄 Processing your document..."):
            path = save_uploaded_pdf(uploaded)
            asyncio.run(send_rag_ingest_event(path))
            time.sleep(0.3)
        
        st.markdown(f"""
            <div class="answer-box">
                <div style="font-size: 1.1rem;">
                    ✅ <strong>Success!</strong> Document processed: <code>{path.name}</code>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.info("💡 You can upload another PDF or start asking questions!")

# Right column - Info/Stats
with col2:
    st.markdown('<div class="section-header">📈 Quick Stats</div>', unsafe_allow_html=True)
    
    # Mock stats (you can make these dynamic)
    stat_col1, stat_col2 = st.columns(2)
    
    with stat_col1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">📚</div>
                <div class="metric-label">Documents Ready</div>
            </div>
        """, unsafe_allow_html=True)
    
    with stat_col2:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">⚡</div>
                <div class="metric-label">Fast Processing</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.markdown("""
    - Upload clear, text-based PDFs for best results
    - Ask specific questions for more accurate answers
    - Use higher chunk retrieval for comprehensive answers
    - Check sources to verify information
    """)

# Divider
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# Query section
st.markdown('<div class="section-header">💬 Ask Questions</div>', unsafe_allow_html=True)

with st.form("rag_query_form", clear_on_submit=False):
    question = st.text_input(
        "What would you like to know?",
        placeholder="e.g., What is the main topic of the document?",
        help="Ask any question about your uploaded documents"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        top_k = st.slider(
            "Number of sources to retrieve",
            min_value=1,
            max_value=20,
            value=5,
            help="Higher values provide more context but may take longer"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        submitted = st.form_submit_button("🔍 Ask Question", use_container_width=True)
    
    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.form_submit_button("🔄 Clear", use_container_width=True):
            st.rerun()

if submitted and question.strip():
    with st.spinner("🤔 Analyzing documents and generating answer..."):
        try:
            event_id = asyncio.run(send_rag_query_event(question.strip(), int(top_k)))
            output = wait_for_run_output(event_id)
            answer = output.get("answer", "")
            sources = output.get("sources", [])
            
            # Answer section
            st.markdown("### 💡 Answer")
            st.markdown(f"""
                <div class="answer-box">
                    <div class="answer-text">{answer if answer else "No answer found. Try uploading more documents or rephrasing your question."}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Sources section
            if sources:
                st.markdown("### 📚 Sources")
                st.markdown('<div class="sources-box">', unsafe_allow_html=True)
                for idx, s in enumerate(sources, 1):
                    st.markdown(f"**{idx}.** {s}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No sources found for this query.")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("Please try again or contact support if the issue persists.")

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #718096; padding: 2rem 0;">
        <p>🤖 Powered by RAG Technology | Built with Streamlit, LlamaIndex & Ollama</p>
        <p style="font-size: 0.9rem;">Your documents are processed locally for maximum privacy 🔒</p>
    </div>
""", unsafe_allow_html=True)