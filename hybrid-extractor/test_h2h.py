"""Head-to-head: qwen3:1.7b vs qwen3:4b on same 4 chunks."""
import sys, time, json, re, requests
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8')
from hybrid_extractor import HybridExtractor

CHUNKS = [
    {"id": "smoke_5", "text": "Krzysiek ma podejrzenie ADHD, przyjmuje escitalopram, planuje dodanie bupropionu. Zdrowie psychiczne wpływa na realizację wszystkich projektów. Raport kliniczny nadciśnienie dotyczy pacjenta 45 lat z zastosowaniem adaptogenów."},
    {"id": "low_kurs9", "text": """06 (aktywne użycie)\n\n**Stack technologiczny:**\n- **PROMPT-GENERATOR-LEKCJI.md** — master prompt z jedną zmienną `DAY = X` | Status: używane\n- **JAK-GENEROWAC-LEKCJE.md** — instrukcja krok po kroku jak użyć prompta | Status: używane\n- **Claude Desktop** — generator lekcji na żądanie | Status: używane"""},
    {"id": "low_bv12", "text": """dukt** — zagregowany cashflow z nałożonymi sezonowościami | Status: omówiony\n- **Multi-location** — osobne cost centers, shared brand (BUSINESS tier)\n- **Revenue Template Engine** — silnik generowania prognoz z wariantami Low/Mid/High\n- **Country Expansion Packs** — gotowe dane rynkowe per kraj (Polska, Niemcy, UK, Czechy)"""},
    {"id": "smoke_15", "text": "AI Grant System uses Qdrant as vector DB, FastAPI for backend, Python 3.11 with Pydantic validation. Claude Opus/Sonnet via API for document analysis. Redis for caching. Beelink SER9 as host machine with Docker Compose orchestration."},
]

for model in ["qwen3:1.7b", "qwen3:4b"]:
    print(f"\n{'='*60}")
    print(f"MODEL: {model}")
    print(f"{'='*60}")
    ext = HybridExtractor(enable_llm=True, llm_model=model, min_entities_threshold=5)
    
    for chunk in CHUNKS:
        t0 = time.time()
        entities = ext.extract(chunk["text"])
        elapsed = time.time() - t0
        
        l3 = [(e.text, e.label) for e in entities if e.source == "llm"]
        stat = ext.stats[-1]
        
        print(f"\n  [{chunk['id']}] {elapsed:.1f}s | L3 called: {stat.layer3_called}")
        if l3:
            print(f"  L3 entities: {l3}")
        else:
            print(f"  L3: not triggered or empty")
    
    print(f"\n  Summary: L3 calls={ext.layer3.calls_made}, avg={ext.layer3.avg_duration_ms}ms")
