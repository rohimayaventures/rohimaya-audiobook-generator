"""
🎙️ Rohimaya Audiobook Generator
Professional Streamlit UI with Rohimaya branding
"""

import streamlit as st
import os
import time
from pathlib import Path
import tempfile
from typing import Optional

# Import Prasad's core modules
from src.chunker import chunk_text_file
from src.text_cleaner import clean_text
from src.merge_audio import merge_audio_files

# Import enhancements
from src.tts_provider import TTSManager
from src.rate_limiter import RateLimiter
from src.cost_tracker import CostTracker

# Page configuration
st.set_page_config(
    page_title="Rohimaya Audiobook Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Rohimaya Brand Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    :root {
        --phoenix-orange: #FF8C42;
        --phoenix-gold: #FFD700;
        --peacock-teal: #4A9B9B;
        --peacock-blue-gray: #7B9AA8;
        --deep-teal: #2F5F5F;
        --midnight-navy: #1A1A2E;
        --cream: #FFF8E7;
    }
    
    /* Main background */
    .main {
        background: linear-gradient(135deg, var(--cream) 0%, #FFFFFF 100%);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
        color: var(--midnight-navy);
    }
    
    h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    /* Primary button */
    .stButton > button {
        background: linear-gradient(135deg, var(--phoenix-orange) 0%, #FF6B1A 100%);
        color: white;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 12px;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 140, 66, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 140, 66, 0.4);
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed var(--peacock-teal);
        border-radius: 12px;
        padding: 2rem;
        background: white;
    }
    
    /* Selectbox */
    .stSelectbox label {
        color: var(--midnight-navy);
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--phoenix-orange) 0%, var(--phoenix-gold) 100%);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: var(--peacock-teal);
        font-weight: 700;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--peacock-teal);
        color: white;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: var(--peacock-teal);
        color: white;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: var(--peacock-blue-gray);
        border-left: 4px solid var(--peacock-teal);
        border-radius: 8px;
    }
    
    /* Warning boxes */
    .stWarning {
        background-color: #FFF3CD;
        border-left: 4px solid var(--phoenix-gold);
        border-radius: 8px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--midnight-navy) 0%, var(--deep-teal) 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom header */
    .custom-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, var(--peacock-teal) 0%, var(--deep-teal) 100%);
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(74, 155, 155, 0.2);
    }
    
    .custom-header h1 {
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .custom-header p {
        color: var(--cream);
        font-style: italic;
        font-size: 1.2rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'cost_tracker' not in st.session_state:
    st.session_state.cost_tracker = CostTracker()

if 'generation_history' not in st.session_state:
    st.session_state.generation_history = []

# Custom Header
st.markdown("""
<div class="custom-header">
    <h1>🎙️ Rohimaya Audiobook Generator</h1>
    <p>Where the Phoenix Rises and the Peacock Dances</p>
    <p style="font-size: 0.9rem; margin-top: 0.5rem;">Ascend • Flourish • Enlighten</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.markdown("## 🎛️ Configuration")
    
    # Voice Selection
    st.markdown("### 🎤 Voice Selection")
    voice_options = {
        "alloy": "Neutral, balanced",
        "echo": "Male, clear",
        "fable": "British, expressive",
        "onyx": "Deep male",
        "nova": "Female, warm",
        "shimmer": "Female, soft"
    }
    
    selected_voice = st.selectbox(
        "Narrator voice:",
        options=list(voice_options.keys(,
        index=0
    ),
        index=0
    ),
        format_func=lambda x: f"{x.title()} - {voice_options[x]}",
        help="Choose the AI voice for your audiobook"
    )
    
    # Advanced Options
    with st.expander("⚙️ Advanced Settings"):
        chunk_size = st.slider(
            "Chunk size:",
            min_value=500,
            max_value=3000,
            value=1500,
            step=100,
            help="Smaller chunks = more API calls but better quality"
        )
        
        speed = st.slider(
            "Narration speed:",
            min_value=0.8,
            max_value=1.5,
            value=1.0,
            step=0.1,
            help="1.0 = normal speed"
        )
        
        acx_ready = st.checkbox(
            "ACX-ready export",
            value=True,
            help="Format for Amazon ACX (44.1kHz, 192kbps)"
        )
    
    # Cost Summary
    st.markdown("---")
    st.markdown("### 💰 Session Cost")
    summary = st.session_state.cost_tracker.get_summary()
    st.metric("Total Cost", f"${summary['total_cost']:.2f}")
    st.metric("Characters", f"{summary['total_characters']:,}")
    st.metric("Requests", summary['total_requests'])

# Main Content
tab1, tab2, tab3 = st.tabs(["📤 Generate", "📊 History", "ℹ️ About"])

with tab1:
    st.markdown("## 📚 Upload Your Manuscript")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose your manuscript:",
            type=['txt', 'docx', 'md'],
            help="Supported formats: .txt, .docx, .md"
        )
    
    with col2:
        st.markdown("### 📖 Supported Formats")
        st.markdown("""
        - `.txt` - Plain text
        - `.docx` - Word document
        - `.md` - Markdown
        """)
    
    if uploaded_file:
        # Display file info
        file_size = len(uploaded_file.getvalue())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 File", uploaded_file.name)
        with col2:
            st.metric("💾 Size", f"{file_size / 1024:.1f} KB")
        with col3:
            # Read and count
            try:
                content = uploaded_file.getvalue().decode('utf-8')
                word_count = len(content.split())
                st.metric("📝 Words", f"{word_count:,}")
            except:
                st.metric("📝 Words", "Error reading")
                content = None
        
        if content:
            # Preview
            with st.expander("👁️ Preview First 500 Characters"):
                st.text(content[:500] + ("..." if len(content) > 500 else ""))
            
            # Cost Estimate
            char_count = len(content)
            est_cost = st.session_state.cost_tracker.calculate_cost('openai', char_count)
            
            st.info(f"💰 **Estimated Cost:** ${est_cost:.2f} • **Characters:** {char_count:,}")
            
            if est_cost > 10:
                st.warning(f"⚠️ This will cost ~${est_cost:.2f}. Large manuscript! Consider breaking into chapters.")
            
            # Generate Button
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                generate_button = st.button(
                    "🎬 Generate Audiobook",
                    use_container_width=True,
                    type="primary"
                )
            
            if generate_button:
                # Generation process
                with st.spinner("🎤 Generating your audiobook..."):
                    try:
                        # Create temp directories
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Save uploaded file
                            input_path = os.path.join(temp_dir, "input.txt")
                            with open(input_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            
                            output_dir = os.path.join(temp_dir, "output")
                            os.makedirs(output_dir, exist_ok=True)
                            
                            # Progress tracking
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            # Step 1: Clean text
                            status_text.text("🧹 Cleaning text...")
                            progress_bar.progress(10)
                            cleaned_text = clean_text(content)
                            
                            # Step 2: Chunk
                            status_text.text("✂️ Creating smart chunks...")
                            progress_bar.progress(20)
                            
                            cleaned_path = os.path.join(temp_dir, "cleaned.txt")
                            with open(cleaned_path, 'w', encoding='utf-8') as f:
                                f.write(cleaned_text)
                            
                            chunk_files = chunk_text_file(
                                input_path=cleaned_path,
                                chunk_size=chunk_size,
                                output_dir=output_dir
                            )
                            
                            num_chunks = len(chunk_files)
                            status_text.text(f"📋 Created {num_chunks} chunks")
                            progress_bar.progress(30)
                            
                            # Step 3: Initialize TTS
                            status_text.text("🎙️ Initializing TTS...")
                            progress_bar.progress(35)
                            
                            config = {
                                'openai_api_key': st.secrets.get('openai', {}).get('api_key'),
                                'inworld_api_key': st.secrets.get('inworld', {}).get('api_key'),
                                'inworld_workspace_id': st.secrets.get('inworld', {}).get('workspace_id'),
                                'elevenlabs_api_key': st.secrets.get('elevenlabs', {}).get('api_key')
                            }
                            
                            tts_manager = TTSManager(config)
                            cost_tracker = st.session_state.cost_tracker
                            rate_limiter = RateLimiter(max_requests_per_minute=60)
                            
                            # Step 4: Generate audio
                            start_time = time.time()
                            audio_files = []
                            
                            for i, chunk_path in enumerate(chunk_files):
                                status_text.text(f"🎤 Generating audio ({i+1}/{num_chunks})...")
                                progress = 35 + int(((i + 1) / num_chunks) * 50)
                                progress_bar.progress(progress)
                                
                                # Rate limiting
                                rate_limiter.wait_if_needed()
                                
                                # Read chunk
                                with open(chunk_path, 'r', encoding='utf-8') as f:
                                    chunk_text = f.read()
                                
                                # Generate audio
                                audio_bytes = tts_manager.synthesize_with_fallback(
                                    chunk_text,
                                    selected_voice
                                )
                                
                                # Save audio
                                audio_path = os.path.join(output_dir, f"part_{i+1:03d}.mp3")
                                with open(audio_path, 'wb') as f:
                                    f.write(audio_bytes)
                                
                                audio_files.append(audio_path)
                                
                                # Track cost
                                cost_tracker.track('openai', chunk_text)
                            
                            generation_time = time.time() - start_time
                            
                            # Step 5: Merge
                            status_text.text("🔗 Merging audio...")
                            progress_bar.progress(90)
                            
                            final_output = os.path.join(output_dir, "audiobook.mp3")
                            merge_audio_files(
                                input_dir=output_dir,
                                output_filename=final_output
                            )
                            
                            # Complete
                            progress_bar.progress(100)
                            status_text.text("✅ Complete!")
                            
                            # Success
                            st.success(f"""
                            🎉 **Audiobook Generated Successfully!**
                            
                            - **Chunks:** {num_chunks}
                            - **Time:** {generation_time/60:.1f} minutes
                            - **Cost:** ${cost_tracker.get_summary()['total_cost']:.2f}
                            - **Size:** {os.path.getsize(final_output) / (1024*1024):.1f} MB
                            """)
                            
                            # Download
                            with open(final_output, 'rb') as audio_file:
                                st.download_button(
                                    label="📥 Download Audiobook",
                                    data=audio_file,
                                    file_name=f"{Path(uploaded_file.name).stem}_audiobook.mp3",
                                    mime="audio/mpeg",
                                    use_container_width=True
                                )
                            
                            # Audio player
                            st.audio(final_output)
                            
                            # Add to history
                            st.session_state.generation_history.append({
                                'filename': uploaded_file.name,
                                'timestamp': time.time(),
                                'cost': cost_tracker.get_summary()['total_cost'],
                                'duration': generation_time,
                                'voice': selected_voice
                            })
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.exception(e)

with tab2:
    st.markdown("## 📊 Generation History")
    
    if st.session_state.generation_history:
        for entry in reversed(st.session_state.generation_history):
            with st.expander(f"🎧 {entry['filename']} - {time.strftime('%Y-%m-%d %H:%M', time.localtime(entry['timestamp']))}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Cost", f"${entry['cost']:.2f}")
                with col2:
                    st.metric("Duration", f"{entry['duration']/60:.1f} min")
                with col3:
                    st.metric("Voice", entry['voice'].title())
    else:
        st.info("📭 No audiobooks generated yet. Upload a manuscript to get started!")

with tab3:
    st.markdown("## ℹ️ About Rohimaya Audiobook Generator")
    
    st.markdown("""
    ### 🎯 What Is This?
    
    Transform your written manuscripts into professional audiobooks using AI.
    Built on **Prasad Pagade's** production-ready pipeline with Rohimaya enhancements.
    
    ### ✨ Features
    
    **Core (by Prasad):**
    - Smart text chunking
    - Intelligent cleaning
    - Automatic merging
    
    **Enhanced:**
    - Multiple AI voices
    - Real-time progress
    - Cost tracking
    - ACX-ready export
    
    ### 💰 Cost Comparison
    
    | Method | Cost | Time |
    |--------|------|------|
    | Professional Narrator | $1,500+ | 2-4 weeks |
    | **Rohimaya AI** | **$6-60** | **30 min** |
    
    ### 🦚 About Rohimaya
    
    *Where the Phoenix Rises and the Peacock Dances*
    
    AI-powered tools helping authors write, format, and publish their books.
    
    **Tagline:** Ascend • Flourish • Enlighten
    
    ### 📞 Support
    
    Email: rohimayapublishing@gmail.com
    
    ---
    
    **Built with 🔥 and 🦚 by Prasad (Phoenix) & Hannah (Peacock)**
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7B9AA8; padding: 1rem;'>
    <p><strong>Rohimaya Publishing</strong></p>
    <p style='font-style: italic; font-size: 0.9rem;'>Where the Phoenix Rises and the Peacock Dances</p>
</div>
""", unsafe_allow_html=True)
