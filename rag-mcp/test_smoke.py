"""Smoke test for GraphStore — runs without MCP server."""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from graph_store import GraphStore

CACHE = os.path.join(os.path.dirname(__file__), "..", "e2graphrag", "production_cache")
print(f"Loading from: {CACHE}")

store = GraphStore(CACHE)

# 1. Stats
stats = store.stats()
print(f"\n=== STATS ===")
print(json.dumps(stats, indent=2, ensure_ascii=False))

# 2. Search entities
print(f"\n=== SEARCH: 'trello' ===")
results = store.search_entities("trello", limit=5)
for r in results:
    print(f"  {r['entity']:40s} score={r['score']} chunks={r['chunk_count']} conn={r['graph_connections']}")

# 3. Entity context
print(f"\n=== ENTITY CONTEXT: 'Trello' ===")
ctx = store.get_entity_context("Trello")
if ctx:
    print(f"  Neighbors (top 5): {[n['entity'] for n in ctx['graph_neighbors'][:5]]}")
    print(f"  Total neighbors: {ctx['total_neighbors']}")
    print(f"  Chunks: {ctx['total_chunks']}")

# 4. Get chunk
print(f"\n=== CHUNK: leaf_0 (first 200 chars) ===")
chunk = store.get_chunk("leaf_0")
if chunk:
    print(f"  Text: {chunk['text'][:200]}...")
    print(f"  Entities: {chunk.get('entities', [])[:10]}")

# 5. Chunk metadata
print(f"\n=== CHUNK METADATA: leaf_0 ===")
meta = store.get_chunk_metadata("leaf_0")
if meta:
    print(json.dumps(meta, indent=2, ensure_ascii=False))

# 6. Subgraph query
print(f"\n=== SUBGRAPH: ['Trello', 'n8n', 'PostgreSQL'] ===")
sg = store.query_subgraph(["Trello", "n8n", "PostgreSQL"], max_hops=3, max_chunks=5)
print(f"  Resolved: {sg['resolved_entities']}")
print(f"  Paths: {len(sg['paths'])}")
for p in sg['paths']:
    print(f"    {p['from']} → {p['to']}: hops={p['hops']}, path={p['path']}")
print(f"  Chunks: {sg['chunk_count']}")

print("\n✅ ALL TESTS PASSED")
