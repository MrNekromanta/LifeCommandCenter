"""Sync orchestrator — pulls all Trello data into Postgres."""

import logging
import time

import trello_client as trello
from db import (
    get_conn, upsert_board, upsert_list, upsert_label, upsert_member,
    upsert_card, sync_card_labels, sync_card_members,
    upsert_checklist, upsert_checklist_item,
    log_sync_start, log_sync_end,
)

logger = logging.getLogger(__name__)


def run_sync() -> dict:
    """
    Full sync: all boards → lists → labels → members → cards → checklists.
    Returns summary dict.
    """
    start = time.time()
    total_boards = 0
    total_cards = 0

    with get_conn() as conn:
        cur = conn.cursor()
        log_id = log_sync_start(cur)
        conn.commit()

        try:
            # 1. Fetch all boards
            boards = trello.get_my_boards()
            logger.info(f"Found {len(boards)} boards")

            for board_data in boards:
                board_id = upsert_board(cur, board_data)
                trello_board_id = board_data["id"]
                total_boards += 1

                # 2. Lists
                lists = trello.get_board_lists(trello_board_id)
                list_map = {}  # trello_id -> local_id
                for lst in lists:
                    local_id = upsert_list(cur, lst, board_id)
                    list_map[lst["id"]] = local_id

                # 3. Labels
                labels = trello.get_board_labels(trello_board_id)
                for label in labels:
                    upsert_label(cur, label, board_id)

                # 4. Members
                members = trello.get_board_members(trello_board_id)
                for member in members:
                    upsert_member(cur, member)

                # 5. Cards
                cards = trello.get_board_cards(trello_board_id)
                for card_data in cards:
                    list_local_id = list_map.get(card_data.get("idList"))
                    if list_local_id is None:
                        logger.warning(
                            f"Card '{card_data['name']}' references unknown list "
                            f"{card_data.get('idList')}, skipping"
                        )
                        continue

                    card_id = upsert_card(cur, card_data, board_id, list_local_id)
                    total_cards += 1

                    # Card ↔ Label associations
                    sync_card_labels(cur, card_id, card_data.get("idLabels", []))

                    # Card ↔ Member associations
                    sync_card_members(cur, card_id, card_data.get("idMembers", []))

                    # 6. Checklists
                    for cl_trello_id in card_data.get("idChecklists", []):
                        try:
                            cl_data = trello.get_checklist(cl_trello_id)
                            cl_id = upsert_checklist(cur, cl_data, card_id)
                            for item in cl_data.get("checkItems", []):
                                upsert_checklist_item(cur, item, cl_id)
                        except Exception as e:
                            logger.warning(f"Failed to sync checklist {cl_trello_id}: {e}")

                conn.commit()
                logger.info(f"Board '{board_data['name']}': {len(cards)} cards synced")

            # Log success
            log_sync_end(cur, log_id, "success", total_boards, total_cards)
            conn.commit()

        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            log_sync_end(cur, log_id, "error", total_boards, total_cards, str(e))
            conn.commit()
            raise

    elapsed = time.time() - start
    summary = {
        "status": "success",
        "boards": total_boards,
        "cards": total_cards,
        "elapsed_seconds": round(elapsed, 2),
    }
    logger.info(f"Sync complete: {summary}")
    return summary
