deps = [
    ("torch", "torch"),
    ("spacy", "spacy"),
    ("networkx", "networkx"),
    ("faiss", "faiss"),
    ("sentence_transformers", "sentence_transformers"),
    ("transformers", "transformers"),
    ("anthropic", "anthropic"),
    ("yaml", "yaml"),
    ("numpy", "numpy"),
    ("tqdm", "tqdm"),
]
for name, mod in deps:
    try:
        m = __import__(mod)
        v = getattr(m, "__version__", "ok")
        print(f"  OK  {name}: {v}")
    except ImportError:
        print(f"  MISS {name}")
