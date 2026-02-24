"""
Trello Sync Service
-------------------
FastAPI app with APScheduler running sync every N minutes.

Start:  uvicorn main:app --host 0.0.0.0 --port 8891
Health: GET /health
Manual: POST /sync
Logs:   GET /sync/history
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException

from config import settings
from db import get_conn
from sync import run_sync

# Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress httpx request logs — they leak API key and token in URLs
logging.getLogger("httpx").setLevel(logging.WARNING)

# Scheduler
scheduler = BackgroundScheduler()


def scheduled_sync():
    """Wrapper for scheduled execution."""
    try:
        run_sync()
    except Exception as e:
        logger.error(f"Scheduled sync failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start scheduler on startup, shut down on exit."""
    scheduler.add_job(
        scheduled_sync,
        "interval",
        minutes=settings.sync_interval_minutes,
        id="trello_sync",
        next_run_time=datetime.now(timezone.utc),  # run immediately on start
    )
    scheduler.start()
    logger.info(f"Scheduler started: sync every {settings.sync_interval_minutes} min")
    yield
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="Trello Sync Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """Health check."""
    job = scheduler.get_job("trello_sync")
    return {
        "status": "ok",
        "next_sync": str(job.next_run_time) if job else None,
        "interval_minutes": settings.sync_interval_minutes,
    }


@app.post("/sync")
async def trigger_sync():
    """Manually trigger a full sync."""
    try:
        result = run_sync()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sync/history")
async def sync_history(limit: int = 10):
    """Get recent sync log entries."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, started_at, finished_at, status, boards_synced,
                   cards_synced, error_message
            FROM trello.sync_log
            ORDER BY started_at DESC
            LIMIT %s
        """, (limit,))
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    return rows


@app.get("/boards")
async def list_boards():
    """List all synced boards."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT b.name, b.url, b.closed,
                   COUNT(c.id) FILTER (WHERE NOT c.closed) AS open_cards
            FROM trello.boards b
            LEFT JOIN trello.cards c ON c.board_id = b.id
            WHERE NOT b.closed
            GROUP BY b.id
            ORDER BY b.name
        """)
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


@app.get("/boards/{board_name}/cards")
async def board_cards(board_name: str, list_name: str = None, include_closed: bool = False):
    """Get cards for a board, optionally filtered by list name."""
    with get_conn() as conn:
        cur = conn.cursor()
        query = """
            SELECT card_name, list_name, labels, members, due, due_complete,
                   description, url, last_activity
            FROM trello.v_cards
            WHERE board_name ILIKE %s
        """
        params = [f"%{board_name}%"]

        if not include_closed:
            query += " AND NOT closed"
        if list_name:
            query += " AND list_name ILIKE %s"
            params.append(f"%{list_name}%")

        query += " ORDER BY position"
        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
