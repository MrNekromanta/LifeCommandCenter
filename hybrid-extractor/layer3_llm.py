"""
Layer 3: LLM micro-extraction using local Ollama (Qwen3:1.7b).
Called selectively — only for chunks where Layers 1+2 found few entities.

Cost: 0 PLN (local inference on SER9).
Uses /api/chat for proper system/user message format.
"""
from __future__ import annotations
import json, re, requests
from models import Entity, EntityExtractor

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "qwen3:1.7b"

SYSTEM_MSG = """You are an entity extraction tool. Extract named entities and return ONLY a JSON array.
Each entity: {"text": "exact text from input", "label": "TYPE"}
Types: PROJECT, TOOL, MODEL, HARDWARE, PLATFORM, CONCEPT, PERSON, ORG, LOCATION, PRODUCT, BIOMEDICAL
Rules:
- Extract project names, tools, frameworks, AI models, hardware, people, organizations, medical terms
- Keep original casing from the input text
- Skip generic words (system, data, file, code, project, plan, status)
- Max 15 entities
- Return ONLY the JSON array, nothing else"""

USER_MSG_TEMPLATE = """Extract entities from this text that are NOT in the already-found list.

Text: {text}

Already found: {known_entities}

Return ONLY a JSON array of new entities. If none found, return []"""


class LLMExtractor(EntityExtractor):
    """Layer 3: Local Ollama LLM micro-extraction for low-entity chunks."""
    
    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = OLLAMA_URL):
        self.model = model
        self.base_url = base_url
        self.calls_made = 0
        self.total_duration_ms = 0
    
    def extract(self, text: str, known_entities: list[str] | None = None) -> list[Entity]:
        known = ", ".join(known_entities) if known_entities else "none"
        
        try:
            resp = requests.post(self.base_url, json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_MSG},
                    {"role": "user", "content": USER_MSG_TEMPLATE.format(text=text, known_entities=known)},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 1024,
                }
            }, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            
            self.calls_made += 1
            self.total_duration_ms += data.get("total_duration", 0) / 1_000_000
            
            raw = data.get("message", {}).get("content", "").strip()
            
            # Strip markdown code fences
            raw = re.sub(r'^```json\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            
            # Find JSON array in response
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if not match:
                return []
            
            items = json.loads(match.group())
            entities = []
            for item in items:
                if isinstance(item, dict) and "text" in item:
                    ent_text = item["text"].strip()
                    if len(ent_text) >= 2:
                        entities.append(Entity(
                            text=ent_text,
                            label=item.get("label", "ENTITY"),
                            source="llm"
                        ))
            return entities
            
        except Exception as e:
            print(f"[LLM Layer 3] Error: {e}")
            return []
    
    @property
    def avg_duration_ms(self) -> float:
        if self.calls_made == 0:
            return 0
        return round(self.total_duration_ms / self.calls_made, 0)
    
    @property
    def cost_estimate_pln(self) -> float:
        return 0.0
