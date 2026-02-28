#!/usr/bin/env python3
"""
index_audits.py — Index all LCC audit files with E²GraphRAG pipeline.

Usage:
    python index_audits.py              # Full pipeline (graph + tree)
    python index_audits.py --graph-only # Graph extraction only (no API calls)
    python index_audits.py --tree-only  # Tree building only (uses cached graph)

Output: cache/audits/ folder with graph, index, appearance_count, tree JSON files.
"""
import sys, os, time, json, logging

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.WARNING)

# ── Config ──
AUDIT_DIR = "c:/googledrive/priv/AI/projekty/LifeCommandCenter/insights/audit"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache", "audits")
CHUNK_LENGTH = 300
CHUNK_OVERLAP = 50
MERGE_NUM = 5

os.makedirs(CACHE_DIR, exist_ok=True)


def load_audits():
    """Load all .md audit files, return concatenated text with source markers."""
    files = sorted(f for f in os.listdir(AUDIT_DIR) if f.endswith(".md"))
    texts = []
    for f in files:
        path = os.path.join(AUDIT_DIR, f)
        text = open(path, encoding="utf-8").read()
        # Add source marker for traceability
        texts.append(f"[SOURCE: {f}]\n{text}")
    print(f"Loaded {len(files)} audit files")
    return texts, files


def chunk_by_tokens(texts, tokenizer, length=300, overlap=50):
    """Split list of texts into overlapping chunks by token count."""
    # Concatenate all texts with separator
    full_text = "\n\n---\n\n".join(texts)
    tokens = tokenizer.encode(full_text)
    print(f"Total tokens: {len(tokens)}")

    chunks = []
    step = length - overlap
    start = 0
    while start < len(tokens):
        end = min(start + length, len(tokens))
        chunk_text = tokenizer.decode(tokens[start:end])
        chunks.append(chunk_text)
        if end >= len(tokens):
            break
        start += step
    print(f"Chunks: {len(chunks)} (length={length}, overlap={overlap})")
    return chunks


def run_graph(chunks):
    """Step 1: Graph extraction with LCCExtractor (local, no API)."""
    from extract_graph import extract_graph
    from lcc_extractor import LCCExtractor

    print(f"\n{'='*60}")
    print("STEP 1: Graph Extraction (LCCExtractor)")
    print(f"{'='*60}")

    nlp = LCCExtractor(enable_llm=False)
    t0 = time.time()
    (G, index, appearance_count), time_cost = extract_graph(
        chunks, CACHE_DIR, nlp, use_cache=False, reextract=True
    )
    elapsed = time.time() - t0

    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    print(f"  Unique entities: {len(index)}")
    print(f"  Time: {elapsed:.1f}s")

    # Top entities
    top = sorted(
        [(k, v) for k, v in appearance_count.items()
         if not k.startswith("leaf_") and isinstance(v, int)],
        key=lambda x: x[1], reverse=True
    )[:30]
    print(f"\n  Top 30 entities:")
    for name, count in top:
        print(f"    {count:>3}x {name}")

    return G, index, appearance_count


def run_tree(chunks):
    """Step 2: Tree building with Claude Haiku (API calls)."""
    from lcc_tree_builder import ClaudeTreeBuilder

    print(f"\n{'='*60}")
    print(f"STEP 2: Tree Building (Haiku 4.5, merge_num={MERGE_NUM})")
    print(f"{'='*60}")

    # Delete existing cache to force rebuild
    cache_path = os.path.join(CACHE_DIR, "tree.json")
    if os.path.exists(cache_path):
        os.remove(cache_path)
        print("  Cleared old tree cache")

    builder = ClaudeTreeBuilder()
    t0 = time.time()
    cache = builder.build_tree(chunks, CACHE_DIR, merge_num=MERGE_NUM)
    elapsed = time.time() - t0

    leaves = sum(1 for k in cache if k.startswith("leaf_"))
    summaries = sum(1 for k in cache if k.startswith("summary_"))
    levels = len(set(k.split("_")[1] for k in cache if k.startswith("summary_")))

    print(f"  Leaves: {leaves}")
    print(f"  Summaries: {summaries}")
    print(f"  Levels: {levels}")
    print(f"  API calls: {builder.call_count}")
    print(f"  Input tokens: {builder.total_input_tokens}")
    print(f"  Output tokens: {builder.total_output_tokens}")
    cost_usd = (builder.total_input_tokens * 1.0 + builder.total_output_tokens * 5.0) / 1_000_000
    print(f"  Cost: ${cost_usd:.4f} (~{cost_usd * 4:.2f} PLN)")
    print(f"  Time: {elapsed:.1f}s")

    return cache


if __name__ == "__main__":
    from transformers import AutoTokenizer

    mode = "full"
    if "--graph-only" in sys.argv:
        mode = "graph"
    elif "--tree-only" in sys.argv:
        mode = "tree"

    print(f"index_audits.py — mode: {mode}")
    print(f"Cache: {CACHE_DIR}")

    # Load and chunk
    texts, files = load_audits()
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    chunks = chunk_by_tokens(texts, tokenizer, CHUNK_LENGTH, CHUNK_OVERLAP)

    if mode in ("full", "graph"):
        run_graph(chunks)

    if mode in ("full", "tree"):
        run_tree(chunks)

    print(f"\n{'='*60}")
    print("DONE")
    print(f"{'='*60}")
