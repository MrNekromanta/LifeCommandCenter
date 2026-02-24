"""
Layer 2: Pattern-based entity matching from seed dictionary.
Uses entity_ruler_seed.json (183 entities, 591 patterns from task 2.4).

This layer catches domain-specific entities that SpaCy NER misses:
projects (LifeCommandCenter, BiznesValidator), tools (n8n, Trello),
models (Claude Haiku, Llama 3.1), hardware (SER9, RTX 3090), etc.
"""
from __future__ import annotations
import json, re
from pathlib import Path
from models import Entity, EntityExtractor

SEED_PATH = Path(r"c:\googledrive\priv\AI\projekty\LifeCommandCenter\insights\entity_ruler_seed.json")


class RulerExtractor(EntityExtractor):
    """Layer 2: Dictionary-based pattern matching."""
    
    def __init__(self, seed_path: Path = SEED_PATH):
        self.patterns: list[dict] = []  # {"pattern": str, "label": str, "canonical": str}
        self._load_seed(seed_path)
    
    def _load_seed(self, path: Path):
        """Load seed dictionary and build pattern list."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for entry in data.get("entities", []):
            label = entry["label"]
            canonical = entry["canonical"]
            # Add canonical name + all aliases as patterns
            all_names = [canonical] + entry.get("aliases", [])
            for name in all_names:
                if len(name) < 2:
                    continue
                self.patterns.append({
                    "pattern": name,
                    "pattern_lower": name.lower(),
                    "label": label,
                    "canonical": canonical,
                })
        
        # Sort by pattern length DESC — match longest first
        self.patterns.sort(key=lambda p: len(p["pattern"]), reverse=True)
    
    def extract(self, text: str) -> list[Entity]:
        entities: dict[str, Entity] = {}
        text_lower = text.lower()
        matched_spans: list[tuple[int, int]] = []  # Prevent overlapping matches
        
        for pat in self.patterns:
            pattern_lower = pat["pattern_lower"]
            # Find all occurrences
            start = 0
            while True:
                idx = text_lower.find(pattern_lower, start)
                if idx == -1:
                    break
                end = idx + len(pattern_lower)
                
                # Check word boundaries (avoid matching "React" inside "Reactive")
                if idx > 0 and text_lower[idx - 1].isalnum():
                    start = end
                    continue
                if end < len(text_lower) and text_lower[end].isalnum():
                    start = end
                    continue
                
                # Check overlap with already matched spans
                overlap = False
                for ms, me in matched_spans:
                    if not (end <= ms or idx >= me):
                        overlap = True
                        break
                
                if not overlap:
                    canonical = pat["canonical"]
                    key = canonical.lower()
                    if key not in entities:
                        entities[key] = Entity(
                            text=canonical,
                            label=pat["label"],
                            source="ruler"
                        )
                    matched_spans.append((idx, end))
                
                start = end
        
        return list(entities.values())

    @property
    def pattern_count(self) -> int:
        return len(self.patterns)
    
    @property 
    def entity_count(self) -> int:
        return len({p["canonical"].lower() for p in self.patterns})
