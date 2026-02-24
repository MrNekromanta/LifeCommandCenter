"""
Layer 1: SpaCy NER extraction.
v4 — radical precision-over-recall after full eval showed 125 ents/chunk.

Strategy: Ruler (L2) handles domain entities. SpaCy's job is ONLY:
  - PL NER: people, organizations, locations (PERSON, ORG, LOC)
  - EN NER: same but ONLY on English-looking text, heavily filtered
  - No PROPN, no noun chunks (these are Ruler's territory)

Target: SpaCy contributes ~5-15 entities/chunk, all high quality.
Ruler adds ~10-15 domain entities. Total: ~15-25/chunk.
"""
from __future__ import annotations
import spacy
from models import Entity, EntityExtractor

SPACY_LABEL_MAP = {
    # PL labels
    "persName": "PERSON", "orgName": "ORG", "placeName": "LOCATION",
    "geogName": "LOCATION",
    # EN labels 
    "PERSON": "PERSON", "ORG": "ORG", "GPE": "LOCATION", "LOC": "LOCATION",
    "FAC": "LOCATION", "PRODUCT": "PRODUCT",
}

# Only keep these high-value NER labels
KEEP_NER_LABELS_PL = {"persName", "orgName", "placeName", "geogName"}
KEEP_NER_LABELS_EN = {"PERSON", "ORG", "GPE", "LOC", "FAC", "PRODUCT"}

PL_DIACRITICS = set("ąęóśźżćłńĄĘÓŚŹŻĆŁŃ")

# Words that indicate garbage NER entity
NER_GARBAGE_WORDS = {
    # PL function words
    "jako", "przez", "jest", "dla", "lub", "ale", "nie", "tak", "ten", "tym",
    "tego", "tej", "tych", "który", "która", "które", "oraz", "więc", "też",
    "tylko", "jak", "gdy", "już", "nad", "pod", "bez", "przed", "między",
    "na", "do", "od", "ze", "po", "za", "we", "się", "co", "to",
    "będzie", "został", "została", "zostało", "może", "nowy", "nowa",
    # EN function words
    "the", "and", "for", "with", "from", "that", "this", "but", "its",
    "all", "can", "has", "had", "was", "are", "were", "been",
}

MIN_ENTITY_LENGTH = 3

# PL words commonly misclassified as EN entities (no diacritics so diacritics filter misses them)
PL_FALSE_ENTITIES = {
    "klonowanie", "magazynowanie", "konfiguracja", "automatyczne", "standardowe",
    "chronologia", "analiza", "nauka", "zarządzanie", "planowane", "używane",
    "działające", "omówiony", "wspomniany", "zrealizowane", "aktywne",
    "projekty", "narzędzia", "decyzje", "relacje", "wnioski", "rekomendacje",
    "platforma", "integracja", "walidacja", "implementacja", "architektura",
    "monitoring", "deployment", "orchestracja", "automatyzacja", "prognoza",
    "optymalizacja", "migracja", "infrastruktura", "dokumentacja",
    # Audit section headers (ALL-CAPS PL words)
    "chronologia", "projekty", "decyzje", "relacje", "rekomendacje",
    "narzędzia", "koncepty", "kontekst", "podsumowanie", "wnioski",
}


def _has_pl_diacritics(text: str) -> bool:
    return bool(PL_DIACRITICS & set(text))

def _is_garbage(text: str) -> bool:
    words = set(text.lower().split())
    return bool(words & NER_GARBAGE_WORDS)

def _clean_entity_text(text: str) -> str:
    """Strip markdown artifacts and trailing punctuation."""
    text = text.strip().lstrip("*_~`#|").rstrip(":.,;!?*_~`|")
    return text.strip()

def _is_noise_entity(text: str) -> bool:
    """Final noise filter for entities that passed other checks."""
    # Pure numbers
    if text.replace(".", "").replace(",", "").isdigit():
        return True
    # File extensions
    if text.startswith(".") and len(text) < 6:
        return True
    # Markdown table fragments
    if "|" in text:
        return True
    # Graph notation arrows
    if "→" in text or "←" in text or "->" in text:
        return True
    # Too short after cleaning
    if len(text) < MIN_ENTITY_LENGTH:
        return True
    return False


class SpacyExtractor(EntityExtractor):
    """Layer 1: SpaCy NER only (v4, precision-focused)."""
    
    def __init__(self, pl_model: str = "pl_core_news_lg", en_model: str = "en_core_web_lg"):
        self.nlp_pl = spacy.load(pl_model, disable=["lemmatizer", "parser"])
        self.nlp_en = spacy.load(en_model, disable=["lemmatizer", "parser"])

    def extract(self, text: str) -> list[Entity]:
        entities: dict[str, Entity] = {}
        
        doc_pl = self.nlp_pl(text)
        doc_en = self.nlp_en(text)
        
        # --- PL NER (primary for Polish text) ---
        for ent in doc_pl.ents:
            if ent.label_ not in KEEP_NER_LABELS_PL:
                continue
            ent_text = _clean_entity_text(ent.text)
            if _is_noise_entity(ent_text):
                continue
            if _is_garbage(ent_text):
                continue
            # Skip known false positives (section headers, generic PL words)
            if ent_text.lower() in PL_FALSE_ENTITIES:
                continue
            # Skip all-lowercase
            if ent_text[0].islower():
                continue
            label = SPACY_LABEL_MAP.get(ent.label_, "ENTITY")
            key = ent_text.lower()
            if key not in entities:
                entities[key] = Entity(text=ent_text, label=label, source="spacy_ner_pl")

        # --- EN NER (supplementary, strict filtering) ---
        for ent in doc_en.ents:
            if ent.label_ not in KEEP_NER_LABELS_EN:
                continue
            ent_text = _clean_entity_text(ent.text)
            if _is_noise_entity(ent_text):
                continue
            if _is_garbage(ent_text):
                continue
            # Skip if contains PL diacritics (EN model misclassifying PL text)
            if _has_pl_diacritics(ent_text):
                continue
            # Skip known PL words that EN model grabs
            if ent_text.lower() in PL_FALSE_ENTITIES:
                continue
            # Must start with uppercase
            if ent_text[0].islower():
                continue
            # Multi-word: all words must start uppercase (skip "po polsku | Status" etc.)
            words = ent_text.split()
            if len(words) > 1 and not all(w[0].isupper() for w in words if len(w) > 2):
                continue
            # Skip if contains pipes, markdown, special chars
            if any(c in ent_text for c in "|*~`#→←{}[]"):
                continue
            
            label = SPACY_LABEL_MAP.get(ent.label_, "ENTITY")
            key = ent_text.lower()
            if key not in entities:
                entities[key] = Entity(text=ent_text, label=label, source="spacy_ner_en")
        
        return list(entities.values())
