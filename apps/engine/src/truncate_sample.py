import os
from text_cleaner import clean_text

input_path = os.path.join("input", "Eclipse_of_Fire_and_Wings_AUDIOBOOK.txt")
output_path = os.path.join("input", "Eclipse_of_Fire_and_Wings_SAMPLE.txt")

# Read the full text
with open(input_path, "r", encoding="utf-8") as f:
    text = f.read()
    text = clean_text(text)

# Find the end of Chapter 1
marker = "CHAPTER TWO"  # Adjust if your chapter headings differ
end_index = text.find(marker)
if end_index != -1:
    sample_text = text[:end_index]
else:
    sample_text = text  # fallback — use full text if marker not found

# Save the truncated sample
with open(output_path, "w", encoding="utf-8") as f:
    f.write(sample_text.strip())

print(f"✅ Sample truncated file created: {output_path}")