"""
LCC Tree Builder — summary tree via Claude API.

Replaces E²GraphRAG's build_tree.py which requires local LLM (Qwen2.5-7B on GPU).
Uses Claude Haiku 4.5 for cost efficiency (~$1/1M input, ~$5/1M output).

Tree structure (same as original):
- leaf_{i}: original chunks
- summary_0_{j}: first-level summaries (merge_num chunks each)
- summary_1_{k}: second-level summaries (merge_num summaries each)
- ... continues until <=1.2*merge_num nodes remain
"""
import os
import json
import time
import logging
from typing import List
from anthropic import Anthropic
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load API key
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'hybrid-extractor', '.env'))

# Prompts adapted for our use case (multi-project knowledge base, PL/EN mix)
SUMMARIZE_LEAF_PROMPT = """Summarize the following content from a personal knowledge base.
Focus on: key entities (projects, tools, people), decisions made, relationships between concepts.
Keep technical terms and project names intact. Write in the same language as the content.
Length: ~300 words.

Content:
{content}

Summary:"""

SUMMARIZE_SUMMARY_PROMPT = """Further summarize these summaries from a personal knowledge base.
Preserve: project names, tool names, key decisions, relationships between concepts.
Merge overlapping information. Write in the same language as the content.
Length: ~300 words.

Summaries:
{summary}

Consolidated summary:"""


class ClaudeTreeBuilder:
    """Build E²GraphRAG summary tree using Claude API."""
    
    def __init__(self, model="claude-haiku-4-5-20251001", max_tokens=1024):
        self.client = Anthropic()
        self.model = model
        self.max_tokens = max_tokens
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
    
    def _call_claude(self, prompt: str) -> str:
        """Single Claude API call with token tracking."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens
        self.call_count += 1
        return response.content[0].text
    
    def summarize_leaf(self, text: str) -> str:
        """Summarize merged leaf chunks."""
        prompt = SUMMARIZE_LEAF_PROMPT.format(content=text)
        return self._call_claude(prompt)
    
    def summarize_summary(self, text: str) -> str:
        """Summarize merged summaries."""
        prompt = SUMMARIZE_SUMMARY_PROMPT.format(summary=text)
        return self._call_claude(prompt)
    
    def build_tree(self, text_chunks: List[str], cache_folder: str,
                   merge_num: int = 5, overlap: int = 100) -> dict:
        """Build hierarchical summary tree from text chunks.
        
        Args:
            text_chunks: List of text chunks (already split)
            cache_folder: Path to save tree.json cache
            merge_num: How many chunks to merge per summary
            overlap: Token overlap between chunks (for merging display)
        
        Returns:
            Tree cache dict with leaf_*, summary_*_* nodes
        """
        cache_path = os.path.join(cache_folder, "tree.json")
        if os.path.exists(cache_path):
            logger.info("Loading cached tree...")
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        start_time = time.time()
        cache = {}
        
        # Create leaf nodes
        for i, chunk in enumerate(text_chunks):
            cache[f"leaf_{i}"] = {
                "text": chunk,
                "children": None,
                "parent": None,
            }
        
        # Level 0: summarize groups of merge_num leaves
        summary_count = 0
        for i in range(0, len(text_chunks), merge_num):
            group = text_chunks[i:i + merge_num]
            merged_text = "\n\n---\n\n".join(group)
            
            logger.info(f"Summarizing leaves {i}-{i+len(group)-1}...")
            summary = self.summarize_leaf(merged_text)
            
            children = [f"leaf_{j}" for j in range(i, min(i + merge_num, len(text_chunks)))]
            cache[f"summary_0_{summary_count}"] = {
                "text": summary,
                "children": children,
                "parent": [],
            }
            for child_id in children:
                cache[child_id]["parent"] = f"summary_0_{summary_count}"
            summary_count += 1
        
        # Higher levels: summarize summaries until small enough
        level = 1
        to_summarize_ids = [f"summary_0_{i}" for i in range(summary_count)]
        
        while len(to_summarize_ids) > 1.2 * merge_num:
            new_count = 0
            texts = [cache[sid]["text"] for sid in to_summarize_ids]
            
            for i in range(0, len(texts), merge_num):
                group = texts[i:i + merge_num]
                merged_text = "\n\n---\n\n".join(group)
                
                logger.info(f"Summarizing level {level}, group {new_count}...")
                summary = self.summarize_summary(merged_text)
                
                children = to_summarize_ids[i:i + merge_num]
                cache[f"summary_{level}_{new_count}"] = {
                    "text": summary,
                    "children": children,
                    "parent": [],
                }
                for child_id in children:
                    cache[child_id]["parent"] = f"summary_{level}_{new_count}"
                new_count += 1
            
            to_summarize_ids = [f"summary_{level}_{i}" for i in range(new_count)]
            level += 1
        
        # Save cache
        os.makedirs(cache_folder, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        
        elapsed = time.time() - start_time
        logger.info(f"Tree built in {elapsed:.1f}s | {self.call_count} API calls | "
                    f"{self.total_input_tokens} in + {self.total_output_tokens} out tokens")
        
        return cache

    def cost_estimate_pln(self) -> float:
        """Estimate cost in PLN (Haiku 4.5: $1/1M in, $5/1M out)."""
        usd = (self.total_input_tokens * 1.0 + self.total_output_tokens * 5.0) / 1_000_000
        return usd * 4.0  # ~4 PLN/USD


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    builder = ClaudeTreeBuilder()
    
    test_chunks = [
        "LifeCommandCenter to system do zarządzania taskami i wiedzą. Łączy Trello z Claude.",
        "BiznesValidator to SaaS do walidacji pomysłów biznesowych. Używa Next.js i Supabase.",
        "E²GraphRAG buduje graf encji i summary tree do cross-project knowledge retrieval.",
    ]
    
    cache_dir = os.path.join(os.path.dirname(__file__), "cache", "test_lcc")
    cache = builder.build_tree(test_chunks, cache_dir, merge_num=3)
    print(f"\nTree nodes: {len(cache)}")
    print(f"API calls: {builder.call_count}")
    print(f"Cost: {builder.cost_estimate_pln():.4f} PLN")
    for key in sorted(cache.keys()):
        text_preview = cache[key]["text"][:80] + "..." if len(cache[key]["text"]) > 80 else cache[key]["text"]
        print(f"  {key}: {text_preview}")
