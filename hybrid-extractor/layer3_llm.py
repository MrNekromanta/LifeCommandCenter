"""
Layer 3: LLM micro-extraction using Claude Haiku.
Called selectively — only for chunks where Layers 1+2 found few entities.

Cost: ~0.01 PLN/chunk. For 100 conversations (~1000 chunks),
  ~5-15 PLN if 10-30% of chunks trigger Layer 3.
"""
from __future__ import annotations
import json, os, re
from models import Entity, EntityExtractor

SYSTEM_PROMPT = """Extract named entities from the text. Return ONLY a JSON array.
Each entity: {"text": "exact text", "label": "TYPE"}

Types: PROJECT, TOOL, MODEL, HARDWARE, PLATFORM, CONCEPT, PERSON, ORG, LOCATION, PRODUCT, BIOMEDICAL

Rules:
- Extract project names, tools, frameworks, AI models, hardware, people, organizations
- Keep original casing
- Skip generic nouns (system, data, file, code, project, plan)
- For multi-word entities use the full name (e.g. "Docker Compose" not "Docker")
- Max 15 entities per chunk
- Return [] if no entities found"""

USER_PROMPT_TEMPLATE = """Text:
{text}

Already found by other methods: {known_entities}

Extract ADDITIONAL entities not in the "already found" list. Return JSON array only."""


class LLMExtractor(EntityExtractor):
    """Layer 3: Claude Haiku micro-extraction for low-entity chunks."""
    
    def __init__(self, api_key: str | None = None, model: str = "claude-haiku-4-5-20251001"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self._client = None
        self.calls_made = 0
        self.tokens_used = 0
    
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
        """Extract entities via LLM. known_entities = what L1+L2 already found."""
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
            self.tokens_used += response.usage.input_tokens + response.usage.output_tokens
            
            # Parse JSON from response
            raw = response.content[0].text.strip()
            # Strip markdown code fences if present
            raw = re.sub(r'^```json\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            
            items = json.loads(raw)
            entities = []
            for item in items:
                if isinstance(item, dict) and "text" in item:
                    entities.append(Entity(
                        text=item["text"],
                        label=item.get("label", "ENTITY"),
                        source="llm"
                    ))
            return entities
            
        except Exception as e:
            print(f"[LLM Layer 3] Error: {e}")
            return []
    
    @property
    def cost_estimate_pln(self) -> float:
        """Rough cost estimate in PLN. Haiku: ~$0.25/1M input, ~$1.25/1M output."""
        # ~4 PLN/USD
        input_cost = (self.tokens_used * 0.5 * 0.25 / 1_000_000) * 4
        output_cost = (self.tokens_used * 0.5 * 1.25 / 1_000_000) * 4
        return round(input_cost + output_cost, 4)
