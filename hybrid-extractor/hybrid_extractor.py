"""
HybridExtractor — orchestrates 3 layers of entity extraction.

Layer 1: SpaCy NER + nouns (free, local, ~48% domain recall)
Layer 2: EntityRuler patterns (free, local, catches known entities)
Layer 3: LLM Haiku (paid, selective, catches remaining ~5%)

Threshold logic: Layer 3 fires only when L1+L2 find fewer than
MIN_ENTITIES_THRESHOLD entities in a chunk.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from models import Entity, EntityExtractor
from layer1_spacy import SpacyExtractor
from layer2_ruler import RulerExtractor
from layer3_llm import LLMExtractor

# If L1+L2 find fewer than this many entities, call L3 (LLM)
MIN_ENTITIES_THRESHOLD = 3


@dataclass
class ExtractionStats:
    """Per-chunk extraction statistics."""
    chunk_id: int = 0
    layer1_count: int = 0
    layer2_count: int = 0
    layer3_count: int = 0
    layer3_called: bool = False
    total_unique: int = 0
    
    @property
    def total_raw(self) -> int:
        return self.layer1_count + self.layer2_count + self.layer3_count


class HybridExtractor(EntityExtractor):
    """3-layer hybrid entity extractor for E²GraphRAG.
    
    Usage:
        extractor = HybridExtractor()
        entities = extractor.extract("Some text about LifeCommandCenter and Trello...")
        # Returns: [Entity(text="LifeCommandCenter", label="PROJECT", source="ruler"), ...]
    
    E²GraphRAG integration:
        The extract() method returns list[Entity].
        For graph construction, use [e.text for e in entities] as node names.
        Co-occurrence edges are built by E²GraphRAG from sentence-level overlap.
    """

    def __init__(
        self,
        min_entities_threshold: int = MIN_ENTITIES_THRESHOLD,
        enable_llm: bool = True,
    ):
        self.layer1 = SpacyExtractor()
        self.layer2 = RulerExtractor()
        self.layer3 = LLMExtractor() if enable_llm else None
        self.threshold = min_entities_threshold
        self.stats: list[ExtractionStats] = []
        self._chunk_counter = 0
    
    def extract(self, text: str) -> list[Entity]:
        """Extract entities using all 3 layers with deduplication."""
        self._chunk_counter += 1
        stat = ExtractionStats(chunk_id=self._chunk_counter)
        
        # --- Layer 1: SpaCy ---
        l1_entities = self.layer1.extract(text)
        stat.layer1_count = len(l1_entities)
        
        # --- Layer 2: EntityRuler ---
        l2_entities = self.layer2.extract(text)
        stat.layer2_count = len(l2_entities)
        
        # Merge L1 + L2 with deduplication
        merged: dict[str, Entity] = {}
        
        # L2 (ruler) takes priority — has better labels
        for e in l2_entities:
            merged[e.text.lower()] = e
        
        # L1 (spacy) fills gaps
        for e in l1_entities:
            key = e.text.lower()
            if key not in merged:
                merged[key] = e
            elif e.label != "ENTITY" and merged[key].label == "ENTITY":
                # Upgrade unlabeled entity with SpaCy's label
                merged[key] = Entity(text=merged[key].text, label=e.label, source=merged[key].source)
        
        # --- Layer 3: LLM (conditional) ---
        if self.layer3 and len(merged) < self.threshold:
            stat.layer3_called = True
            known = [e.text for e in merged.values()]
            l3_entities = self.layer3.extract(text, known_entities=known)
            stat.layer3_count = len(l3_entities)
            
            for e in l3_entities:
                key = e.text.lower()
                if key not in merged:
                    merged[key] = e
        
        stat.total_unique = len(merged)
        self.stats.append(stat)
        
        return list(merged.values())
    
    def extract_for_graph(self, text: str) -> list[str]:
        """Convenience method for E²GraphRAG — returns just entity text strings."""
        return [e.text for e in self.extract(text)]
    
    def get_summary(self) -> dict:
        """Return summary statistics across all processed chunks."""
        if not self.stats:
            return {"chunks": 0}
        
        total_chunks = len(self.stats)
        l3_calls = sum(1 for s in self.stats if s.layer3_called)
        
        return {
            "chunks_processed": total_chunks,
            "avg_entities_per_chunk": round(sum(s.total_unique for s in self.stats) / total_chunks, 1),
            "layer1_avg": round(sum(s.layer1_count for s in self.stats) / total_chunks, 1),
            "layer2_avg": round(sum(s.layer2_count for s in self.stats) / total_chunks, 1),
            "layer3_calls": l3_calls,
            "layer3_call_rate": f"{l3_calls/total_chunks*100:.0f}%",
            "layer3_avg_when_called": round(
                sum(s.layer3_count for s in self.stats if s.layer3_called) / max(l3_calls, 1), 1
            ),
            "llm_input_tokens": self.layer3.input_tokens if self.layer3 else 0,
            "llm_output_tokens": self.layer3.output_tokens if self.layer3 else 0,
            "llm_cost_pln": self.layer3.cost_estimate_pln if self.layer3 else 0,
        }
