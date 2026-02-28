# RAG MCP Server — LifeCommandCenter

MCP server exposing E²GraphRAG knowledge graph to Claude.
Zero ML dependencies. Startup < 200ms, RAM ~50MB.

## Stats
- 1308 entities, 32K+ edges
- 171 chunks (leaves) + 87 summaries
- 9 source audit files

## Tools

| Tool | Purpose |
|------|---------|
| `search_entities(query)` | Fuzzy search across entity names |
| `get_entity_context(entity)` | Graph neighbors + chunk locations |
| `get_chunk(chunk_id)` | Full text of a chunk/summary |
| `get_chunk_metadata(chunk_id)` | Parent, children, source file |
| `query_subgraph(entities)` | Shortest paths → ranked chunks |
| `rag_stats()` | Graph statistics |

## Setup

```powershell
cd c:\projects\AI\LifeCommandCenter\rag-mcp
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Claude Desktop Config

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lcc-rag": {
      "command": "c:\\projects\\AI\\LifeCommandCenter\\rag-mcp\\.venv\\Scripts\\python.exe",
      "args": ["c:\\projects\\AI\\LifeCommandCenter\\rag-mcp\\server.py"]
    }
  }
}
```

## Test

```powershell
.venv\Scripts\python test_smoke.py
```
