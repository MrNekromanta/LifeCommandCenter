"""
RAG MCP Server — exposes E²GraphRAG production cache to Claude.

5 tools for structured graph + chunk access.
Zero ML dependencies.
"""
import os
import json
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from graph_store import GraphStore

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("rag-mcp")

CACHE_DIR = os.environ.get(
    "RAG_CACHE_DIR",
    os.path.join(os.path.dirname(__file__), "..", "e2graphrag", "production_cache"),
)

mcp = FastMCP(
    "LifeCommandCenter RAG",
    instructions="Query Krzysiek's knowledge graph: 9 project audits, 1308 entities, 171 chunks.",
)

# Load store at import time (server startup)
store: GraphStore | None = None


def _get_store() -> GraphStore:
    global store
    if store is None:
        logger.info("Loading GraphStore from %s", CACHE_DIR)
        store = GraphStore(CACHE_DIR)
    return store


@mcp.tool()
def search_entities(query: str, limit: int = 20) -> str:
    """Search for entities (projects, tools, people, concepts) in the knowledge graph.
    
    Use this as the FIRST step when answering questions about Krzysiek's projects.
    Returns matching entities with relevance score and connection counts.
    
    Args:
        query: Search term (entity name, project name, technology, etc.)
        limit: Max results to return (default 20)
    """
    s = _get_store()
    results = s.search_entities(query, limit)
    if not results:
        return json.dumps({"matches": [], "hint": "No entities matched. Try broader terms or check spelling."})
    return json.dumps({"matches": results, "total": len(results)}, ensure_ascii=False)


@mcp.tool()
def get_entity_context(entity: str) -> str:
    """Get full context for a specific entity: graph neighbors and chunks where it appears.
    
    Use AFTER search_entities to drill into a specific entity.
    Returns connected entities (sorted by weight) and chunk locations.
    
    Args:
        entity: Exact entity name (use search_entities first to find correct spelling)
    """
    s = _get_store()
    result = s.get_entity_context(entity)
    if not result:
        # Try fuzzy match as fallback
        matches = s.search_entities(entity, limit=3)
        return json.dumps({
            "error": f"Entity '{entity}' not found.",
            "did_you_mean": [m["entity"] for m in matches],
        }, ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_chunk(chunk_id: str) -> str:
    """Retrieve the full text of a specific chunk or summary node.
    
    Chunk IDs look like 'leaf_0', 'leaf_170', 'summary_0_0', etc.
    Leaf nodes contain raw audit text. Summary nodes contain aggregated summaries.
    
    Args:
        chunk_id: Node ID from the tree (e.g. 'leaf_42', 'summary_1_3')
    """
    s = _get_store()
    result = s.get_chunk(chunk_id)
    if not result:
        return json.dumps({"error": f"Chunk '{chunk_id}' not found. Valid range: leaf_0..leaf_{s.n_leaves-1}, plus summary nodes."})
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def get_chunk_metadata(chunk_id: str) -> str:
    """Get structural metadata for a chunk: parent, children, source file, entity list.
    
    Use to understand where a chunk fits in the document hierarchy
    and which source audit file it came from.
    
    Args:
        chunk_id: Node ID from the tree
    """
    s = _get_store()
    result = s.get_chunk_metadata(chunk_id)
    if not result:
        return json.dumps({"error": f"Chunk '{chunk_id}' not found."})
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def query_subgraph(entities: list[str], max_hops: int = 3, max_chunks: int = 25) -> str:
    """Find connections between multiple entities via graph shortest paths.
    
    This is the POWER tool for cross-project queries. Given 2+ entities,
    finds shortest paths between them in the knowledge graph and returns
    chunks where path entities co-occur (ranked by overlap count).
    
    Args:
        entities: List of entity names to connect (minimum 2)
        max_hops: Maximum path length between entities (default 3)
        max_chunks: Maximum chunks to return (default 25)
    """
    s = _get_store()
    result = s.query_subgraph(entities, max_hops, max_chunks)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def rag_stats() -> str:
    """Get knowledge graph statistics: node/edge counts, source files, entity count."""
    s = _get_store()
    return json.dumps(s.stats(), ensure_ascii=False)


if __name__ == "__main__":
    _get_store()  # Pre-load on startup
    mcp.run(transport="stdio")
