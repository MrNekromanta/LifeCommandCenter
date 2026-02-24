"""Diagnostic: what's generating noise in L1 extraction?"""
import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8')
from hybrid_extractor import HybridExtractor

CHUNK = "LifeCommandCenter łączy Trello jako GUI z Claude jako analiza, przez Postgres jako storage i n8n jako proaktywność. Trzy warstwy: STATE (Trello→FastAPI sync co 60 min→Postgres→MCP), KNOWLEDGE (E²GraphRAG), AGENCY (n8n workflows)."

ext = HybridExtractor(enable_llm=False)
entities = ext.extract(CHUNK)

by_source = {}
for e in sorted(entities, key=lambda x: x.source):
    by_source.setdefault(e.source, []).append(e)

for src, ents in by_source.items():
    print(f"\n=== {src} ({len(ents)}) ===")
    for e in sorted(ents, key=lambda x: x.text):
        print(f"  {e.text:30s} [{e.label}]")
