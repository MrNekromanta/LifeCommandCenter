"""
Entity models and Protocol interface for E²GraphRAG integration.
Task 2.6: Hybrid Entity Extractor
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Entity:
    """Single extracted entity."""
    text: str                    # Canonical form (deduplicated)
    label: str = "ENTITY"        # Type: PROJECT, TOOL, MODEL, PERSON, etc.
    source: str = "unknown"      # Which layer found it: spacy_ner, spacy_noun, ruler, llm

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.text.lower() == other.text.lower()

    def __hash__(self):
        return hash(self.text.lower())


@runtime_checkable
class EntityExtractor(Protocol):
    """Protocol for pluggable entity extraction in E²GraphRAG.
    
    Any extractor must implement extract() returning a list of Entity objects.
    E²GraphRAG uses entity.text for graph construction (co-occurrence edges).
    entity.label is optional metadata for filtering and analysis.
    """
    def extract(self, text: str) -> list[Entity]:
        """Extract entities from a text chunk."""
        ...
