"""
Quick smoke test for HybridExtractor (Layers 1+2 only, no LLM cost).
Uses 5 chunks from benchmark (task 2.5) to verify basic functionality.
Full evaluation with LLM = task 2.7.
"""
import sys, json
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8')

from hybrid_extractor import HybridExtractor

# 5 representative chunks from benchmark
TEST_CHUNKS = [
    {
        "id": 2, "lang": "MIX",
        "text": "React 19 + Vite 7 — frontend framework, dev server na localhost:5173. Tailwind CSS 4 via Vite plugin do stylowania. Zustand 5 jako state management. Supabase (PostgreSQL) — backend: auth, wait list. Vercel — hosting, auto-deploy z GitHub.",
        "expected": ["React", "Vite", "Tailwind CSS", "Zustand", "Supabase", "PostgreSQL", "Vercel", "GitHub"],
    },
    {
        "id": 5, "lang": "PL",
        "text": "Krzysiek ma podejrzenie ADHD, przyjmuje escitalopram, planuje dodanie bupropionu. Zdrowie psychiczne wpływa na realizację wszystkich projektów. Raport kliniczny nadciśnienie dotyczy pacjenta 45 lat z zastosowaniem adaptogenów.",
        "expected": ["Krzysiek", "ADHD", "escitalopram", "bupropion"],
    },
    {
        "id": 10, "lang": "MIX",
        "text": "LifeCommandCenter łączy Trello jako GUI z Claude jako analiza, przez Postgres jako storage i n8n jako proaktywność. Trzy warstwy: STATE (Trello→FastAPI sync co 60 min→Postgres→MCP), KNOWLEDGE (E²GraphRAG), AGENCY (n8n workflows).",
        "expected": ["LifeCommandCenter", "Trello", "Claude", "Postgres", "n8n", "FastAPI", "MCP", "E²GraphRAG"],
    },
    {
        "id": 15, "lang": "EN",
        "text": "AI Grant System uses Qdrant as vector DB, FastAPI for backend, Python 3.11 with Pydantic validation. Claude Opus/Sonnet via API for document analysis. Redis for caching. Beelink SER9 as host machine with Docker Compose orchestration.",
        "expected": ["AI Grant System", "Qdrant", "FastAPI", "Python 3.11", "Pydantic", "Claude Opus", "Redis", "Beelink SER9", "Docker Compose"],
    },
    {
        "id": 20, "lang": "MIX",
        "text": "Crypto Phantom Rebalancing współdzieli stack z Habit Tracker: PostgreSQL, Telegram, Docker, SER9. PKB (Personal Knowledge Base) korzysta z Obsidian i Meilisearch. n8n MCP Integration zmienia architekturę PKB — nowe MCP nodes z n8n.",
        "expected": ["Crypto Phantom Rebalancing", "Habit Tracker", "PostgreSQL", "Telegram", "Docker", "SER9", "PKB", "Obsidian", "Meilisearch", "n8n", "MCP"],
    },
]

def main():
    print("Loading HybridExtractor (L1+L2 only, no LLM)...")
    extractor = HybridExtractor(enable_llm=False)
    print(f"  Layer 2 patterns: {extractor.layer2.pattern_count}")
    print(f"  Layer 2 entities: {extractor.layer2.entity_count}")
    print()

    total_expected = 0
    total_found = 0

    for chunk in TEST_CHUNKS:
        entities = extractor.extract(chunk["text"])
        entity_texts = {e.text.lower() for e in entities}
        
        # Check recall against expected
        found = 0
        results = []
        for exp in chunk["expected"]:
            matched = any(exp.lower() in et or et in exp.lower() for et in entity_texts)
            found += int(matched)
            status = "✅" if matched else "❌"
            # Find which entity matched
            match_detail = ""
            if matched:
                for e in entities:
                    if exp.lower() in e.text.lower() or e.text.lower() in exp.lower():
                        match_detail = f" → {e.text} [{e.label}] ({e.source})"
                        break
            results.append(f"  {status} {exp}{match_detail}")
        
        total_expected += len(chunk["expected"])
        total_found += found
        recall = found / len(chunk["expected"]) * 100
        
        print(f"--- Chunk {chunk['id']} [{chunk['lang']}] ---")
        print(f"  Entities found: {len(entities)} | Expected recall: {found}/{len(chunk['expected'])} ({recall:.0f}%)")
        for r in results:
            print(r)
        
        # Show L1/L2 breakdown
        l1 = [e for e in entities if e.source.startswith("spacy")]
        l2 = [e for e in entities if e.source == "ruler"]
        print(f"  Breakdown: L1(SpaCy)={len(l1)}, L2(Ruler)={len(l2)}")
        print()

    overall_recall = total_found / total_expected * 100
    print("=" * 60)
    print(f"OVERALL RECALL (L1+L2, no LLM): {total_found}/{total_expected} ({overall_recall:.0f}%)")
    print(f"Summary: {json.dumps(extractor.get_summary(), indent=2)}")

if __name__ == "__main__":
    main()
