"""
Layer 1: SpaCy NER + Noun extraction.
Baseline entity extraction using pl_core_news_lg and en_core_web_lg.

Benchmark results (task 2.5):
  - Standard NER recall: 67%
  - Domain NER recall: 48% (PL: 29%, EN: 67%, MIX: 52%)
  - Noun recall: 95% (but without semantic labels)
"""
from __future__ import annotations
import spacy
from models import Entity, EntityExtractor

# SpaCy label mapping to our labels
SPACY_LABEL_MAP = {
    # Polish labels
    "persName": "PERSON", "orgName": "ORG", "placeName": "LOCATION",
    "geogName": "LOCATION", "date": "DATE", "time": "DATE",
    # English labels
    "PERSON": "PERSON", "ORG": "ORG", "GPE": "LOCATION", "LOC": "LOCATION",
    "FAC": "LOCATION", "PRODUCT": "PRODUCT", "WORK_OF_ART": "CONCEPT",
    "EVENT": "CONCEPT", "DATE": "DATE", "TIME": "DATE",
    "MONEY": "VALUE", "QUANTITY": "VALUE", "CARDINAL": "VALUE",
    "NORP": "ORG", "LAW": "CONCEPT", "LANGUAGE": "CONCEPT",
}

# Noise filters
STOP_NOUNS = {
    "projekt", "system", "tool", "model", "warstwa", "dane", "plik",
    "kod", "sesja", "krok", "opis", "cel", "plan", "use", "way",
    "thing", "part", "time", "day", "example", "case", "set",
    "data", "file", "code", "step", "type", "layer", "list",
    "chunk", "node", "edge", "query", "result", "level", "cost",
}

MIN_ENTITY_LENGTH = 2  # Skip single-char entities


class SpacyExtractor(EntityExtractor):
    """Layer 1: SpaCy NER + noun extraction."""
    
    def __init__(self, pl_model: str = "pl_core_news_lg", en_model: str = "en_core_web_lg"):
        self.nlp_pl = spacy.load(pl_model, disable=["lemmatizer"])
        self.nlp_en = spacy.load(en_model, disable=["lemmatizer"])

    def extract(self, text: str) -> list[Entity]:
        entities: dict[str, Entity] = {}  # lowercase -> Entity (dedup)
        
        # Run both models on every chunk (MIX is most common)
        doc_pl = self.nlp_pl(text)
        doc_en = self.nlp_en(text)
        
        # NER entities (higher confidence — labeled)
        for doc, model_name in [(doc_pl, "pl"), (doc_en, "en")]:
            for ent in doc.ents:
                if len(ent.text.strip()) < MIN_ENTITY_LENGTH:
                    continue
                label = SPACY_LABEL_MAP.get(ent.label_, "ENTITY")
                key = ent.text.strip().lower()
                if key not in entities:
                    entities[key] = Entity(
                        text=ent.text.strip(),
                        label=label,
                        source=f"spacy_ner_{model_name}"
                    )

        # Noun extraction (high recall, no labels)
        seen_nouns: set[str] = set()
        for doc in [doc_pl, doc_en]:
            for token in doc:
                if token.pos_ in ("NOUN", "PROPN") and len(token.text) > MIN_ENTITY_LENGTH:
                    key = token.text.strip().lower()
                    if key not in STOP_NOUNS and key not in entities and key not in seen_nouns:
                        seen_nouns.add(key)
                        entities[key] = Entity(
                            text=token.text.strip(),
                            label="ENTITY",  # Unknown type — Layer 2/3 may upgrade
                            source="spacy_noun"
                        )
        
        # EN noun chunks (multi-word entities like "Docker Compose")
        try:
            for chunk in doc_en.noun_chunks:
                chunk_text = chunk.text.strip()
                if len(chunk_text) > MIN_ENTITY_LENGTH and " " in chunk_text:
                    key = chunk_text.lower()
                    if chunk.root.pos_ in ("NOUN", "PROPN") and key not in STOP_NOUNS:
                        if key not in entities:
                            entities[key] = Entity(
                                text=chunk_text,
                                label="ENTITY",
                                source="spacy_noun_chunk"
                            )
        except ValueError:
            pass  # noun_chunks not available (parser disabled or unsupported)
        
        return list(entities.values())
