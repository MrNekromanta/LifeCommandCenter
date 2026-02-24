# Trello Sync Service

Syncs **all** your Trello boards to local Postgres. Runs as a FastAPI service with scheduled sync every 60 minutes.

## Architecture

```
Trello (GUI) ──sync every 60min──▶ Postgres (trello schema) ──MCP──▶ Claude
                                          ▲
                                   FastAPI service
                                   (port 8891)
```

## Setup (SER9)

### 1. Trello API credentials

1. Go to https://trello.com/power-ups/admin
2. Click "New" → create a Power-Up (name: "Sync Engine")
3. Copy the **API Key**
4. Generate a **Token**: visit this URL (replace YOUR_KEY):
   ```
   https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&key=YOUR_KEY
   ```
5. Copy the token

### 2. Database

```powershell
createdb trello_sync
psql -d trello_sync -f schema.sql
```

### 3. Environment

```powershell
cp .env.example .env
# Edit .env with your Trello API key, token, and DB connection string
```

### 4. Install & run

```powershell
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8891
```

Or as a background service (Windows):
```powershell
# Using pythonw for background execution
Start-Process pythonw -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8891"
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Status + next sync time |
| POST | `/sync` | Manual trigger (immediate full sync) |
| GET | `/sync/history` | Recent sync logs |
| GET | `/boards` | All synced boards with card counts |
| GET | `/boards/{name}/cards` | Cards for a board (filter: `?list_name=...`) |

## Postgres MCP (for Claude Desktop)

Add to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "trello-db": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://postgres:postgres@localhost:5432/trello_sync"
      ]
    }
  }
}
```

### Useful queries for Claude

```sql
-- All open cards across all boards
SELECT board_name, list_name, card_name, labels, due
FROM trello.v_cards WHERE NOT closed ORDER BY board_name, list_name;

-- BiznesValidator board specifically
SELECT list_name, card_name, labels, due
FROM trello.v_cards
WHERE board_name ILIKE '%biznes%' AND NOT closed
ORDER BY list_name, position;

-- Board summary
SELECT * FROM trello.v_board_summary;

-- Last sync status
SELECT * FROM trello.sync_log ORDER BY started_at DESC LIMIT 1;
```

## Sync behavior

- Runs every 60 minutes (configurable via `SYNC_INTERVAL_MINUTES`)
- First sync runs immediately on service start
- Full upsert: creates new items, updates existing, preserves local IDs
- Sync log tracks every run with timing and error details
- Cards in unknown lists are skipped with a warning
