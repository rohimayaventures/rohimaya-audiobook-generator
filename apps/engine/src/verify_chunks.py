import os

def verify_chunks(path="output/chunks"):
    files = sorted([f for f in os.listdir(path) if f.startswith("chunk_")])
    if not files:
        print("❌ No chunks found.")
        return False
    for f in files:
        idx = int(f.split("_")[1].split(".")[0])
        if f"chunk_{idx:03}.txt" not in files:
            print(f"❌ Missing chunk {idx:03}")
            return False
    print(f"✅ Verified {len(files)} chunks.")
    return True
