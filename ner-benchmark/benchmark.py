"""
Task 2.5: SpaCy NER Benchmark on Krzysiek's audit data
Models: pl_core_news_lg (Polish), en_core_web_lg (English)
Goal: Baseline F1 for standard NER + gap analysis for domain entities

20 chunks from 9 audit files, mix of:
- Pure Polish (PL)
- Pure English (EN) 
- Mixed PL/EN (MIX) — the most common in actual conversations
"""
import json, sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# 20 TEST CHUNKS with manual annotations
# Each chunk has:
#   text: actual text from audits
#   lang: PL / EN / MIX
#   source: audit file
#   expected_entities: manually annotated entities we WANT found
#     - standard: entities SpaCy NER should catch (PER, ORG, LOC, DATE, etc.)
#     - domain: entities only EntityRuler/LLM can catch (PROJECT, TOOL, MODEL, etc.)
# ============================================================

CHUNKS = [
    # --- CHUNK 1: PL, Crypto decisions ---
    {
        "id": 1, "lang": "MIX", "source": "crypto-rebalancing",
        "text": "Wybór aktywa do rebalancingu: ETH/USDC na Arbitrum. ETH jest mean-reverting, wysoka volatility (~60% annualized) generuje rebalancing premium 15-30%, Arbitrum ma niskie fees ($0.10-0.50), głęboką płynność ($19.2B TVL). TRX odrzucone bo HODL lepsze o 68%.",
        "expected": {
            "standard": [
                {"text": "Arbitrum", "label": "ORG_OR_PRODUCT"},
            ],
            "domain": [
                {"text": "ETH", "label": "PRODUCT"}, {"text": "USDC", "label": "PRODUCT"},
                {"text": "Arbitrum", "label": "PLATFORM"}, {"text": "TRX", "label": "PRODUCT"},
                {"text": "rebalancing", "label": "CONCEPT"}, {"text": "mean-reverting", "label": "CONCEPT"},
            ]
        }
    },
    # --- CHUNK 2: MIX, BiznesValidator stack ---
    {
        "id": 2, "lang": "MIX", "source": "biznesvalidator",
        "text": "React 19 + Vite 7 — frontend framework, dev server na localhost:5173. Tailwind CSS 4 via Vite plugin do stylowania. Zustand 5 jako state management. Supabase (PostgreSQL) — backend: auth, wait list. Vercel — hosting, auto-deploy z GitHub.",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "React", "label": "TOOL"}, {"text": "Vite", "label": "TOOL"},
                {"text": "Tailwind CSS", "label": "TOOL"}, {"text": "Zustand", "label": "TOOL"},
                {"text": "Supabase", "label": "TOOL"}, {"text": "PostgreSQL", "label": "TOOL"},
                {"text": "Vercel", "label": "TOOL"}, {"text": "GitHub", "label": "TOOL"},
            ]
        }
    },
    # --- CHUNK 3: PL, Liofilizacja regulations ---
    {
        "id": 3, "lang": "PL", "source": "biznesvalidator",
        "text": "Liofilizacja wymaga pełnego zatwierdzenia GHP/GMP przez Sanepid. Koszt liofilizatora HarvestRight to około 26 000 PLN. Planowane produkty: mango, truskawki, rzęsa wodna jako superfood. Rynek docelowy: Polska na start, potem EU.",
        "expected": {
            "standard": [
                {"text": "Sanepid", "label": "ORG"},
                {"text": "Polska", "label": "LOC"},
            ],
            "domain": [
                {"text": "Liofilizacja", "label": "PROJECT"}, {"text": "GHP/GMP", "label": "CONCEPT"},
                {"text": "HarvestRight", "label": "HARDWARE"}, {"text": "rzęsa wodna", "label": "PRODUCT"},
            ]
        }
    },
    # --- CHUNK 4: MIX, Docker + monitoring ---
    {
        "id": 4, "lang": "MIX", "source": "crypto-rebalancing",
        "text": "Docker Compose orchestruje kontenery: PostgreSQL, n8n, Grafana. Telegram Bot wysyła alerty soft/hard/confirmation plus komendy /status, /balance, /history. Web3.py komunikuje się z Arbitrum blockchain przez Alchemy RPC provider.",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "Docker Compose", "label": "TOOL"}, {"text": "PostgreSQL", "label": "TOOL"},
                {"text": "n8n", "label": "TOOL"}, {"text": "Grafana", "label": "TOOL"},
                {"text": "Telegram Bot", "label": "TOOL"}, {"text": "Web3.py", "label": "TOOL"},
                {"text": "Arbitrum", "label": "PLATFORM"}, {"text": "Alchemy", "label": "PLATFORM"},
            ]
        }
    },
    # --- CHUNK 5: PL, ADHD + health ---
    {
        "id": 5, "lang": "PL", "source": "main-chat",
        "text": "Krzysiek ma podejrzenie ADHD, przyjmuje escitalopram, planuje dodanie bupropionu. Zdrowie psychiczne wpływa na realizację wszystkich projektów. Raport kliniczny nadciśnienie dotyczy pacjenta 45 lat z zastosowaniem adaptogenów.",
        "expected": {
            "standard": [
                {"text": "Krzysiek", "label": "PER"},
            ],
            "domain": [
                {"text": "ADHD", "label": "CONCEPT"}, {"text": "escitalopram", "label": "CONCEPT"},
                {"text": "bupropion", "label": "CONCEPT"},
            ]
        }
    },
    # --- CHUNK 6: MIX, E²GraphRAG architecture ---
    {
        "id": 6, "lang": "MIX", "source": "main-chat",
        "text": "E²GraphRAG daje summary tree (hierarchiczne streszczenia), entity graph (relacje między bytami) i adaptive retrieval. Implementacja: SpaCy HerBERT jako warstwa 1, EntityRuler jako warstwa 2, Claude Haiku jako warstwa 3 LLM micro-extraction.",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "E²GraphRAG", "label": "TOOL"}, {"text": "summary tree", "label": "CONCEPT"},
                {"text": "entity graph", "label": "CONCEPT"}, {"text": "adaptive retrieval", "label": "CONCEPT"},
                {"text": "SpaCy", "label": "TOOL"}, {"text": "HerBERT", "label": "TOOL"},
                {"text": "EntityRuler", "label": "TOOL"}, {"text": "Claude Haiku", "label": "MODEL"},
            ]
        }
    },
    # --- CHUNK 7: PL, Allmedica procurement ---
    {
        "id": 7, "lang": "PL", "source": "main-chat",
        "text": "Unieważnienie SZAFLARY/1/FENG/2025 z powodu braku ofert. Wezwanie firmy QUANTARA do wyjaśnień rażąco niskiej ceny w trybie Prawa zamówień publicznych. Wybór oferty Winroof na okna dachowe za 32 000 PLN brutto.",
        "expected": {
            "standard": [
                {"text": "QUANTARA", "label": "ORG"},
                {"text": "Winroof", "label": "ORG"},
                {"text": "SZAFLARY", "label": "LOC_OR_ID"},
            ],
            "domain": [
                {"text": "FENG", "label": "PROJECT"}, {"text": "rażąco niska cena", "label": "CONCEPT"},
                {"text": "Prawo zamówień publicznych", "label": "CONCEPT"},
            ]
        }
    },
    # --- CHUNK 8: EN, Wiki RAG architecture ---
    {
        "id": 8, "lang": "EN", "source": "wiki-rag",
        "text": "Wiki RAG Baremetal uses Meilisearch as vector DB, Nginx as reverse proxy, Docker for containerization. Llama 3.1 70B running on LocalAI. Embedding model: BGE-M3 from BAAI. Confluence as source of 20k wiki pages.",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "Wiki RAG Baremetal", "label": "PROJECT"}, {"text": "Meilisearch", "label": "TOOL"},
                {"text": "Nginx", "label": "TOOL"}, {"text": "Docker", "label": "TOOL"},
                {"text": "Llama 3.1 70B", "label": "MODEL"}, {"text": "LocalAI", "label": "TOOL"},
                {"text": "BGE-M3", "label": "MODEL"}, {"text": "BAAI", "label": "ORG"},
                {"text": "Confluence", "label": "TOOL"},
            ]
        }
    },
    # --- CHUNK 9: PL, Propolis biomedical ---
    {
        "id": 9, "lang": "PL", "source": "produkty-pszczele",
        "text": "Propolis blokuje szlak NF-κB przez substancję CAPE. TGF-β wzrasta 2.8x przy zastosowaniu ekstraktu propolisowego. VEGF wspiera angiogenezę w procesie gojenia ran. Mleczko pszczele zawiera kwas 10-HDA blokujący NF-κB.",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "NF-κB", "label": "BIOMEDICAL"}, {"text": "CAPE", "label": "BIOMEDICAL"},
                {"text": "TGF-β", "label": "BIOMEDICAL"}, {"text": "VEGF", "label": "BIOMEDICAL"},
                {"text": "10-HDA", "label": "BIOMEDICAL"}, {"text": "propolis", "label": "BIOMEDICAL"},
                {"text": "mleczko pszczele", "label": "BIOMEDICAL"},
            ]
        }
    },
    # --- CHUNK 10: MIX, LifeCommandCenter architecture ---
    {
        "id": 10, "lang": "MIX", "source": "main-chat",
        "text": "LifeCommandCenter łączy Trello jako GUI z Claude jako analiza, przez Postgres jako storage i n8n jako proaktywność. Trzy warstwy: STATE (Trello→FastAPI sync co 60 min→Postgres→MCP), KNOWLEDGE (E²GraphRAG), AGENCY (n8n workflows).",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "LifeCommandCenter", "label": "PROJECT"}, {"text": "Trello", "label": "TOOL"},
                {"text": "Claude", "label": "MODEL"}, {"text": "Postgres", "label": "TOOL"},
                {"text": "n8n", "label": "TOOL"}, {"text": "FastAPI", "label": "TOOL"},
                {"text": "MCP", "label": "TOOL"}, {"text": "E²GraphRAG", "label": "TOOL"},
            ]
        }
    },
    # --- CHUNK 11: MIX, Ollama models ---
    {
        "id": 11, "lang": "MIX", "source": "crypto-rebalancing",
        "text": "Ollama jako local LLM runtime na Beelink SER9. DeepSeek-R1:7B odrzucony — jakość analiz w polskim niezadowalająca. Qwen3:8B wybrany jako replacement, lepsza obsługa wielojęzyczna. Na przyszłość DeepSeek-R1:14B z RTX 3090.",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "Ollama", "label": "TOOL"}, {"text": "Beelink SER9", "label": "HARDWARE"},
                {"text": "DeepSeek-R1:7B", "label": "MODEL"}, {"text": "Qwen3:8B", "label": "MODEL"},
                {"text": "DeepSeek-R1:14B", "label": "MODEL"}, {"text": "RTX 3090", "label": "HARDWARE"},
            ]
        }
    },
    # --- CHUNK 12: PL, Food forest + energy ---
    {
        "id": 12, "lang": "PL", "source": "main-chat",
        "text": "Food forest na 36 arach w Krzeszowicach jako źródło surowców do liofilizacji. Termomodernizacja domu umożliwia fotowoltaikę — sens ekonomiczny PV zależy od izolacji. Baterie LiFePO4 wspólne z projektem Meshtastic LoRa mesh.",
        "expected": {
            "standard": [
                {"text": "Krzeszowice", "label": "LOC"},
            ],
            "domain": [
                {"text": "Food forest", "label": "PROJECT"}, {"text": "liofilizacja", "label": "PROJECT"},
                {"text": "Termomodernizacja", "label": "PROJECT"}, {"text": "fotowoltaika", "label": "PROJECT"},
                {"text": "LiFePO4", "label": "HARDWARE"}, {"text": "Meshtastic", "label": "PROJECT"},
            ]
        }
    },
    # --- CHUNK 13: MIX, Cloudflare + security ---
    {
        "id": 13, "lang": "MIX", "source": "biznesvalidator",
        "text": "Wdrożyliśmy Cloudflare Turnstile na landing page z Zustand store i honeypot fields jako dodatkowa warstwa antyspamowa. Stripe + Przelewy24 planowane na milestone M7. Claude API przez backend proxy — nigdy bezpośrednio z frontendu.",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "Cloudflare Turnstile", "label": "TOOL"}, {"text": "Zustand", "label": "TOOL"},
                {"text": "Stripe", "label": "TOOL"}, {"text": "Przelewy24", "label": "TOOL"},
                {"text": "Claude API", "label": "MODEL"},
            ]
        }
    },
    # --- CHUNK 14: PL, Kurs PM/PO ---
    {
        "id": 14, "lang": "PL", "source": "kurs-pm-po",
        "text": "Kurs PM/PO oparty na Scrum Guide 2020, książkach Cagana 'Inspired' i Torres 'Continuous Discovery Habits'. Moduł 1 obejmuje 12 lekcji, Moduł 2 skupia się na Discovery. System generowania lekcji przez Claude z Desktop Commander do zapisu plików.",
        "expected": {
            "standard": [
                {"text": "Cagan", "label": "PER"},
                {"text": "Torres", "label": "PER"},
            ],
            "domain": [
                {"text": "Kurs PM/PO", "label": "PROJECT"}, {"text": "Scrum Guide", "label": "CONCEPT"},
                {"text": "Claude", "label": "MODEL"}, {"text": "Desktop Commander", "label": "TOOL"},
            ]
        }
    },
    # --- CHUNK 15: EN, Grant system ---
    {
        "id": 15, "lang": "EN", "source": "automatyzacja-wnioskow",
        "text": "AI Grant System uses Qdrant as vector DB, FastAPI for backend, Python 3.11 with Pydantic validation. Claude Opus/Sonnet via API for document analysis. Redis for caching. Beelink SER9 as host machine with Docker Compose orchestration.",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "AI Grant System", "label": "PROJECT"}, {"text": "Qdrant", "label": "TOOL"},
                {"text": "FastAPI", "label": "TOOL"}, {"text": "Python 3.11", "label": "TOOL"},
                {"text": "Pydantic", "label": "TOOL"}, {"text": "Claude Opus", "label": "MODEL"},
                {"text": "Redis", "label": "TOOL"}, {"text": "Beelink SER9", "label": "HARDWARE"},
                {"text": "Docker Compose", "label": "TOOL"},
            ]
        }
    },
    # --- CHUNK 16: PL, cross-project relations ---
    {
        "id": 16, "lang": "PL", "source": "main-chat",
        "text": "BiznesValidator ewoluował w projekt Liofilizacja — narzędzia do walidacji stały się samodzielnym SaaS. Doświadczenie z Allmedica w compliance i fintech wpływa na decyzje o privacy i security. Crypto Rebalancer współdzieli Postgres z LifeCommandCenter na SER9.",
        "expected": {
            "standard": [
                {"text": "Allmedica", "label": "ORG"},
            ],
            "domain": [
                {"text": "BiznesValidator", "label": "PROJECT"}, {"text": "Liofilizacja", "label": "PROJECT"},
                {"text": "Crypto Rebalancer", "label": "PROJECT"}, {"text": "LifeCommandCenter", "label": "PROJECT"},
                {"text": "Postgres", "label": "TOOL"}, {"text": "SER9", "label": "HARDWARE"},
            ]
        }
    },
    # --- CHUNK 17: MIX, Raspberry Pi education ---
    {
        "id": 17, "lang": "MIX", "source": "main-chat",
        "text": "12-miesięczny plan nauki komputera dla Jasia (4 lata) z Raspberry Pi 4 8GB. 18 projektów edukacyjnych zaplanowanych. Raspberry Pi współdzieli stack z Home Assistant — Linux, GPIO, Python. Smart Home integruje n8n i MCP jako narzędzia automation.",
        "expected": {
            "standard": [
                {"text": "Jasio", "label": "PER"},
            ],
            "domain": [
                {"text": "Raspberry Pi 4", "label": "HARDWARE"}, {"text": "Home Assistant", "label": "TOOL"},
                {"text": "n8n", "label": "TOOL"}, {"text": "MCP", "label": "TOOL"},
                {"text": "Smart Home", "label": "PROJECT"}, {"text": "Python", "label": "TOOL"},
            ]
        }
    },
    # --- CHUNK 18: EN, DD AI System ---
    {
        "id": 18, "lang": "EN", "source": "automatyzacja-wnioskow",
        "text": "DD AI System integrates MPZP data from ekw.ms.gov.pl and Krajowa Integracja MPZP. Uses GPT-4o Vision for document analysis, Streamlit for UI, Cloudflare Tunnel for secure access. Shares infrastructure with AI Grant System on SER9.",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "DD AI System", "label": "PROJECT"}, {"text": "GPT-4o", "label": "MODEL"},
                {"text": "Streamlit", "label": "TOOL"}, {"text": "Cloudflare Tunnel", "label": "TOOL"},
                {"text": "AI Grant System", "label": "PROJECT"}, {"text": "SER9", "label": "HARDWARE"},
            ]
        }
    },
    # --- CHUNK 19: PL, Mitos + Digital Memorial ---
    {
        "id": 19, "lang": "PL", "source": "main-chat",
        "text": "Projekt Mitos Translation wymaga Whisper large-v3 na GPU do transkrypcji audio. ElevenLabs do klonowania głosu, wspólna technologia z Digital Memorial. Oba projekty zależą od RTX 3090 — bez GPU inference trwa zbyt długo.",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "Mitos Translation", "label": "PROJECT"}, {"text": "Whisper", "label": "TOOL"},
                {"text": "ElevenLabs", "label": "TOOL"}, {"text": "Digital Memorial", "label": "PROJECT"},
                {"text": "RTX 3090", "label": "HARDWARE"},
            ]
        }
    },
    # --- CHUNK 20: MIX, n8n + MCP integration ---
    {
        "id": 20, "lang": "MIX", "source": "projekt-claude",
        "text": "Crypto Phantom Rebalancing współdzieli stack z Habit Tracker: PostgreSQL, Telegram, Docker, SER9. PKB (Personal Knowledge Base) korzysta z Obsidian i Meilisearch. n8n MCP Integration zmienia architekturę PKB — nowe MCP nodes z n8n.",
        "expected": {
            "standard": [],
            "domain": [
                {"text": "Crypto Phantom Rebalancing", "label": "PROJECT"},
                {"text": "Habit Tracker", "label": "PROJECT"}, {"text": "PostgreSQL", "label": "TOOL"},
                {"text": "Telegram", "label": "TOOL"}, {"text": "Docker", "label": "TOOL"},
                {"text": "SER9", "label": "HARDWARE"}, {"text": "PKB", "label": "PROJECT"},
                {"text": "Obsidian", "label": "TOOL"}, {"text": "Meilisearch", "label": "TOOL"},
                {"text": "n8n", "label": "TOOL"}, {"text": "MCP", "label": "TOOL"},
            ]
        }
    },
]

# ============================================================
# BENCHMARK ENGINE
# ============================================================

import spacy

print("Loading models...")
nlp_pl = spacy.load("pl_core_news_lg")
nlp_en = spacy.load("en_core_web_lg")
print(f"  pl_core_news_lg: {nlp_pl.meta['name']} v{nlp_pl.meta['version']}")
print(f"  en_core_web_lg: {nlp_en.meta['name']} v{nlp_en.meta['version']}")
print(f"  PL NER labels: {nlp_pl.get_pipe('ner').labels}")
print(f"  EN NER labels: {nlp_en.get_pipe('ner').labels}")
print()

def run_spacy_ner(text, lang):
    """Run SpaCy NER, return found entities."""
    if lang == "EN":
        doc = nlp_en(text)
    elif lang == "PL":
        doc = nlp_pl(text)
    else:  # MIX — run both and merge
        doc_pl = nlp_pl(text)
        doc_en = nlp_en(text)
        # Merge: prefer PL entities, add EN entities that don't overlap
        ents_pl = [(e.text, e.label_, e.start_char, e.end_char) for e in doc_pl.ents]
        ents_en = [(e.text, e.label_, e.start_char, e.end_char) for e in doc_en.ents]
        # Use PL as base, add non-overlapping EN
        pl_spans = set()
        for _, _, start, end in ents_pl:
            pl_spans.update(range(start, end))
        merged = list(ents_pl)
        for text_e, label, start, end in ents_en:
            if not any(i in pl_spans for i in range(start, end)):
                merged.append((text_e, label, start, end))
        return merged
    
    return [(e.text, e.label_, e.start_char, e.end_char) for e in doc.ents]

def extract_nouns(text, lang):
    """Extract nouns (which E²GraphRAG uses for entity graph)."""
    if lang == "EN":
        doc = nlp_en(text)
    elif lang == "PL":
        doc = nlp_pl(text)
    else:  # MIX — use both
        doc_pl = nlp_pl(text)
        doc_en = nlp_en(text)
        nouns = set()
        for token in doc_pl:
            if token.pos_ in ("NOUN", "PROPN") and len(token.text) > 2:
                nouns.add(token.text)
        for token in doc_en:
            if token.pos_ in ("NOUN", "PROPN") and len(token.text) > 2:
                nouns.add(token.text)
        # Only EN supports noun_chunks
        chunks = set()
        for chunk in doc_en.noun_chunks:
            if len(chunk.text) > 2:
                chunks.add(chunk.text)
        return nouns, chunks
    
    nouns = set()
    for token in doc:
        if token.pos_ in ("NOUN", "PROPN") and len(token.text) > 2:
            nouns.add(token.text)
    # noun_chunks only for EN
    chunks = set()
    if lang == "EN":
        for chunk in doc.noun_chunks:
            if len(chunk.text) > 2:
                chunks.add(chunk.text)
    return nouns, chunks

def entity_match(found_text, expected_text):
    """Fuzzy match: found contains expected or vice versa."""
    f = found_text.lower().strip()
    e = expected_text.lower().strip()
    return f == e or f in e or e in f

# ============================================================
# RUN BENCHMARK
# ============================================================

print("=" * 70)
print("BENCHMARK: SpaCy NER on LifeCommandCenter audit data")
print("=" * 70)
print()

# Aggregated metrics
total_standard_expected = 0
total_standard_found = 0
total_standard_correct = 0
total_domain_expected = 0
total_domain_found_by_ner = 0
total_domain_found_by_nouns = 0

all_results = []

for chunk in CHUNKS:
    cid = chunk["id"]
    text = chunk["text"]
    lang = chunk["lang"]
    expected_std = chunk["expected"]["standard"]
    expected_dom = chunk["expected"]["domain"]
    
    # Run NER
    ner_results = run_spacy_ner(text, lang)
    
    # Run noun extraction
    nouns, noun_chunks = extract_nouns(text, lang)
    
    # --- Evaluate STANDARD entities ---
    std_found = 0
    std_matches = []
    for exp in expected_std:
        matched = False
        for found_text, found_label, _, _ in ner_results:
            if entity_match(found_text, exp["text"]):
                matched = True
                std_matches.append(f"✅ {exp['text']} → {found_text} [{found_label}]")
                break
        if not matched:
            std_matches.append(f"❌ {exp['text']} [{exp['label']}] — NOT FOUND")
        std_found += int(matched)
    
    # --- Evaluate DOMAIN entities (NER) ---
    dom_ner_found = 0
    dom_matches = []
    for exp in expected_dom:
        matched = False
        for found_text, found_label, _, _ in ner_results:
            if entity_match(found_text, exp["text"]):
                matched = True
                dom_matches.append(f"✅ NER: {exp['text']} → {found_text} [{found_label}]")
                break
        if not matched:
            # Check nouns
            noun_match = False
            for n in nouns | noun_chunks:
                if entity_match(n, exp["text"]):
                    noun_match = True
                    dom_matches.append(f"🔶 NOUN: {exp['text']} → {n}")
                    break
            if not noun_match:
                dom_matches.append(f"❌ MISS: {exp['text']} [{exp['label']}]")
        dom_ner_found += int(matched)
    
    # Count domain entities found by nouns (including those found by NER)
    dom_noun_found = 0
    for exp in expected_dom:
        for n in nouns | noun_chunks:
            if entity_match(n, exp["text"]):
                dom_noun_found += 1
                break
    
    total_standard_expected += len(expected_std)
    total_standard_found += std_found
    total_domain_expected += len(expected_dom)
    total_domain_found_by_ner += dom_ner_found
    total_domain_found_by_nouns += dom_noun_found
    
    result = {
        "id": cid, "lang": lang,
        "ner_entities": [(t, l) for t, l, _, _ in ner_results],
        "std_recall": std_found / max(len(expected_std), 1),
        "dom_ner_recall": dom_ner_found / max(len(expected_dom), 1),
        "dom_noun_recall": dom_noun_found / max(len(expected_dom), 1),
        "std_matches": std_matches,
        "dom_matches": dom_matches,
        "nouns": sorted(nouns),
        "noun_chunks": sorted(noun_chunks),
    }
    all_results.append(result)
    
    # Print per-chunk
    print(f"--- Chunk {cid} [{lang}] ({chunk['source']}) ---")
    print(f"  Text: {text[:80]}...")
    print(f"  SpaCy NER found: {[(t, l) for t, l in result['ner_entities']]}")
    if std_matches:
        print(f"  Standard entities ({std_found}/{len(expected_std)}):")
        for m in std_matches:
            print(f"    {m}")
    print(f"  Domain entities — NER: {dom_ner_found}/{len(expected_dom)}, Nouns: {dom_noun_found}/{len(expected_dom)}")
    for m in dom_matches:
        print(f"    {m}")
    print()

# ============================================================
# AGGREGATE RESULTS
# ============================================================

print("=" * 70)
print("AGGREGATE RESULTS")
print("=" * 70)
print()

std_recall = total_standard_found / max(total_standard_expected, 1) * 100
dom_ner_recall = total_domain_found_by_ner / max(total_domain_expected, 1) * 100
dom_noun_recall = total_domain_found_by_nouns / max(total_domain_expected, 1) * 100

print(f"STANDARD NER ENTITIES (PER, ORG, LOC, DATE):")
print(f"  Expected: {total_standard_expected}")
print(f"  Found:    {total_standard_found}")
print(f"  Recall:   {std_recall:.1f}%")
print()
print(f"DOMAIN ENTITIES (PROJECT, TOOL, MODEL, HARDWARE, CONCEPT, etc.):")
print(f"  Expected:       {total_domain_expected}")
print(f"  Found by NER:   {total_domain_found_by_ner} ({dom_ner_recall:.1f}%)")
print(f"  Found by Nouns: {total_domain_found_by_nouns} ({dom_noun_recall:.1f}%)")
print(f"  Gap (NER miss):  {total_domain_expected - total_domain_found_by_ner} entities ({100 - dom_ner_recall:.1f}%)")
print()

# Per-language breakdown
for lang_filter in ["PL", "EN", "MIX"]:
    lang_chunks = [r for r in all_results if CHUNKS[r["id"]-1]["lang"] == lang_filter]
    if not lang_chunks:
        continue
    lang_dom_exp = sum(len(CHUNKS[r["id"]-1]["expected"]["domain"]) for r in lang_chunks)
    lang_dom_ner = sum(int(r["dom_ner_recall"] * len(CHUNKS[r["id"]-1]["expected"]["domain"])) for r in lang_chunks)
    lang_dom_noun = sum(int(r["dom_noun_recall"] * len(CHUNKS[r["id"]-1]["expected"]["domain"])) for r in lang_chunks)
    print(f"  {lang_filter}: NER {lang_dom_ner}/{lang_dom_exp} ({lang_dom_ner/max(lang_dom_exp,1)*100:.0f}%), "
          f"Nouns {lang_dom_noun}/{lang_dom_exp} ({lang_dom_noun/max(lang_dom_exp,1)*100:.0f}%)")

print()
print("CONCLUSION:")
print(f"  SpaCy NER alone catches ~{dom_ner_recall:.0f}% of domain entities")
print(f"  Noun extraction adds coverage to ~{dom_noun_recall:.0f}%")
print(f"  Remaining ~{100 - dom_noun_recall:.0f}% requires EntityRuler + LLM layers")
print()

# ============================================================
# SAVE RESULTS
# ============================================================

output = {
    "meta": {
        "date": "2026-02-24",
        "task": "2.5",
        "models": {
            "pl": f"{nlp_pl.meta['name']} v{nlp_pl.meta['version']}",
            "en": f"{nlp_en.meta['name']} v{nlp_en.meta['version']}"
        },
        "chunks": len(CHUNKS),
        "total_standard_expected": total_standard_expected,
        "total_domain_expected": total_domain_expected,
    },
    "results": {
        "standard_ner_recall": round(std_recall, 1),
        "domain_ner_recall": round(dom_ner_recall, 1),
        "domain_noun_recall": round(dom_noun_recall, 1),
        "domain_gap_percent": round(100 - dom_noun_recall, 1),
    },
    "per_chunk": [{
        "id": r["id"],
        "lang": r["lang"],
        "ner_entities": r["ner_entities"],
        "std_recall": round(r["std_recall"] * 100, 1),
        "dom_ner_recall": round(r["dom_ner_recall"] * 100, 1),
        "dom_noun_recall": round(r["dom_noun_recall"] * 100, 1),
    } for r in all_results],
    "finding": "pl_core_news_trf (HerBERT) not available as prepackaged SpaCy model (v3.8). "
               "Benchmark uses pl_core_news_lg as best available baseline. "
               "Custom spacy-transformers pipeline with allegro/herbert-base-cased possible but requires separate build."
}

out_path = Path(r"c:\googledrive\priv\AI\projekty\LifeCommandCenter\insights\ner_benchmark_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"Results saved to: {out_path}")
