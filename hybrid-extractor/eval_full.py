"""
Task 2.7: Full evaluation of HybridExtractor on audit corpus.
Chunks 9 audit files → runs L1+L2 → reports entity density & quality.
"""
import sys, json, re, time
from pathlib import Path
from collections import Counter

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8')

from hybrid_extractor import HybridExtractor

AUDIT_DIR = Path(r"c:\googledrive\priv\AI\projekty\LifeCommandCenter\insights\audit")
CHUNK_SIZE = 1200  # chars (~300 tokens, E²GraphRAG default ~1200 tokens but our text is dense)
CHUNK_OVERLAP = 100


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Simple char-based chunking with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def main():
    print("Loading HybridExtractor (L1+L2, no LLM)...")
    ext = HybridExtractor(enable_llm=False)
    print(f"  Ruler patterns: {ext.layer2.pattern_count}, entities: {ext.layer2.entity_count}")
    print()

    all_chunks = []
    for f in sorted(AUDIT_DIR.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        for i, c in enumerate(chunks):
            all_chunks.append({"file": f.stem, "chunk_idx": i, "text": c})

    print(f"Audit files: {len(list(AUDIT_DIR.glob('*.md')))}")
    print(f"Total chunks: {len(all_chunks)}")
    print()

    # Run extraction
    t0 = time.time()
    results = []
    for item in all_chunks:
        entities = ext.extract(item["text"])
        by_source = Counter(e.source for e in entities)
        by_label = Counter(e.label for e in entities)
        results.append({
            "file": item["file"],
            "chunk_idx": item["chunk_idx"],
            "n_entities": len(entities),
            "by_source": dict(by_source),
            "by_label": dict(by_label),
            "entities": [(e.text, e.label, e.source) for e in entities],
        })
    elapsed = time.time() - t0

    # --- Aggregate stats ---
    n_chunks = len(results)
    total_ents = sum(r["n_entities"] for r in results)
    avg_ents = total_ents / n_chunks

    # Source breakdown
    source_totals = Counter()
    label_totals = Counter()
    for r in results:
        for src, cnt in r["by_source"].items():
            source_totals[src] += cnt
        for lbl, cnt in r["by_label"].items():
            label_totals[lbl] += cnt

    # Distribution
    ent_counts = [r["n_entities"] for r in results]
    ent_counts_sorted = sorted(ent_counts)
    p50 = ent_counts_sorted[n_chunks // 2]
    p90 = ent_counts_sorted[int(n_chunks * 0.9)]
    p10 = ent_counts_sorted[int(n_chunks * 0.1)]

    print(f"{'='*60}")
    print(f"FULL EVALUATION: {n_chunks} chunks from 9 audits")
    print(f"{'='*60}")
    print(f"Time: {elapsed:.1f}s ({elapsed/n_chunks*1000:.0f}ms/chunk)")
    print(f"Total entities: {total_ents}")
    print(f"Avg entities/chunk: {avg_ents:.1f}")
    print(f"Distribution: p10={p10}, p50={p50}, p90={p90}, min={min(ent_counts)}, max={max(ent_counts)}")
    print()

    print("BY SOURCE:")
    for src, cnt in source_totals.most_common():
        print(f"  {src:25s} {cnt:5d} ({cnt/total_ents*100:.1f}%)")
    print()

    print("BY LABEL:")
    for lbl, cnt in label_totals.most_common():
        print(f"  {lbl:25s} {cnt:5d} ({cnt/total_ents*100:.1f}%)")
    print()

    # Show 3 high-entity chunks for manual inspection
    results_sorted = sorted(results, key=lambda r: r["n_entities"], reverse=True)
    print("TOP 3 HIGH-ENTITY CHUNKS (inspect for noise):")
    for r in results_sorted[:3]:
        print(f"\n  [{r['file']}] chunk {r['chunk_idx']} — {r['n_entities']} entities")
        print(f"  Text: {all_chunks[results.index(r)]['text'][:120]}...")
        ruler = [(t, l) for t, l, s in r["entities"] if s == "ruler"]
        spacy_items = [(t, l, s) for t, l, s in r["entities"] if s != "ruler"]
        print(f"  Ruler ({len(ruler)}): {[t for t, l in ruler[:10]]}")
        print(f"  SpaCy ({len(spacy_items)}): {[(t, s.split('_')[-1]) for t, l, s in spacy_items[:10]]}")

    # Show 3 low-entity chunks (candidates for L3)
    print("\n\nBOTTOM 3 LOW-ENTITY CHUNKS (L3 candidates):")
    for r in results_sorted[-3:]:
        print(f"\n  [{r['file']}] chunk {r['chunk_idx']} — {r['n_entities']} entities")
        print(f"  Text: {all_chunks[results.index(r)]['text'][:150]}...")
        print(f"  Entities: {[(t, l) for t, l, s in r['entities']]}")

    # Save results
    out = {
        "meta": {"date": "2026-02-24", "task": "2.7", "chunks": n_chunks, "elapsed_s": round(elapsed, 1)},
        "aggregate": {
            "total_entities": total_ents,
            "avg_per_chunk": round(avg_ents, 1),
            "p10": p10, "p50": p50, "p90": p90,
            "min": min(ent_counts), "max": max(ent_counts),
        },
        "by_source": dict(source_totals.most_common()),
        "by_label": dict(label_totals.most_common()),
    }
    out_path = Path(r"c:\googledrive\priv\AI\projekty\LifeCommandCenter\insights\hybrid_extractor_eval.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
