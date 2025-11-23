import os
from docx import Document

def convert_docx_to_chunks(path, max_chars=2000):
    doc = Document(path)
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    chunks, chunk, total_chars = [], [], 0

    for para in full_text.split("\n"):
        if total_chars + len(para) > max_chars:
            chunks.append(" ".join(chunk))
            chunk, total_chars = [], 0
        chunk.append(para)
        total_chars += len(para)

    if chunk:
        chunks.append(" ".join(chunk))

    os.makedirs("output/chunks", exist_ok=True)
    for i, c in enumerate(chunks, 1):
        with open(f"output/chunks/chunk_{i:03}.txt", "w") as f:
            f.write(c.strip())

    print(f"✅ Created {len(chunks)} chunks.")
    return len(chunks)
