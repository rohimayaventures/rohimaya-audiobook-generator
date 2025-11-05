"""
Audiobook Producer - Main Workflow
----------------------------------
Splits a book into text chunks, generates high-quality speech using Inworld TTS,
and merges all parts into a single audiobook.

Dependencies:
- chunker.py
- tts_inworld.py
- merge_audio.py
- input text file under /input
"""

import os
from chunker import chunk_text_file
from tts_inworld import synthesize_with_inworld
from merge_audio import merge_audio_files


def main():
    input_path = "input/Eclipse_of_Fire_and_Wings_AUDIOBOOK.txt"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # 1️⃣ Split book into manageable text chunks
    print("📘 Splitting book into text chunks...")
    chunk_files = chunk_text_file(
        input_path=input_path,
        chunk_size=1500,
        output_dir=output_dir
    )

    if not chunk_files:
        print("❌ No chunks created — check your input text file.")
        return

    # 2️⃣ Generate speech for each chunk
    print("\n🎤 Generating audio files for each chunk...")
    for i, chunk_path in enumerate(chunk_files, start=1):
        with open(chunk_path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        try:
            synthesize_with_inworld(text, part_num=i)
        except Exception as e:
            print(f"⚠️ Skipping chunk {i} due to error: {e}")

    # 3️⃣ Merge all generated audio files
    print("\n🎧 Merging all audio parts into final audiobook...")
    merged_output_path = os.path.join(output_dir, "merged_audiobook.mp3")

    merge_audio_files(
        input_dir=output_dir,
        output_filename=merged_output_path
    )

    print("\n✅ Done! Your audiobook is ready at:")
    print(f"   → {merged_output_path}")


if __name__ == "__main__":
    main()