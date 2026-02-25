"""Test Layer 3 (Ollama Qwen3:8B) on chunks where L1+L2 fail."""
import sys, time
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8')
from hybrid_extractor import HybridExtractor

# Chunks where L1+L2 had issues
TEST_CHUNKS = [
    {
        "id": "smoke_5",
        "text": "Krzysiek ma podejrzenie ADHD, przyjmuje escitalopram, planuje dodanie bupropionu. Zdrowie psychiczne wpływa na realizację wszystkich projektów. Raport kliniczny nadciśnienie dotyczy pacjenta 45 lat z zastosowaniem adaptogenów.",
        "note": "L1+L2 missed: bupropion (declined form 'bupropionu')",
    },
    {
        "id": "smoke_15",
        "text": "AI Grant System uses Qdrant as vector DB, FastAPI for backend, Python 3.11 with Pydantic validation. Claude Opus/Sonnet via API for document analysis. Redis for caching. Beelink SER9 as host machine with Docker Compose orchestration.",
        "note": "L1+L2 missed: Python 3.11",
    },
    {
        "id": "low_kurs9",
        "text": """06 (aktywne użycie)

**Stack technologiczny:**
- **PROMPT-GENERATOR-LEKCJI.md** — master prompt z jedną zmienną `DAY = X` | Status: używane
- **JAK-GENEROWAC-LEKCJE.md** — instrukcja krok po kroku jak użyć prompta | Status: używane
- **Claude Desktop** — generator lekcji na żądanie | Status: używane""",
        "note": "L1+L2 found only 1 entity (Desktop Commander)",
    },
    {
        "id": "low_bv12",
        "text": """dukt** — zagregowany cashflow z nałożonymi sezonowościami | Status: omówiony
- **Multi-location** — osobne cost centers, shared brand (BUSINESS tier) 
- **Revenue Template Engine** — silnik generowania prognoz z wariantami Low/Mid/High
- **Country Expansion Packs** — gotowe dane rynkowe per kraj (Polska, Niemcy, UK, Czechy)""",
        "note": "L1+L2 found only 1 entity (Angielska)",
    },
]

def main():
    print("Loading HybridExtractor with L3 (Ollama Qwen3:8B)...")
    ext = HybridExtractor(enable_llm=True, llm_model="qwen3:1.7b", min_entities_threshold=5)
    print()

    for chunk in TEST_CHUNKS:
        print(f"--- {chunk['id']} ---")
        print(f"  Note: {chunk['note']}")
        t0 = time.time()
        entities = ext.extract(chunk["text"])
        elapsed = time.time() - t0
        
        by_source = {}
        for e in entities:
            by_source.setdefault(e.source, []).append(e)
        
        print(f"  Total: {len(entities)} entities ({elapsed:.1f}s)")
        for src, ents in sorted(by_source.items()):
            print(f"  {src}: {[(e.text, e.label) for e in ents]}")
        
        # Check if L3 was called
        stat = ext.stats[-1]
        if stat.layer3_called:
            print(f"  ✅ L3 CALLED — added {stat.layer3_count} entities")
        else:
            print(f"  ⬜ L3 not triggered (threshold={ext.threshold}, L1+L2={stat.layer1_count + stat.layer2_count})")
        print()

    summary = ext.get_summary()
    print(f"Summary: L3 calls={summary['layer3_calls']}, avg LLM time={summary['llm_avg_ms']}ms")

if __name__ == "__main__":
    main()
