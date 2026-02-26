from transformers import AutoTokenizer
t = AutoTokenizer.from_pretrained("gpt2")
print(f"Tokenizer OK: {len(t)} tokens")

from sentence_transformers import SentenceTransformer
m = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
print(f"Embedder OK: dim={m.get_sentence_embedding_dimension()}")
