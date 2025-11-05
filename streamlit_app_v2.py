"""
🎙️ Rohimaya Audiobook Generator
Professional-grade TTS application built on Prasad Pagade's proven architecture
"""
import streamlit as st
import os
import tempfile
from pathlib import Path
from openai import OpenAI

# Prasad's proven modules
from src.chunker import chunk_text_file
from src.text_cleaner import clean_text
from src.merge_audio import merge_audio_files

# ========================================
# PAGE CONFIGURATION
# ========================================
st.set_page_config(
    page_title="Rohimaya Audiobook Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# ROHIMAYA BRAND STYLING - ULTRA PIZZAZZ EDITION
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;600;700&display=swap');
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-20px); }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(255, 140, 66, 0.5); }
        50% { box-shadow: 0 0 40px rgba(255, 215, 0, 0.8); }
    }
    
    @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
    }
    
    :root {
        --phoenix-orange: #FF8C42;
        --phoenix-gold: #FFD700;
        --peacock-teal: #4A9B9B;
        --peacock-blue: #7B9AA8;
        --midnight-navy: #1A1A2E;
        --cream: #FFF8E7;
    }
    
    /* ARTSY ANIMATED BACKGROUND WITH PATTERN */
    .main {
        background: 
            radial-gradient(circle at 10% 20%, rgba(255, 140, 66, 0.05) 0%, transparent 20%),
            radial-gradient(circle at 90% 80%, rgba(74, 155, 155, 0.05) 0%, transparent 20%),
            radial-gradient(circle at 50% 50%, rgba(255, 215, 0, 0.03) 0%, transparent 30%),
            linear-gradient(135deg, 
                var(--cream) 0%, 
                #FFF5E1 25%,
                #FFFACD 50%,
                #FFF5E1 75%,
                var(--cream) 100%
            );
        background-size: 
            300% 300%,
            300% 300%,
            400% 400%,
            400% 400%;
        animation: gradientShift 15s ease infinite;
        font-family: 'Inter', sans-serif;
        position: relative;
    }
    
    /* PEACOCK FEATHER & PHOENIX FLAME ARTISTIC OVERLAY */
    .main::after {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            repeating-radial-gradient(circle at 15% 25%, 
                transparent 0px, 
                transparent 10px,
                rgba(74, 155, 155, 0.02) 10px, 
                rgba(74, 155, 155, 0.02) 20px
            ),
            repeating-radial-gradient(circle at 85% 75%, 
                transparent 0px, 
                transparent 15px,
                rgba(255, 140, 66, 0.02) 15px, 
                rgba(255, 140, 66, 0.02) 30px
            ),
            linear-gradient(45deg, 
                transparent 48%, 
                rgba(255, 215, 0, 0.01) 49%, 
                rgba(255, 215, 0, 0.01) 51%, 
                transparent 52%
            );
        background-size: 200px 200px, 250px 250px, 100px 100px;
        pointer-events: none;
        z-index: 1;
        opacity: 0.8;
    }
    
    /* PEACOCK FEATHER PATTERN OVERLAY */
    .main::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 20% 50%, rgba(74, 155, 155, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(255, 140, 66, 0.03) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* ANIMATED TITLE */
    h1 {
        font-family: 'Playfair Display', serif !important;
        background: linear-gradient(135deg, 
            var(--phoenix-orange) 0%,
            var(--phoenix-gold) 25%,
            var(--phoenix-orange) 50%,
            var(--phoenix-gold) 75%,
            var(--phoenix-orange) 100%
        );
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        font-size: 3.5rem !important;
        margin-bottom: 0 !important;
        font-weight: 900 !important;
        animation: shimmer 3s linear infinite, float 3s ease-in-out infinite;
        text-shadow: 0 0 30px rgba(255, 140, 66, 0.3);
        letter-spacing: 2px;
    }
    
    /* GLOWING TAGLINE */
    .tagline {
        text-align: center;
        font-style: italic;
        color: var(--peacock-teal);
        font-size: 1.4rem;
        margin: 0.5rem 0 2rem 0;
        font-family: 'Playfair Display', serif;
        animation: float 4s ease-in-out infinite;
        text-shadow: 0 0 10px rgba(74, 155, 155, 0.5);
        font-weight: 600;
    }
    
    /* ULTRA GLOWING BUTTON */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--phoenix-orange), #FFB366, var(--phoenix-gold)) !important;
        background-size: 200% auto !important;
        color: white !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 15px !important;
        padding: 1.2rem 2.5rem !important;
        font-size: 1.3rem !important;
        box-shadow: 0 8px 25px rgba(255, 140, 66, 0.4) !important;
        transition: all 0.4s ease !important;
        width: 100% !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        animation: glow 2s ease-in-out infinite;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button[kind="primary"]::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(255, 255, 255, 0.3), 
            transparent
        );
        transition: left 0.5s;
    }
    
    .stButton > button[kind="primary"]:hover::before {
        left: 100%;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-5px) scale(1.02) !important;
        box-shadow: 0 12px 35px rgba(255, 140, 66, 0.6) !important;
        background-position: right center !important;
    }
    
    /* ANIMATED SIDEBAR */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, 
            var(--midnight-navy) 0%,
            #2A2A3E 50%,
            #1A1A2E 100%
        ) !important;
        border-right: 3px solid var(--phoenix-orange);
        box-shadow: 5px 0 15px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] h2 {
        color: var(--phoenix-orange) !important;
        font-family: 'Playfair Display', serif !important;
        text-shadow: 0 0 10px rgba(255, 140, 66, 0.5);
        font-weight: 700 !important;
    }
    
    /* GLOWING FILE UPLOADER */
    .uploadedFile {
        background: linear-gradient(135deg, 
            rgba(74, 155, 155, 0.1) 0%,
            rgba(74, 155, 155, 0.2) 100%
        ) !important;
        border: 3px solid var(--peacock-teal) !important;
        border-radius: 15px !important;
        padding: 1.5rem !important;
        box-shadow: 0 0 20px rgba(74, 155, 155, 0.3);
        transition: all 0.3s ease;
    }
    
    .uploadedFile:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 25px rgba(74, 155, 155, 0.5);
    }
    
    /* ANIMATED SUCCESS BOXES */
    .stSuccess {
        background: linear-gradient(135deg, 
            rgba(74, 155, 155, 0.1) 0%,
            rgba(74, 155, 155, 0.2) 100%
        ) !important;
        border-left: 6px solid var(--peacock-teal) !important;
        border-radius: 10px;
        animation: float 3s ease-in-out infinite;
        box-shadow: 0 4px 15px rgba(74, 155, 155, 0.2);
    }
    
    .stInfo {
        background: linear-gradient(135deg, 
            rgba(255, 140, 66, 0.1) 0%,
            rgba(255, 140, 66, 0.2) 100%
        ) !important;
        border-left: 6px solid var(--phoenix-orange) !important;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(255, 140, 66, 0.2);
    }
    
    /* GLOWING PROGRESS BAR */
    .stProgress > div > div {
        background: linear-gradient(90deg, 
            var(--phoenix-orange), 
            var(--phoenix-gold),
            var(--phoenix-orange)
        ) !important;
        background-size: 200% auto !important;
        animation: shimmer 2s linear infinite;
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
        border-radius: 10px;
    }
    
    /* METRIC CARDS WITH GLOW */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: var(--phoenix-orange) !important;
        text-shadow: 0 0 10px rgba(255, 140, 66, 0.3);
    }
    
    /* TABS WITH STYLE */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--phoenix-orange), #FFB366) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(255, 140, 66, 0.3);
    }
    
    /* DOWNLOAD BUTTON SPECIAL STYLE */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--peacock-teal), #5FB8B8) !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        padding: 1rem 2rem !important;
        font-size: 1.1rem !important;
        box-shadow: 0 6px 20px rgba(74, 155, 155, 0.4) !important;
        transition: all 0.3s ease !important;
        animation: glow 3s ease-in-out infinite;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-3px) scale(1.05) !important;
        box-shadow: 0 10px 30px rgba(74, 155, 155, 0.6) !important;
    }
    
    /* SLIDER STYLING */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, var(--phoenix-orange), var(--phoenix-gold)) !important;
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# HEADER
# ========================================
st.title("🎙️ Rohimaya Audiobook Generator")
st.markdown('<p class="tagline">Where the Phoenix Rises and the Peacock Dances</p>', unsafe_allow_html=True)

# ========================================
# SIDEBAR CONFIGURATION
# ========================================
with st.sidebar:
    st.markdown("## 🎛️ Configuration")
    
    st.markdown("### 🎤 Voice Selection")
    
    VOICES = {
        "alloy": "🎭 Neutral & Balanced",
        "echo": "👔 Male, Clear",
        "fable": "🎩 British, Expressive",
        "onyx": "🎙️ Deep Male",
        "nova": "👩 Female, Warm",
        "shimmer": "✨ Female, Soft"
    }
    
    selected_voice = st.selectbox(
        "Narrator Voice:",
        options=list(VOICES.keys()),
        format_func=lambda x: f"{x.title()} - {VOICES[x]}",
        help="Choose the AI voice that will narrate your audiobook"
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ Advanced Settings")
    
    chunk_size = st.slider(
        "Chunk Size (characters)",
        min_value=500,
        max_value=3000,
        value=1500,
        step=100,
        help="Smaller chunks = more API calls but better pacing"
    )
    
    st.markdown("---")
    st.markdown("### 💰 Cost Estimate")
    st.info("OpenAI TTS: ~$0.015 per 1K characters\n\nTypical 80K word novel ≈ $6")
    
    st.markdown("---")
    st.markdown("### 📚 About")
    st.markdown("""
    **Built with** ❤️ **by Rohimaya Publishing**
    
    Core TTS Engine: Prasad Pagade
    
    *Ascend • Flourish • Enlighten*
    """)

# ========================================
# MAIN CONTENT
# ========================================
tab1, tab2, tab3 = st.tabs(["📤 Generate", "📊 History", "ℹ️ About"])

with tab1:
    st.markdown("### 📄 Upload Your Manuscript")
    
    uploaded_file = st.file_uploader(
        "Choose your manuscript file",
        type=["txt", "docx", "md"],
        help="Supported formats: TXT, DOCX, MD (Max 200MB)"
    )
    
    if uploaded_file:
        # File info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📁 File", uploaded_file.name)
        with col2:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.metric("📊 Size", f"{file_size_mb:.2f} MB")
        with col3:
            # Estimate word count (rough)
            text_preview = uploaded_file.getvalue().decode('utf-8', errors='ignore')[:1000]
            word_count = len(text_preview.split()) * (uploaded_file.size / len(text_preview.encode('utf-8')))
            st.metric("📝 Est. Words", f"{int(word_count):,}")
        
        st.markdown("---")
        
        # Generate button
        if st.button("🎬 Generate Audiobook", type="primary", use_container_width=True):
            
            try:
                # Initialize OpenAI client
                client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                
                # Create temporary directory for processing
                with tempfile.TemporaryDirectory() as tmp_dir:
                    
                    # ===== STEP 1: Save & Clean Text =====
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("📥 Processing manuscript...")
                    progress_bar.progress(10)
                    
                    # Save uploaded file
                    input_path = os.path.join(tmp_dir, "manuscript.txt")
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    
                    # Clean text
                    status_text.text("🧹 Cleaning text...")
                    progress_bar.progress(20)
                    raw_text = open(input_path, encoding='utf-8', errors='ignore').read()
                    cleaned_text = clean_text(raw_text)
                    
                    cleaned_path = os.path.join(tmp_dir, "cleaned.txt")
                    with open(cleaned_path, "w", encoding='utf-8') as f:
                        f.write(cleaned_text)
                    
                    # ===== STEP 2: Create Chunks =====
                    status_text.text("✂️ Creating text chunks...")
                    progress_bar.progress(30)
                    
                    output_dir = os.path.join(tmp_dir, "output")
                    os.makedirs(output_dir, exist_ok=True)
                    
                    chunk_files = chunk_text_file(
                        input_path=cleaned_path,
                        chunk_size=chunk_size,
                        output_dir=output_dir
                    )
                    
                    num_chunks = len(chunk_files)
                    st.info(f"📋 Created {num_chunks} text chunks")
                    
                    # ===== STEP 3: Generate Audio =====
                    status_text.text(f"🎙️ Generating audio (0/{num_chunks})...")
                    progress_bar.progress(40)
                    
                    audio_files = []
                    
                    for i, chunk_file in enumerate(chunk_files):
                        # Read chunk
                        with open(chunk_file, "r", encoding='utf-8') as f:
                            chunk_text = f.read().strip()
                        
                        # Generate audio with OpenAI
                        response = client.audio.speech.create(
                            model="tts-1",
                            voice=selected_voice,
                            input=chunk_text
                        )
                        
                        # Save audio chunk
                        audio_path = os.path.join(output_dir, f"audio_{i:03d}.mp3")
                        with open(audio_path, "wb") as f:
                            f.write(response.content)
                        
                        audio_files.append(audio_path)
                        
                        # Update progress
                        chunk_progress = 40 + int(50 * (i + 1) / num_chunks)
                        progress_bar.progress(chunk_progress)
                        status_text.text(f"🎙️ Generating audio ({i+1}/{num_chunks})...")
                    
                    # ===== STEP 4: Merge Audio =====
                    status_text.text("🎧 Merging audio files...")
                    progress_bar.progress(95)
                    
                    final_output = os.path.join(tmp_dir, "audiobook.mp3")
                    merge_audio_files(output_dir, final_output)
                    
                    # ===== COMPLETE =====
                    progress_bar.progress(100)
                    status_text.text("✅ Complete!")
                    
                    st.success("🎉 Your audiobook is ready!")
                    
                    # Download button
                    with open(final_output, "rb") as audio_file:
                        audio_data = audio_file.read()
                        
                        st.download_button(
                            label="📥 Download Audiobook MP3",
                            data=audio_data,
                            file_name=f"{Path(uploaded_file.name).stem}_audiobook.mp3",
                            mime="audio/mpeg",
                            use_container_width=True
                        )
                    
                    # Show file size
                    audio_size_mb = len(audio_data) / (1024 * 1024)
                    st.info(f"📊 Final audiobook size: {audio_size_mb:.2f} MB")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                with st.expander("🔍 See full error details"):
                    st.exception(e)
    
    else:
        st.info("👆 Upload a manuscript file to get started!")

with tab2:
    st.markdown("### 📊 Generation History")
    st.info("History feature coming soon!")

with tab3:
    st.markdown("### ℹ️ About Rohimaya Audiobook Generator")
    
    st.markdown("""
    **Transform your manuscript into a professional audiobook in minutes!**
    
    #### 🚀 Features:
    - 6 professional AI voices
    - Automatic text cleaning & optimization
    - Intelligent chunking for natural pacing
    - High-quality MP3 output
    - Cost-effective ($6-60 per book vs $1,500+ traditional)
    
    #### 🔧 Technology:
    - **Core Engine:** Built on Prasad Pagade's proven TTS architecture
    - **Voice Provider:** OpenAI TTS-1
    - **Processing:** Python + FFmpeg
    - **Interface:** Streamlit
    
    #### 💝 Created by Rohimaya Publishing
    *Where the Phoenix Rises and the Peacock Dances*
    
    **Ascend • Flourish • Enlighten**
    """)
