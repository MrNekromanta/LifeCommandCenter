"""
LCC Extractor Adapter — wraps HybridExtractor for E²GraphRAG compatibility.

E²GraphRAG expects naive_extract_graph() to return:
{
    "nouns": list[str],           # all entities found
    "cooccurrence": dict,         # {(e1,e2): count} pairs within chunk
    "double_nouns": dict,         # multi-word name mappings
    "appearance_count": dict      # {entity: count}
}

Our HybridExtractor returns: list[Entity(text, label)]
This adapter bridges the gap.
"""
import sys
import os
from itertools import combinations

# Add hybrid-extractor to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hybrid-extractor'))

from hybrid_extractor import HybridExtractor
from extract_graph import Extractor


class LCCExtractor(Extractor):
    """Adapter: HybridExtractor → E²GraphRAG Extractor interface."""
    
    def __init__(self, language="pl", enable_llm=False):
        self.language = language
        self.method = "LCC_Hybrid"
        self.hybrid = HybridExtractor(enable_llm=enable_llm)
    
    def load_model(self, language):
        # Model loading handled by HybridExtractor
        return None
    
    def naive_extract_graph(self, text: str) -> dict:
        """Extract entities and build co-occurrence graph from a single chunk."""
        # Get entities from HybridExtractor
        entities = self.hybrid.extract(text)
        
        # Build entity list (deduplicated by text)
        entity_texts = []
        seen = set()
        for ent in entities:
            key = ent.text.lower()
            if key not in seen:
                entity_texts.append(ent.text)
                seen.add(key)
        
        # Build appearance count (each entity appears once per chunk call)
        appearance_count = {}
        for ent_text in entity_texts:
            appearance_count[ent_text] = appearance_count.get(ent_text, 0) + 1
        
        # Build co-occurrence pairs (all entities in same chunk co-occur)
        cooccurrence = {}
        for i in range(len(entity_texts)):
            for j in range(i + 1, len(entity_texts)):
                pair = tuple(sorted([entity_texts[i], entity_texts[j]]))
                cooccurrence[pair] = cooccurrence.get(pair, 0) + 1
        
        # Double nouns: multi-word entities (for person name handling)
        double_nouns = {}
        for ent in entities:
            parts = ent.text.split()
            if len(parts) >= 2:
                for part in parts:
                    double_nouns[part] = parts
        
        return {
            "nouns": entity_texts,
            "cooccurrence": cooccurrence,
            "double_nouns": double_nouns,
            "appearance_count": appearance_count,
        }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("Testing LCCExtractor adapter...")
    ext = LCCExtractor(enable_llm=False)
    
    test_chunk = """LifeCommandCenter to cross-projektowy system łączący Trello z Claude 
    przez Postgres i n8n. Krzysiek pracuje nad BiznesValidator jako side project. 
    System używa E²GraphRAG do knowledge retrieval."""
    
    result = ext.naive_extract_graph(test_chunk)
    print(f"\nNouns ({len(result['nouns'])}): {result['nouns']}")
    print(f"Co-occurrence pairs: {len(result['cooccurrence'])}")
    print(f"Appearance count: {result['appearance_count']}")
    print(f"Double nouns: {result['double_nouns']}")
