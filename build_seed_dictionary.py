"""
EntityRuler Seed Dictionary Generator
Task 2.4: Extract, clean, deduplicate entities from audit files.
Output: JSON seed dictionary for SpaCy EntityRuler (Layer 2 of Hybrid Extractor)
"""
import re, json, sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

audit_dir = Path(r"c:\googledrive\priv\AI\projekty\LifeCommandCenter\insights\audit")

# ============================================================
# CURATED SEED DICTIONARY
# Source: 9 audit files from insights/audit/
# Categories follow SpaCy NER labels + custom domain labels
# ============================================================

seed = {
    "_meta": {
        "version": "1.0",
        "created": "2026-02-24",
        "source": "9 audit files from insights/audit/",
        "purpose": "SpaCy EntityRuler seed for Hybrid Entity Extractor (Layer 2)",
        "task": "2.4 from ROADMAP.md",
        "categories": {
            "PROJECT": "Krzysiek's projects (side projects, work, learning)",
            "TOOL": "Software tools, frameworks, services, libraries",
            "HARDWARE": "Physical hardware, devices, components",
            "MODEL": "AI/ML models (LLMs, embedding models, etc.)",
            "PLATFORM": "Cloud platforms, hosting, blockchain networks",
            "CONCEPT": "Domain concepts, methodologies, patterns",
            "PERSON": "People mentioned in conversations",
            "ORG": "Organizations, companies, institutions",
            "LOCATION": "Physical locations relevant to projects",
            "PRODUCT": "Specific products (bee products, food, etc.)",
            "BIOMEDICAL": "Biomedical entities (proteins, pathways, etc.)"
        }
    },
    "entities": []
}

def add(label, canonical, aliases=None, notes=""):
    entry = {"label": label, "canonical": canonical}
    if aliases:
        entry["aliases"] = aliases
    if notes:
        entry["notes"] = notes
    seed["entities"].append(entry)

# ============================================================
# PROJECTS (from relation graphs across all audits)
# ============================================================

# --- Active / Core ---
add("PROJECT", "LifeCommandCenter", ["LCC", "Life Command Center", "LifeCC"])
add("PROJECT", "BiznesValidator", ["Biznes Validator", "BV"])
add("PROJECT", "Crypto Phantom Rebalancing", [
    "Crypto Rebalancer", "Crypto Rebalancing System", "Crypto_Phantom_Rebalancing",
    "Crypto_Rebalancing_System", "Crypto_Rebalancer", "rebalancer", "phantom rebalancing"
])
add("PROJECT", "Liofilizacja", ["liofilizacja projekt", "freeze-drying business"])

# --- Work ---
add("PROJECT", "Allmedica FENG", ["ALLMEDICA_FENG", "FENG", "Allmedica - FENG", "SZAFLARY"])
add("PROJECT", "Allmedica FENX", ["ALLMEDICA_FENX", "FENX", "Allmedica - FENX"])

# --- AI/Automation ---
add("PROJECT", "AI Automation", ["AI_Automation", "AI automation business", "Wiki Cleanup"])
add("PROJECT", "AI Grant System", ["AI_Grant_System", "grant automation", "automatyzacja wniosków dotacyjnych"])
add("PROJECT", "DD AI System", ["DD_AI_System", "due diligence AI", "Document Intelligence Hub", "DOCUMENT_INTELLIGENCE_HUB"])
add("PROJECT", "Kurs PM/PO", ["KURS_AI_AUTOMATION", "kurs PM PO", "Kurs-PM-PO"])
add("PROJECT", "Podręcznik AI Dzieci", ["PODRĘCZNIK_AI_DZIECI", "podręcznik AI dla dzieci"])

# --- Knowledge/RAG ---
add("PROJECT", "Wiki RAG Baremetal", ["Wiki_RAG_Baremetal", "wiki RAG", "Confluence RAG"])
add("PROJECT", "Wiki RAG Cloud", ["Wiki_RAG_Cloud"])
add("PROJECT", "Digital Brain GraphRAG", ["Digital_Brain_GraphRAG", "PKB", "Personal Knowledge Base"])
add("PROJECT", "E²GraphRAG Pipeline", ["E2GraphRAG", "E²GraphRAG", "nano-graphrag", "GraphRAG pipeline"])
add("PROJECT", "Fan Fiction RAG", ["Fan_Fiction_RAG", "ebook RAG"])
add("PROJECT", "Ebook Library", ["Ebook_Library", "Calibre library"])

# --- Hardware/Infra ---
add("PROJECT", "Beelink SER9 Lab", ["Beelink_SER9_Lab", "Home_Lab_SER9", "SER9 lab", "home lab"])
add("PROJECT", "RTX 3090 Upgrade", ["RTX_3090_Desktop", "RTX_3090_Upgrade", "AI Lab Hardware", "AI_Lab_Hardware"])
add("PROJECT", "MiniPC Research", ["MiniPC_Research"])

# --- Home/Life ---
add("PROJECT", "Smart Home", ["Smart_Home", "home assistant project"])
add("PROJECT", "Food Forest", ["Food_Forest", "food forest", "las jadalny"])
add("PROJECT", "Thermal Insulation", ["Thermal_Insulation", "termomodernizacja", "izolacja"])
add("PROJECT", "PV Energy", ["PV_Energy", "fotowoltaika", "panele PV"])
add("PROJECT", "Meshtastic", ["meshtastic", "LoRa mesh"])
add("PROJECT", "Raspberry Pi Education", ["Raspberry_Pi_Education", "nauka programowania Jasio"])

# --- Health ---
add("PROJECT", "ADHD Mental Health", ["ADHD_Mental_Health", "ADHD projekt", "zdrowie psychiczne"])
add("PROJECT", "Neurotransmission Docs", ["Neurotransmission_Docs", "dokumentacja neuroprzekaźników"])
add("PROJECT", "Apitherapy Research", ["Apitherapy_Research", "produkty pszczele"])
add("PROJECT", "Propolis Edukacja", ["Propolis_Edukacja", "materiały o propolisie"])
add("PROJECT", "Mleczko Edukacja", ["Mleczko_Edukacja", "materiały o mleczku pszczelim"])

# --- Other ---
add("PROJECT", "Mitos Translation", ["Mitos_Translation", "tłumaczenie Mitos"])
add("PROJECT", "Digital Memorial", ["Digital_Memorial", "pamięć cyfrowa"])
add("PROJECT", "Habit Tracker", ["Habit_Tracker", "tracker nawyków"])
add("PROJECT", "CNC Research", ["CNC_Research", "frezarka CNC"])
add("PROJECT", "Browser Automation", ["Browser_Automation", "Playwright automation"])
add("PROJECT", "IDP Research", ["IDP_Research", "Internal Developer Platform"])
add("PROJECT", "Terraform CICD", ["Terraform_CICD", "Terraform CI/CD"])
add("PROJECT", "Duckweed", ["Duckweed", "rzęsa wodna"])
add("PROJECT", "Confluence Wiki Analysis", ["Confluence_Wiki_Analysis"])
add("PROJECT", "Grant Writing", ["Grant_Writing", "pisanie wniosków"])
add("PROJECT", "Crypto Portfolio", ["Crypto_Portfolio", "portfel krypto"])

# ============================================================
# TOOLS & FRAMEWORKS
# ============================================================

# --- Workflow/Automation ---
add("TOOL", "n8n", ["N8n", "n8n workflow", "n8n automation"])
add("TOOL", "Home Assistant", ["home assistant", "HA", "HASS"])
add("TOOL", "MCP", ["Model Context Protocol", "MCP server", "MCP servers"])
add("TOOL", "Desktop Commander", ["DesktopCommander", "DC", "Desktop Commander MCP"])
add("TOOL", "Playwright", ["playwright", "Playwright MCP"])
add("TOOL", "LangChain", ["langchain", "LangGraph", "LangChain/LangGraph"])

# --- Databases ---
add("TOOL", "PostgreSQL", ["Postgres", "PostgreSQL 15", "postgres", "psql", "crypto-postgres"])
add("TOOL", "Supabase", ["supabase"])
add("TOOL", "Qdrant", ["qdrant", "vector DB Qdrant"])
add("TOOL", "Meilisearch", ["meilisearch", "Meili"])
add("TOOL", "ChromaDB", ["Chroma", "chromadb", "Chroma DB"])
add("TOOL", "Pinecone", ["pinecone"])
add("TOOL", "Redis", ["redis"])

# --- Web/API Frameworks ---
add("TOOL", "FastAPI", ["fastapi", "Fast API"])
add("TOOL", "React", ["react", "React.js"])
add("TOOL", "Next.js", ["nextjs", "Next.js"])
add("TOOL", "Vite", ["vite"])
add("TOOL", "Tailwind CSS", ["tailwind", "Tailwind", "TailwindCSS"])
add("TOOL", "Streamlit", ["streamlit"])
add("TOOL", "Express", ["express", "Express.js"])
add("TOOL", "Zustand", ["zustand"])
add("TOOL", "Recharts", ["recharts"])
add("TOOL", "Lucide React", ["lucide-react", "Lucide"])

# --- DevOps/Infra ---
add("TOOL", "Docker", ["docker", "Docker Compose", "docker-compose", "Docker Desktop"])
add("TOOL", "Nginx", ["nginx"])
add("TOOL", "Grafana", ["grafana"])
add("TOOL", "Jenkins", ["jenkins"])
add("TOOL", "GitLab", ["gitlab", "GitLab CI"])
add("TOOL", "GitHub", ["github", "Git/GitHub"])
add("TOOL", "Puppet", ["puppet"])
add("TOOL", "Terraform", ["terraform"])
add("TOOL", "Cloudflare Tunnel", ["cloudflare tunnel", "CF Tunnel"])
add("TOOL", "Cloudflare Turnstile", ["cloudflare turnstile", "Turnstile"])
add("TOOL", "Vercel", ["vercel"])
add("TOOL", "Tailscale", ["tailscale", "Tailscale VPN"])

# --- AI/ML Frameworks ---
add("TOOL", "Ollama", ["ollama"])
add("TOOL", "LocalAI", ["localai", "LocalAI"])
add("TOOL", "SpaCy", ["spacy", "SpaCy", "spacy-pl-trf"])
add("TOOL", "HerBERT", ["herbert", "HerBERT", "spacy-pl-trf"])
add("TOOL", "Pydantic", ["pydantic"])

# --- Communication ---
add("TOOL", "Telegram Bot", ["Telegram", "telegram bot", "python-telegram-bot"])
add("TOOL", "ElevenLabs", ["elevenlabs", "ElevenLabs voice"])
add("TOOL", "Whisper", ["whisper", "Whisper large-v3", "OpenAI Whisper"])

# --- Document Processing ---
add("TOOL", "Pandoc", ["pandoc"])
add("TOOL", "python-docx", ["python-docx", "docx lib"])
add("TOOL", "Google Document AI", ["Document AI", "Google Doc AI"])

# --- Other Tools ---
add("TOOL", "Trello", ["trello", "Trello board", "Trello MCP"])
add("TOOL", "Obsidian", ["obsidian"])
add("TOOL", "Calibre-Web", ["calibre-web", "Calibre Web", "Calibre-Web Automated"])
add("TOOL", "Syncthing", ["syncthing"])
add("TOOL", "Bitwarden", ["bitwarden"])
add("TOOL", "Google Drive", ["google drive", "Google Drive sync"])
add("TOOL", "Stripe", ["stripe", "Stripe payments"])
add("TOOL", "Przelewy24", ["przelewy24", "P24"])
add("TOOL", "MetaMask", ["metamask", "MetaMask wallet"])
add("TOOL", "PowerShell", ["powershell", "PS"])
add("TOOL", "Inter", notes="Font used in BiznesValidator")
add("TOOL", "Midjourney", ["midjourney"])
add("TOOL", "Canva", ["canva", "Canva Pro"])

# --- Python/Libraries ---
add("TOOL", "Web3.py", ["web3.py", "web3", "Web3"])
add("TOOL", "psycopg2", ["psycopg2"])
add("TOOL", "schedule", notes="Python scheduling library")
add("TOOL", "httrack", ["httrack"])

# ============================================================
# AI MODELS
# ============================================================

add("MODEL", "Claude", ["Claude AI", "Claude API", "Anthropic Claude"])
add("MODEL", "Claude Sonnet", ["Claude 3.5 Sonnet", "Sonnet", "Claude Sonnet 4.5"])
add("MODEL", "Claude Haiku", ["Haiku", "Claude Haiku 4.5"])
add("MODEL", "Claude Opus", ["Opus", "Claude Opus 4.5"])
add("MODEL", "GPT-4o", ["gpt-4o", "GPT-4 Vision", "GPT-4o-mini"])
add("MODEL", "DeepSeek-R1", ["DeepSeek R1", "deepseek-r1", "DeepSeek-R1:7B", "DeepSeek-R1:14B", "DeepSeek-R1:32B"])
add("MODEL", "DeepSeek-V3", ["deepseek-v3"])
add("MODEL", "Qwen3:8B", ["Qwen3", "qwen3:8b", "Qwen 3"])
add("MODEL", "O1-preview", ["o1-preview", "O1"])
add("MODEL", "Llama 3.1 70B", ["Llama 3.1", "llama3.1"])
add("MODEL", "Mixtral 8x7B", ["Mixtral", "mixtral", "Mixtral 8x7B Instruct"])
add("MODEL", "CodeLlama 34B", ["CodeLlama", "codellama"])
add("MODEL", "BGE-M3", ["bge-m3", "BAAI/bge-m3"])
add("MODEL", "E5-mistral-7b", ["e5-mistral", "E5-mistral-7b-instruct"])
add("MODEL", "text-embedding-3-small", ["OpenAI embeddings", "text-embedding-3-small"])

# ============================================================
# HARDWARE
# ============================================================

add("HARDWARE", "Beelink SER9", ["SER9", "ser9", "Beelink", "serwer SER9"])
add("HARDWARE", "RTX 3090", ["RTX 3090 24GB", "RTX3090", "GeForce RTX 3090"])
add("HARDWARE", "Raspberry Pi 4", ["Raspberry Pi", "RPi", "Raspberry Pi 4 8GB"])
add("HARDWARE", "HarvestRight", ["harvest right", "liofilizator", "freeze dryer"])
add("HARDWARE", "NAS 4x4TB", ["NAS", "serwer NAS"])
add("HARDWARE", "LiFePO4", ["LiFePO4 battery", "bateria LiFePO4", "akumulator LiFePO4"])

# ============================================================
# PLATFORMS / NETWORKS
# ============================================================

add("PLATFORM", "Arbitrum", ["arbitrum", "Arbitrum One", "arb"])
add("PLATFORM", "Solana", ["solana", "SOL"])
add("PLATFORM", "Tron", ["tron", "TRX", "TRON"])
add("PLATFORM", "Ethereum", ["ethereum", "ETH", "Ethereum L1"])
add("PLATFORM", "Alchemy", ["alchemy", "Alchemy RPC"])
add("PLATFORM", "Chainlink", ["chainlink", "Chainlink oracle"])
add("PLATFORM", "Nutanix", ["nutanix"])
add("PLATFORM", "Rocky Linux", ["Rocky Linux 9", "rocky linux"])
add("PLATFORM", "Ubuntu", ["ubuntu", "Ubuntu Server", "Ubuntu 24.04"])
add("PLATFORM", "Windows 11", ["Windows", "windows 11", "Win11"])

# ============================================================
# DOMAIN CONCEPTS
# ============================================================

add("CONCEPT", "rebalancing", ["rebalancing portfolio", "portfolio rebalancing", "80/20 rebalancing"])
add("CONCEPT", "phantom buffer", ["phantom capital", "virtual buffer", "wirtualny bufor"])
add("CONCEPT", "mean-reversion", ["mean-reverting", "mean reversion strategy"])
add("CONCEPT", "WIP limit", ["WIP limit 3", "Work in Progress limit"])
add("CONCEPT", "stale detection", ["stale card", "karta stale", "14 dni bez aktywności"])
add("CONCEPT", "daily digest", ["morning digest", "daily summary"])
add("CONCEPT", "ADHD coaching", ["coaching ADHD", "external accountability", "pattern detection"])
add("CONCEPT", "Entity Extraction", ["entity extraction", "NER", "Named Entity Recognition"])
add("CONCEPT", "Hybrid Entity Extractor", ["3-warstwowy extractor", "hybrid extractor"])
add("CONCEPT", "EntityRuler", ["entity ruler", "SpaCy EntityRuler", "pattern matching rules"])
add("CONCEPT", "Summary Tree", ["summary tree", "hierarchiczne streszczenia"])
add("CONCEPT", "Entity Graph", ["entity graph", "graf encji", "knowledge graph"])
add("CONCEPT", "chunking", ["chunk", "chunking strategy", "1200 tokens"])
add("CONCEPT", "board per project", ["board per projekt", "konwencja Trello"])
add("CONCEPT", "session protocol", ["protokół sesji", "kickoff", "closing"])
add("CONCEPT", "balance-based tracking", ["balance tracking", "snapshot comparison"])
add("CONCEPT", "monitoring-only", ["read-only monitoring", "bez automatic execution"])
add("CONCEPT", "GHP/GMP", ["Good Hygiene Practice", "Good Manufacturing Practice"])
add("CONCEPT", "rażąco niska cena", ["abnormally low tender", "RNC"])
add("CONCEPT", "zamówienia publiczne", ["public procurement", "PZP", "Prawo zamówień publicznych"])
add("CONCEPT", "revenue template", ["revenue model", "model przychodowy"])
add("CONCEPT", "country pack", ["country packs", "pakiety krajowe"])
add("CONCEPT", "escitalopram", ["Lexapro", "SSRI"])
add("CONCEPT", "bupropion", ["Wellbutrin", "NDRI"])
add("CONCEPT", "E²GraphRAG", ["E2GraphRAG", "E-squared GraphRAG"])
add("CONCEPT", "Adaptive Retrieval", ["adaptive strategy", "local vs global mode"])

# ============================================================
# ORGANIZATIONS
# ============================================================

add("ORG", "Anthropic", ["anthropic"])
add("ORG", "OpenAI", ["openai", "Open AI"])
add("ORG", "Allmedica", ["allmedica", "ALLMEDICA"])
add("ORG", "IPI PAN", ["IPI PAN", "Instytut Podstaw Informatyki PAN"])

# ============================================================
# LOCATIONS
# ============================================================

add("LOCATION", "Krzeszowice", ["krzeszowice"])
add("LOCATION", "Szaflary", ["szaflary", "SZAFLARY"])
add("LOCATION", "Miękinia", ["miękinia", "Miekinia"])

# ============================================================
# BIOMEDICAL (from Apitherapy audits)
# ============================================================

add("BIOMEDICAL", "NF-κB", ["NF-kB", "NF-kappaB", "szlak NF-κB"])
add("BIOMEDICAL", "TGF-β", ["TGF-beta", "TGF-β1", "Transforming Growth Factor"])
add("BIOMEDICAL", "VEGF", ["VEGF", "Vascular Endothelial Growth Factor"])
add("BIOMEDICAL", "CAPE", ["CAPE", "kwas kawowy fenyloester"])
add("BIOMEDICAL", "10-HDA", ["10-HDA", "kwas 10-hydroksy-2-decenowy", "10-hydroxy-2-decenoic acid"])
add("BIOMEDICAL", "propolis", ["propolis", "ekstrakt propolisowy"])
add("BIOMEDICAL", "mleczko pszczele", ["royal jelly", "mleczko pszczele", "bee milk"])

# ============================================================
# CRYPTO TOKENS (from Crypto audits)
# ============================================================

add("PRODUCT", "ETH", ["Ether", "Ethereum token"])
add("PRODUCT", "USDC", ["USD Coin", "USDC stablecoin"])
add("PRODUCT", "SOL", ["Solana token"])
add("PRODUCT", "USDD", ["USDD stablecoin"])
add("PRODUCT", "PAXG", ["Pax Gold", "PAXG gold"])
add("PRODUCT", "SCRT", ["Secret", "SCRT token"])
add("PRODUCT", "USDJ", ["USDJ stablecoin"])

# ============================================================
# OUTPUT
# ============================================================

# Stats
labels = defaultdict(int)
for e in seed["entities"]:
    labels[e["label"]] += 1

print("=== SEED DICTIONARY STATS ===")
print(f"Total entities: {len(seed['entities'])}")
for label, count in sorted(labels.items()):
    print(f"  {label}: {count}")

# Count total patterns (canonical + aliases)
total_patterns = 0
for e in seed["entities"]:
    total_patterns += 1  # canonical
    total_patterns += len(e.get("aliases", []))
print(f"\nTotal patterns (canonical + aliases): {total_patterns}")

# Save
output_path = Path(r"c:\googledrive\priv\AI\projekty\LifeCommandCenter\insights\entity_ruler_seed.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(seed, f, ensure_ascii=False, indent=2)
print(f"\nSaved to: {output_path}")

# Also generate SpaCy EntityRuler patterns format for quick reference
patterns = []
for e in seed["entities"]:
    names = [e["canonical"]] + e.get("aliases", [])
    for name in names:
        patterns.append({"label": e["label"], "pattern": name, "id": e["canonical"]})

patterns_path = Path(r"c:\googledrive\priv\AI\projekty\LifeCommandCenter\insights\entity_ruler_patterns.jsonl")
with open(patterns_path, "w", encoding="utf-8") as f:
    for p in patterns:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")
print(f"SpaCy patterns saved to: {patterns_path} ({len(patterns)} patterns)")
