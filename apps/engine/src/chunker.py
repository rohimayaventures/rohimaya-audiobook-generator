import os

def chunk_text_file(input_path, chunk_size=1500, output_dir="output"):
    """
    Splits a large text file into smaller chunks and saves them as numbered .txt files.
    Each chunk is saved directly in the same 'output' folder as MP3s.
    Returns a list of all generated chunk file paths.
    """

    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        return []

    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print(f"⚠️ Input file is empty: {input_path}")
        return []

    os.makedirs(output_dir, exist_ok=True)

    # Split text into manageable pieces (on sentence boundaries if possible)
    chunks = []
    current_chunk = []
    current_length = 0
    sentences = text.split(". ")

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        # If adding this sentence exceeds chunk size, start a new one
        if current_length + len(sentence) > chunk_size:
            chunks.append(". ".join(current_chunk).strip() + ".")
            current_chunk = [sentence]
            current_length = len(sentence)
        else:
            current_chunk.append(sentence)
            current_length += len(sentence)

    # Add the last chunk
    if current_chunk:
        chunks.append(". ".join(current_chunk).strip() + ".")

    chunk_files = []
    for i, chunk in enumerate(chunks, start=1):
        chunk_filename = os.path.join(output_dir, f"chunk_{i:03}.txt")
        with open(chunk_filename, "w", encoding="utf-8") as f:
            f.write(chunk.strip())
        chunk_files.append(chunk_filename)
        print(f"📝 Created {chunk_filename}")

    print(f"\n✅ Created {len(chunk_files)} chunks total in '{output_dir}'")
    return chunk_files