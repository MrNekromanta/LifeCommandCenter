"""Database connection and upsert operations."""

import logging
from contextlib import contextmanager
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

from config import settings

logger = logging.getLogger(__name__)


@contextmanager
def get_conn():
    """Context manager for database connections."""
    conn = psycopg2.connect(settings.database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def upsert_board(cur, board: dict) -> int:
    """Upsert a Trello board. Returns local id."""
    cur.execute("""
        INSERT INTO trello.boards (trello_id, name, description, url, closed, last_activity, synced_at)
        VALUES (%(trello_id)s, %(name)s, %(desc)s, %(url)s, %(closed)s, %(last_activity)s, NOW())
        ON CONFLICT (trello_id) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            url = EXCLUDED.url,
            closed = EXCLUDED.closed,
            last_activity = EXCLUDED.last_activity,
            synced_at = NOW()
        RETURNING id
    """, {
        "trello_id": board["id"],
        "name": board["name"],
        "desc": board.get("desc", ""),
        "url": board.get("url", ""),
        "closed": board.get("closed", False),
        "last_activity": board.get("dateLastActivity"),
    })
    return cur.fetchone()[0]


def upsert_list(cur, lst: dict, board_id: int) -> int:
    """Upsert a Trello list. Returns local id."""
    cur.execute("""
        INSERT INTO trello.lists (trello_id, board_id, name, position, closed, synced_at)
        VALUES (%(trello_id)s, %(board_id)s, %(name)s, %(pos)s, %(closed)s, NOW())
        ON CONFLICT (trello_id) DO UPDATE SET
            board_id = EXCLUDED.board_id,
            name = EXCLUDED.name,
            position = EXCLUDED.position,
            closed = EXCLUDED.closed,
            synced_at = NOW()
        RETURNING id
    """, {
        "trello_id": lst["id"],
        "board_id": board_id,
        "name": lst["name"],
        "pos": lst.get("pos"),
        "closed": lst.get("closed", False),
    })
    return cur.fetchone()[0]


def upsert_label(cur, label: dict, board_id: int) -> int:
    """Upsert a Trello label. Returns local id."""
    cur.execute("""
        INSERT INTO trello.labels (trello_id, board_id, name, color, synced_at)
        VALUES (%(trello_id)s, %(board_id)s, %(name)s, %(color)s, NOW())
        ON CONFLICT (trello_id) DO UPDATE SET
            board_id = EXCLUDED.board_id,
            name = EXCLUDED.name,
            color = EXCLUDED.color,
            synced_at = NOW()
        RETURNING id
    """, {
        "trello_id": label["id"],
        "board_id": board_id,
        "name": label.get("name", ""),
        "color": label.get("color"),
    })
    return cur.fetchone()[0]


def upsert_member(cur, member: dict) -> int:
    """Upsert a Trello member. Returns local id."""
    cur.execute("""
        INSERT INTO trello.members (trello_id, username, full_name, avatar_url, synced_at)
        VALUES (%(trello_id)s, %(username)s, %(full_name)s, %(avatar_url)s, NOW())
        ON CONFLICT (trello_id) DO UPDATE SET
            username = EXCLUDED.username,
            full_name = EXCLUDED.full_name,
            avatar_url = EXCLUDED.avatar_url,
            synced_at = NOW()
        RETURNING id
    """, {
        "trello_id": member["id"],
        "username": member.get("username", ""),
        "full_name": member.get("fullName", ""),
        "avatar_url": member.get("avatarUrl"),
    })
    return cur.fetchone()[0]


def upsert_card(cur, card: dict, board_id: int, list_id: int) -> int:
    """Upsert a Trello card. Returns local id."""
    cur.execute("""
        INSERT INTO trello.cards
            (trello_id, board_id, list_id, name, description, position,
             url, due, due_complete, closed, last_activity, synced_at)
        VALUES
            (%(trello_id)s, %(board_id)s, %(list_id)s, %(name)s, %(desc)s, %(pos)s,
             %(url)s, %(due)s, %(due_complete)s, %(closed)s, %(last_activity)s, NOW())
        ON CONFLICT (trello_id) DO UPDATE SET
            board_id = EXCLUDED.board_id,
            list_id = EXCLUDED.list_id,
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            position = EXCLUDED.position,
            url = EXCLUDED.url,
            due = EXCLUDED.due,
            due_complete = EXCLUDED.due_complete,
            closed = EXCLUDED.closed,
            last_activity = EXCLUDED.last_activity,
            synced_at = NOW()
        RETURNING id
    """, {
        "trello_id": card["id"],
        "board_id": board_id,
        "list_id": list_id,
        "name": card["name"],
        "desc": card.get("desc", ""),
        "pos": card.get("pos"),
        "url": card.get("url", ""),
        "due": card.get("due"),
        "due_complete": card.get("dueComplete", False),
        "closed": card.get("closed", False),
        "last_activity": card.get("dateLastActivity"),
    })
    return cur.fetchone()[0]


def sync_card_labels(cur, card_id: int, label_trello_ids: list[str]):
    """Replace card-label associations."""
    cur.execute("DELETE FROM trello.card_labels WHERE card_id = %s", (card_id,))
    for trello_id in label_trello_ids:
        cur.execute("""
            INSERT INTO trello.card_labels (card_id, label_id)
            SELECT %s, id FROM trello.labels WHERE trello_id = %s
            ON CONFLICT DO NOTHING
        """, (card_id, trello_id))


def sync_card_members(cur, card_id: int, member_trello_ids: list[str]):
    """Replace card-member associations."""
    cur.execute("DELETE FROM trello.card_members WHERE card_id = %s", (card_id,))
    for trello_id in member_trello_ids:
        cur.execute("""
            INSERT INTO trello.card_members (card_id, member_id)
            SELECT %s, id FROM trello.members WHERE trello_id = %s
            ON CONFLICT DO NOTHING
        """, (card_id, trello_id))


def upsert_checklist(cur, checklist: dict, card_id: int) -> int:
    """Upsert a Trello checklist. Returns local id."""
    cur.execute("""
        INSERT INTO trello.checklists (trello_id, card_id, name, position, synced_at)
        VALUES (%(trello_id)s, %(card_id)s, %(name)s, %(pos)s, NOW())
        ON CONFLICT (trello_id) DO UPDATE SET
            card_id = EXCLUDED.card_id,
            name = EXCLUDED.name,
            position = EXCLUDED.position,
            synced_at = NOW()
        RETURNING id
    """, {
        "trello_id": checklist["id"],
        "card_id": card_id,
        "name": checklist["name"],
        "pos": checklist.get("pos"),
    })
    return cur.fetchone()[0]


def upsert_checklist_item(cur, item: dict, checklist_id: int) -> int:
    """Upsert a checklist item. Returns local id."""
    cur.execute("""
        INSERT INTO trello.checklist_items
            (trello_id, checklist_id, name, state, position, due, synced_at)
        VALUES
            (%(trello_id)s, %(checklist_id)s, %(name)s, %(state)s, %(pos)s, %(due)s, NOW())
        ON CONFLICT (trello_id) DO UPDATE SET
            checklist_id = EXCLUDED.checklist_id,
            name = EXCLUDED.name,
            state = EXCLUDED.state,
            position = EXCLUDED.position,
            due = EXCLUDED.due,
            synced_at = NOW()
        RETURNING id
    """, {
        "trello_id": item["id"],
        "checklist_id": checklist_id,
        "name": item["name"],
        "state": item.get("state", "incomplete"),
        "pos": item.get("pos"),
        "due": item.get("due"),
    })
    return cur.fetchone()[0]


def log_sync_start(cur) -> int:
    """Create sync log entry. Returns log id."""
    cur.execute("""
        INSERT INTO trello.sync_log (started_at, status)
        VALUES (NOW(), 'running')
        RETURNING id
    """)
    return cur.fetchone()[0]


def log_sync_end(cur, log_id: int, status: str, boards: int = 0,
                 cards: int = 0, error: str = None):
    """Update sync log entry."""
    cur.execute("""
        UPDATE trello.sync_log
        SET finished_at = NOW(), status = %s, boards_synced = %s,
            cards_synced = %s, error_message = %s
        WHERE id = %s
    """, (status, boards, cards, error, log_id))
