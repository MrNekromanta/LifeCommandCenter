"""
Layer 3: LLM micro-extraction using Claude Sonnet via Anthropic API.
Called selectively — only for chunks where Layers 1+2 found few entities.

Cost: ~0.07 USD per full corpus run (15 chunks × ~700 tokens).
"""
from __future__ import annotations
import json, os, re
from pathlib import Path
from dotenv import load_dotenv
from models import Entity, EntityExtractor

# Load .env from hybrid-extractor dir
load_dotenv(Path(__file__).parent / ".env")

MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """You are an entity extraction tool for a Polish/English mixed-language knowledge base.
Extract named entities and return ONLY a valid JSON array.
Each entity: {"text": "exact text from input", "label": "TYPE"}

Types: PROJECT, TOOL, MODEL, HARDWARE, PLATFORM, CONCEPT, PERSON, ORG, LOCATION, PRODUCT, BIOMEDICAL

Rules:
- Extract: project names, tools, frameworks, AI models, hardware, people, organizations, medical/biomedical terms
- Handle Polish declension: "bupropionu" → {"text": "bupropion", "label": "BIOMEDICAL"}
- Keep original casing for proper nouns, use base form for declined words
- Skip generic nouns (system, data, file, code, project, plan, status, opis, cel)
- For multi-word entities use the full name (e.g. "Docker Compose" not "Docker")
- Max 15 entities per chunk
- Return ONLY the JSON array, no explanation, no markdown"""

USER_PROMPT_TEMPLATE = """Extract entities from this text that are NOT already in the known list.

Text:
{text}

Already found by other methods: {known_entities}

Return ONLY a JSON array of NEW entities not in the above list. If none found, return []"""


class LLMExtractor(EntityExtractor):
    """Layer 3: Claude Sonnet micro-extraction for low-entity chunks."""
    
    def __init__(self, model: str = MODEL, api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._client = None
        self.calls_made = 0
        self.input_tokens = 0
        self.output_tokens = 0
    
    @property
    def client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("pip install anthropic")
        return self._client
    
    def extract(self, text: str, known_entities: list[str] | None = None) -> list[Entity]:
        known = ", ".join(known_entities) if known_entities else "none"
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(text=text, known_entities=known)
                }]
            )
            self.calls_made += 1
            self.input_tokens += response.usage.input_tokens
            self.output_tokens += response.usage.output_tokens
            
            raw = response.content[0].text.strip()
            # Strip markdown code fences if present
            raw = re.sub(r'^```json\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            
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
        return 0  # API doesn't report duration
    
    @property
    def cost_estimate_pln(self) -> float:
        """Sonnet: $3/1M input, $15/1M output. ~4 PLN/USD."""
        cost_usd = (self.input_tokens * 3 / 1_000_000) + (self.output_tokens * 15 / 1_000_000)
        return round(cost_usd * 4, 4)
