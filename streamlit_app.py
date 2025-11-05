"""
Rohimaya Audiobook Generator - Clean Build
Using Prasad's proven working code
"""
import streamlit as st
import os
import tempfile
from pathlib import Path

# Import Prasad's working modules
from src.chunker import chunk_text_file
from src.text_cleaner import clean_text
from src.merge_audio import merge_audio_files

# Import ONLY OpenAI (proven to work)
from openai import OpenAI

# Page config
st.set_page_config(
    page_title="Rohimaya Audiobook Generator",
    page_icon="🎙️",
    layout="wide"
)

# Simple styling
st.markdown("""
<style>
    .main {background-color: #FFF8E7;}
    h1 {color: #FF8C42;}
</style>
""", unsafe_allow_html=True)

# Header
st.title("🎙️ Rohimaya Audiobook Generator")
st.markdown("*Where the Phoenix Rises and the Peacock Dances*")

# Sidebar
with st.sidebar:
    st.header("🎛️ Settings")
    
    # Voice selection - SIMPLE list
    voice = st.selectbox(
        "Narrator Voice:",
        ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        help="Choose your narrator voice"
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.info("Built with ❤️ using Prasad's TTS engine")

# Main content
uploaded_file = st.file_uploader(
    "📄 Upload Your Manuscript",
    type=["txt", "docx", "md"],
    help="Upload your book manuscript"
)

if uploaded_file:
    st.success(f"✅ Uploaded: {uploaded_file.name}")
    
    if st.button("🎬 Generate Audiobook", type="primary", use_container_width=True):
        try:
            # Create temp directory
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Save uploaded file
                input_path = os.path.join(tmp_dir, "manuscript.txt")
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                # Progress
                progress = st.progress(0)
                status = st.empty()
                
                # Step 1: Clean text
                status.text("🧹 Cleaning text...")
                progress.progress(20)
                cleaned_text = clean_text(open(input_path).read())
                
                # Step 2: Chunk text
                status.text("✂️ Creating chunks...")
                progress.progress(40)
                output_dir = os.path.join(tmp_dir, "output")
                os.makedirs(output_dir, exist_ok=True)
                
                cleaned_path = os.path.join(tmp_dir, "cleaned.txt")
                with open(cleaned_path, "w") as f:
                    f.write(cleaned_text)
                
                chunk_files = chunk_text_file(cleaned_path, chunk_size=1500, output_dir=output_dir)
                
                # Step 3: Generate audio with OpenAI
                status.text(f"🎙️ Generating audio ({len(chunk_files)} chunks)...")
                progress.progress(60)
                
                # Get OpenAI key from secrets
                client = OpenAI(api_key=st.secrets["openai"]["api_key"])
                
                audio_files = []
                for i, chunk_file in enumerate(chunk_files):
                    with open(chunk_file, "r") as f:
                        text = f.read()
                    
                    # Generate audio
                    response = client.audio.speech.create(
                        model="tts-1",
                        voice=voice,
                        input=text
                    )
                    
                    # Save audio
                    audio_path = os.path.join(output_dir, f"part_{i:03d}.mp3")
                    with open(audio_path, "wb") as f:
                        f.write(response.content)
                    audio_files.append(audio_path)
                    
                    # Update progress
                    progress.progress(60 + int(30 * (i + 1) / len(chunk_files)))
                
                # Step 4: Merge audio
                status.text("🎧 Merging audio files...")
                progress.progress(95)
                
                final_output = os.path.join(tmp_dir, "audiobook.mp3")
                merge_audio_files(output_dir, final_output)
                
                # Done!
                progress.progress(100)
                status.text("✅ Complete!")
                
                # Download button
                with open(final_output, "rb") as f:
                    st.download_button(
                        label="📥 Download Audiobook",
                        data=f,
                        file_name="audiobook.mp3",
                        mime="audio/mpeg"
                    )
                
                st.success("🎉 Your audiobook is ready!")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)
