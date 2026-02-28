"""
GraphStore — loads production_cache and provides query primitives.

Zero ML dependencies. Pure Python + networkx.
"""
import json
import os
import re
import logging
from collections import defaultdict
from typing import Optional

import networkx as nx


def _camel_split(s: str) -> list[str]:
    """Split CamelCase, snake_case, kebab-case, slash-separated into tokens.
    
    'BiznesValidator'      → ['biznes', 'validator']
    'E²GraphRAG Pipeline'  → ['e²graph', 'rag', 'pipeline']
    'Wiki RAG Baremetal'   → ['wiki', 'rag', 'baremetal']
    'leaf_42'              → ['leaf', '42']
    """
    # First split on spaces, underscores, hyphens, slashes, //
    parts = re.split(r'[\s_\-/]+', s)
    tokens = []
    for part in parts:
        # Split CamelCase: insert boundary before uppercase runs
        sub = re.sub(r'([a-zżźćńółęąś])([A-ZŻŹĆŃÓŁĘĄŚ])', r'\1 \2', part)
        # Split runs of uppercase followed by lowercase: 'RAGPipeline' → 'RAG Pipeline'
        sub = re.sub(r'([A-ZŻŹĆŃÓŁĘĄŚ]+)([A-ZŻŹĆŃÓŁĘĄŚ][a-zżźćńółęąś])', r'\1 \2', sub)
        tokens.extend(sub.split())
    return [t.lower() for t in tokens if t]


def _trigrams(s: str) -> set[str]:
    """Generate character trigrams for fuzzy matching."""
    s = s.lower()
    if len(s) < 3:
        return {s}
    return {s[i:i+3] for i in range(len(s) - 2)}


def _trigram_similarity(a: str, b: str) -> float:
    """Jaccard similarity on trigrams. Returns 0.0-1.0."""
    ta, tb = _trigrams(a), _trigrams(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

logger = logging.getLogger(__name__)


class GraphStore:
    """In-memory store for E²GraphRAG production cache."""

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self._load(cache_dir)
        logger.info(
            "GraphStore ready: %d nodes, %d edges, %d entities, %d leaves, %d summaries",
            self.graph.number_of_nodes(),
            self.graph.number_of_edges(),
            len(self.index),
            self.n_leaves,
            self.n_summaries,
        )

    # ── Loading ──────────────────────────────────────────────

    def _load(self, d: str):
        with open(os.path.join(d, "tree.json"), encoding="utf-8") as f:
            self.tree: dict = json.load(f)

        with open(os.path.join(d, "index_LCC_Hybrid.json"), encoding="utf-8") as f:
            self.index: dict[str, list[str]] = json.load(f)

        with open(os.path.join(d, "appearance_count_LCC_Hybrid.json"), encoding="utf-8") as f:
            self.appearance: dict[str, dict[str, int]] = json.load(f)

        with open(os.path.join(d, "graph_LCC_Hybrid.json"), encoding="utf-8") as f:
            edges = json.load(f)

        self.graph = self._build_graph(edges)

        with open(os.path.join(d, "chunk_metadata.json"), encoding="utf-8") as f:
            meta_list = json.load(f)
        self.chunk_meta: dict[str, dict] = {}
        for i, item in enumerate(meta_list):
            key = f"leaf_{i}"
            self.chunk_meta[key] = item

        # Pre-compute entity list (lowercased → original) + tokenized forms
        self.entity_lc: dict[str, str] = {}
        self.entity_tokens: dict[str, set[str]] = {}  # lowercased entity → set of tokens
        for ent in self.index:
            lc = ent.lower()
            self.entity_lc[lc] = ent
            self.entity_tokens[lc] = set(_camel_split(ent))

        # Build inverse index: chunk_id → [entities]
        self.inverse_index: dict[str, list[str]] = defaultdict(list)
        for ent, chunk_ids in self.index.items():
            for cid in chunk_ids:
                self.inverse_index[cid].append(ent)

        self.n_leaves = sum(1 for k in self.tree if k.startswith("leaf_"))
        self.n_summaries = sum(1 for k in self.tree if k.startswith("summary_"))

    @staticmethod
    def _build_graph(edges: list) -> nx.Graph:
        G = nx.Graph()
        edge_weights: dict[tuple, int] = {}
        for n1, n2, w in edges:
            key = tuple(sorted([n1, n2]))
            edge_weights[key] = edge_weights.get(key, 0) + w
        for (n1, n2), w in edge_weights.items():
            G.add_edge(n1, n2, weight=w)
        return G

    # ── Tool 1: search_entities ──────────────────────────────

    def search_entities(self, query: str, limit: int = 20) -> list[dict]:
        """Fuzzy search over entity names. Returns matches sorted by relevance.
        
        Scoring tiers:
        100 — exact match
         80 — query is substring of entity (or vice versa)
         60 — all query tokens found in entity tokens (CamelCase-aware)
         50 — partial token overlap
         30 — partial substring match in any token
         20 — trigram similarity fallback (>0.3 threshold)
        """
        q_lower = query.lower()
        q_tokens = set(_camel_split(query))
        results = []

        for ent_lc, ent_original in self.entity_lc.items():
            ent_tokens = self.entity_tokens[ent_lc]
            score = 0

            if q_lower == ent_lc:
                score = 100
            elif q_lower in ent_lc:
                score = 80
            elif ent_lc in q_lower:
                # Penalize very short entities matching long queries
                # "Biznes" in "biznes validator" should score lower than full token match
                if len(ent_lc) < len(q_lower) * 0.6:
                    score = 45
                else:
                    score = 70
            else:
                # Token-level matching (CamelCase-aware)
                overlap = q_tokens & ent_tokens
                if overlap:
                    if q_tokens == ent_tokens:
                        # Perfect token match: "biznes validator" ↔ "BiznesValidator"
                        score = 75
                    elif q_tokens <= ent_tokens:
                        # All query tokens present in entity
                        score = 60
                    elif ent_tokens <= q_tokens:
                        # Entity is subset of query
                        score = 55
                    else:
                        score = 50 * len(overlap) / max(len(q_tokens), len(ent_tokens))
                else:
                    # Partial substring in any token
                    for qt in q_tokens:
                        if len(qt) >= 3:
                            for et in ent_tokens:
                                if qt in et:
                                    score = max(score, 30)
                                elif et in qt:
                                    score = max(score, 25)

                    # Trigram similarity fallback
                    if score == 0:
                        sim = _trigram_similarity(q_lower, ent_lc)
                        if sim > 0.3:
                            score = round(20 * sim / 0.3, 1)  # 20-ish for decent matches

            if score > 0:
                chunk_count = len(self.index.get(ent_original, []))
                neighbor_count = self.graph.degree(ent_original) if ent_original in self.graph else 0
                results.append({
                    "entity": ent_original,
                    "score": round(score, 1),
                    "chunk_count": chunk_count,
                    "graph_connections": neighbor_count,
                })

        results.sort(key=lambda x: (-x["score"], -x["chunk_count"]))
        return results[:limit]

    # ── Tool 2: get_entity_context ───────────────────────────

    def get_entity_context(self, entity: str) -> Optional[dict]:
        """For an entity: graph neighbors, chunks where it appears, co-occurrence strength."""
        # Resolve case-insensitive
        canonical = self.entity_lc.get(entity.lower())
        if not canonical:
            return None

        # Graph neighbors sorted by edge weight
        neighbors = []
        if canonical in self.graph:
            for nb in self.graph.neighbors(canonical):
                w = self.graph[canonical][nb].get("weight", 1)
                neighbors.append({"entity": nb, "weight": w})
            neighbors.sort(key=lambda x: -x["weight"])

        # Chunks
        chunk_ids = self.index.get(canonical, [])

        # Chunk details with source info
        chunks_info = []
        for cid in chunk_ids:
            info = {"chunk_id": cid}
            if cid in self.chunk_meta:
                info["source"] = self.chunk_meta[cid]["source"]
            count = self.appearance.get(cid, {}).get(canonical, 0)
            if count:
                info["mentions"] = count
            chunks_info.append(info)

        return {
            "entity": canonical,
            "graph_neighbors": neighbors[:30],
            "total_neighbors": len(neighbors),
            "chunks": chunks_info,
            "total_chunks": len(chunks_info),
        }

    # ── Tool 3: get_chunk ────────────────────────────────────

    def get_chunk(self, chunk_id: str) -> Optional[dict]:
        """Return text of a specific chunk or summary node."""
        node = self.tree.get(chunk_id)
        if not node:
            return None
        result = {
            "chunk_id": chunk_id,
            "text": node["text"],
        }
        # Add entities present in this chunk
        if chunk_id in self.inverse_index:
            result["entities"] = self.inverse_index[chunk_id]
        # Add source metadata for leaf nodes
        if chunk_id in self.chunk_meta:
            result["source"] = self.chunk_meta[chunk_id]["source"]
        return result

    # ── Tool 4: get_chunk_metadata ───────────────────────────

    def get_chunk_metadata(self, chunk_id: str) -> Optional[dict]:
        """Return structural metadata: parent, children, source file."""
        node = self.tree.get(chunk_id)
        if not node:
            return None
        result = {
            "chunk_id": chunk_id,
            "parent": node.get("parent"),
            "children": node.get("children"),
            "has_text": bool(node.get("text")),
            "text_length": len(node.get("text", "")),
        }
        if chunk_id in self.chunk_meta:
            result["source"] = self.chunk_meta[chunk_id]["source"]
            result["chunk_index"] = self.chunk_meta[chunk_id]["chunk_index"]
            result["total_chunks_in_source"] = self.chunk_meta[chunk_id]["total_chunks"]
        # Entities in this chunk
        if chunk_id in self.inverse_index:
            result["entities"] = self.inverse_index[chunk_id]
            result["entity_count"] = len(self.inverse_index[chunk_id])
        return result

    # ── Tool 5: query_subgraph ───────────────────────────────

    def query_subgraph(
        self, entities: list[str], max_hops: int = 3, max_chunks: int = 25
    ) -> dict:
        """
        Find shortest paths between entities in the graph.
        Return chunks where path entities co-occur.
        """
        # Resolve entities to canonical names
        resolved = []
        unresolved = []
        for e in entities:
            canonical = self.entity_lc.get(e.lower())
            if canonical and canonical in self.graph:
                resolved.append(canonical)
            else:
                unresolved.append(e)

        if len(resolved) < 2:
            # Fallback: return chunks for each individual entity
            all_chunks = set()
            for e in resolved:
                all_chunks.update(self.index.get(e, []))
            chunk_list = sorted(all_chunks)[:max_chunks]
            return {
                "resolved_entities": resolved,
                "unresolved_entities": unresolved,
                "strategy": "individual_lookup",
                "paths": [],
                "chunks": chunk_list,
                "chunk_count": len(chunk_list),
            }

        # Find shortest paths between all pairs
        from itertools import combinations

        paths_found = []
        path_entities = set(resolved)

        for e1, e2 in combinations(resolved, 2):
            try:
                path = nx.shortest_path(self.graph, e1, e2)
                if len(path) - 1 <= max_hops:
                    paths_found.append({
                        "from": e1,
                        "to": e2,
                        "hops": len(path) - 1,
                        "path": path,
                    })
                    path_entities.update(path)
            except nx.NetworkXNoPath:
                paths_found.append({
                    "from": e1,
                    "to": e2,
                    "hops": -1,
                    "path": [],
                    "note": "no path exists",
                })

        # Collect chunks: prefer chunks where multiple path entities co-occur
        chunk_scores: dict[str, int] = defaultdict(int)
        for ent in path_entities:
            for cid in self.index.get(ent, []):
                chunk_scores[cid] += 1

        # Sort by entity overlap count (descending), then by chunk_id
        ranked_chunks = sorted(
            chunk_scores.items(), key=lambda x: (-x[1], x[0])
        )[:max_chunks]

        return {
            "resolved_entities": resolved,
            "unresolved_entities": unresolved,
            "strategy": "subgraph_paths",
            "paths": paths_found,
            "path_entities": sorted(path_entities),
            "chunks": [{"chunk_id": cid, "entity_overlap": score} for cid, score in ranked_chunks],
            "chunk_count": len(ranked_chunks),
        }

    # ── Utility: stats ───────────────────────────────────────

    def stats(self) -> dict:
        """Return store statistics."""
        sources = set()
        for meta in self.chunk_meta.values():
            sources.add(meta["source"])
        return {
            "graph_nodes": self.graph.number_of_nodes(),
            "graph_edges": self.graph.number_of_edges(),
            "entities": len(self.index),
            "leaves": self.n_leaves,
            "summaries": self.n_summaries,
            "sources": sorted(sources),
            "source_count": len(sources),
        }
