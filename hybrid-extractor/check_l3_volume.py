"""Quick check: how many chunks would trigger L3 at various thresholds?"""
import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from hybrid_extractor import HybridExtractor

AUDIT_DIR = Path(r"c:\googledrive\priv\AI\projekty\LifeCommandCenter\insights\audit")
CHUNK_SIZE, OVERLAP = 1200, 100

def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    chunks, start = [], 0
    while start < len(text):
        c = text[start:start+size].strip()
        if c: chunks.append(c)
        start += size - overlap
    return chunks

ext = HybridExtractor(enable_llm=False)
all_counts = []
for f in sorted(AUDIT_DIR.glob("*.md")):
    for c in chunk_text(f.read_text(encoding="utf-8")):
        ents = ext.extract(c)
        all_counts.append(len(ents))

print(f"Total chunks: {len(all_counts)}")
for threshold in [3, 5, 7, 10]:
    below = sum(1 for c in all_counts if c < threshold)
    print(f"  <{threshold} entities: {below} chunks ({below/len(all_counts)*100:.1f}%) → L3 calls")
