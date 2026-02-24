"""Trello REST API client."""

import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.trello.com/1"


def _params(**extra) -> dict:
    """Base auth params + extras."""
    return {"key": settings.trello_api_key, "token": settings.trello_token, **extra}


def _get(path: str, params: dict = None) -> Any:
    """GET request to Trello API with error handling."""
    url = f"{BASE_URL}{path}"
    all_params = _params(**(params or {}))
    resp = httpx.get(url, params=all_params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_my_boards() -> list[dict]:
    """Get all boards for the authenticated member."""
    return _get("/members/me/boards", {"fields": "name,desc,url,closed,dateLastActivity"})


def get_board_lists(board_id: str) -> list[dict]:
    """Get all lists for a board (including closed)."""
    return _get(f"/boards/{board_id}/lists", {"filter": "all", "fields": "name,pos,closed"})


def get_board_labels(board_id: str) -> list[dict]:
    """Get all labels for a board."""
    return _get(f"/boards/{board_id}/labels", {"fields": "name,color"})


def get_board_members(board_id: str) -> list[dict]:
    """Get all members of a board."""
    return _get(f"/boards/{board_id}/members", {"fields": "username,fullName,avatarUrl"})


def get_board_cards(board_id: str) -> list[dict]:
    """Get all cards for a board (including closed)."""
    return _get(f"/boards/{board_id}/cards/all", {
        "fields": "name,desc,pos,url,due,dueComplete,closed,dateLastActivity,idList,idLabels,idMembers,idChecklists",
    })


def get_checklist(checklist_id: str) -> dict:
    """Get a single checklist with items."""
    return _get(f"/checklists/{checklist_id}", {
        "checkItem_fields": "name,state,pos,due",
    })
