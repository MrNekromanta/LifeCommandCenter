"""Retest qwen3:1.7b with noise filter on L3 output."""
import sys, time
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8')
from hybrid_extractor import HybridExtractor

CHUNKS = [
    {"id": "smoke_5", "text": "Krzysiek ma podejrzenie ADHD, przyjmuje escitalopram, planuje dodanie bupropionu. Zdrowie psychiczne wpływa na realizację wszystkich projektów. Raport kliniczny nadciśnienie dotyczy pacjenta 45 lat z zastosowaniem adaptogenów."},
    {"id": "low_kurs9", "text": "06 (aktywne użycie)\n\nStack technologiczny:\nPROMPT-GENERATOR-LEKCJI.md - master prompt z jedną zmienną DAY = X | Status: używane\nJAK-GENEROWAC-LEKCJE.md - instrukcja krok po kroku jak użyć prompta | Status: używane\nClaude Desktop - generator lekcji na żądanie | Status: używane"},
    {"id": "low_bv12", "text": "dukt - zagregowany cashflow z nałożonymi sezonowościami | Status: omówiony\nMulti-location - osobne cost centers, shared brand (BUSINESS tier)\nRevenue Template Engine - silnik generowania prognoz z wariantami Low/Mid/High\nCountry Expansion Packs - gotowe dane rynkowe per kraj (Polska, Niemcy, UK, Czechy)"},
]

ext = HybridExtractor(enable_llm=True, llm_model="qwen3:1.7b", min_entities_threshold=5)

for chunk in CHUNKS:
    t0 = time.time()
    entities = ext.extract(chunk["text"])
    elapsed = time.time() - t0
    l3 = [(e.text, e.label) for e in entities if e.source == "llm"]
    other = [(e.text, e.label, e.source) for e in entities if e.source != "llm"]
    stat = ext.stats[-1]
    print(f"\n[{chunk['id']}] {elapsed:.1f}s | L3 called={stat.layer3_called}")
    print(f"  L1+L2: {[(t,l) for t,l,s in other]}")
    if l3:
        print(f"  L3 added: {l3}")
    else:
        print(f"  L3: empty")
