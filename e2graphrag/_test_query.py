"""Quick test: load cached graph+tree and run queries."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from extract_graph import SpacyExtractor, load_cache
from query import Retriever

CACHE = os.path.join(os.path.dirname(__file__), "demo_cache")

# Load graph cache
G, index, appearance_count = load_cache(CACHE, "Spacy")
print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# Load tree cache
with open(os.path.join(CACHE, "tree.json"), "r") as f:
    tree = json.load(f)
n_leaves = sum(1 for k in tree if k.startswith("leaf_"))
n_summaries = sum(1 for k in tree if k.startswith("summary_"))
print(f"Tree: {n_leaves} leaves, {n_summaries} summaries")

# Init retriever
nlp = SpacyExtractor("en")
retriever = Retriever(
    tree, G, index, appearance_count, nlp,
    device="cpu", merge_num=3, overlap=50,
    shortest_path_k=4, debug=False, max_chunk_setting=10,
    tokenizer="gpt2", embedder="all-MiniLM-L6-v2",
)

queries = [
    "What is LifeCommandCenter?",
    "What tools does Krzysiek use?",
    "How does entity extraction work?",
]

for q in queries:
    result = retriever.query(q, shortest_path_k=4, max_chunk_setting=10, debug=False)
    rtype = result.get("retrieval_type", "?")
    entities = result.get("entities", [])[:8]
    n_chunks = result.get("len_chunks", 0)
    print(f"\nQ: {q}")
    print(f"  type={rtype}, entities={entities}, chunks={n_chunks}")

print("\nALL QUERIES OK")
