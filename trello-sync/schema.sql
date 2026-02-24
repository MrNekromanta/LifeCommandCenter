-- Trello Sync Schema
-- Database: biznesvalidator_tasks (or any dedicated DB)
-- Supports: all boards, full card metadata, labels, members, checklists

CREATE SCHEMA IF NOT EXISTS trello;

-- ============================================================
-- BOARDS
-- ============================================================
CREATE TABLE trello.boards (
    id              SERIAL PRIMARY KEY,
    trello_id       TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    url             TEXT,
    closed          BOOLEAN DEFAULT FALSE,
    last_activity   TIMESTAMPTZ,
    synced_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- LISTS (columns on a board)
-- ============================================================
CREATE TABLE trello.lists (
    id              SERIAL PRIMARY KEY,
    trello_id       TEXT UNIQUE NOT NULL,
    board_id        INTEGER NOT NULL REFERENCES trello.boards(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    position        REAL,
    closed          BOOLEAN DEFAULT FALSE,
    synced_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- LABELS
-- ============================================================
CREATE TABLE trello.labels (
    id              SERIAL PRIMARY KEY,
    trello_id       TEXT UNIQUE NOT NULL,
    board_id        INTEGER NOT NULL REFERENCES trello.boards(id) ON DELETE CASCADE,
    name            TEXT,
    color           TEXT,
    synced_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- MEMBERS
-- ============================================================
CREATE TABLE trello.members (
    id              SERIAL PRIMARY KEY,
    trello_id       TEXT UNIQUE NOT NULL,
    username        TEXT,
    full_name       TEXT,
    avatar_url      TEXT,
    synced_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CARDS
-- ============================================================
CREATE TABLE trello.cards (
    id              SERIAL PRIMARY KEY,
    trello_id       TEXT UNIQUE NOT NULL,
    board_id        INTEGER NOT NULL REFERENCES trello.boards(id) ON DELETE CASCADE,
    list_id         INTEGER NOT NULL REFERENCES trello.lists(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    description     TEXT,
    position        REAL,
    url             TEXT,
    due             TIMESTAMPTZ,
    due_complete    BOOLEAN DEFAULT FALSE,
    closed          BOOLEAN DEFAULT FALSE,
    last_activity   TIMESTAMPTZ,
    synced_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- JUNCTION: card <-> label
-- ============================================================
CREATE TABLE trello.card_labels (
    card_id         INTEGER NOT NULL REFERENCES trello.cards(id) ON DELETE CASCADE,
    label_id        INTEGER NOT NULL REFERENCES trello.labels(id) ON DELETE CASCADE,
    PRIMARY KEY (card_id, label_id)
);

-- ============================================================
-- JUNCTION: card <-> member
-- ============================================================
CREATE TABLE trello.card_members (
    card_id         INTEGER NOT NULL REFERENCES trello.cards(id) ON DELETE CASCADE,
    member_id       INTEGER NOT NULL REFERENCES trello.members(id) ON DELETE CASCADE,
    PRIMARY KEY (card_id, member_id)
);

-- ============================================================
-- CHECKLISTS (optional but useful for subtasks)
-- ============================================================
CREATE TABLE trello.checklists (
    id              SERIAL PRIMARY KEY,
    trello_id       TEXT UNIQUE NOT NULL,
    card_id         INTEGER NOT NULL REFERENCES trello.cards(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    position        REAL,
    synced_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE trello.checklist_items (
    id              SERIAL PRIMARY KEY,
    trello_id       TEXT UNIQUE NOT NULL,
    checklist_id    INTEGER NOT NULL REFERENCES trello.checklists(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    state           TEXT DEFAULT 'incomplete', -- 'complete' or 'incomplete'
    position        REAL,
    due             TIMESTAMPTZ,
    synced_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SYNC LOG (audit trail)
-- ============================================================
CREATE TABLE trello.sync_log (
    id              SERIAL PRIMARY KEY,
    started_at      TIMESTAMPTZ NOT NULL,
    finished_at     TIMESTAMPTZ,
    status          TEXT DEFAULT 'running', -- 'running', 'success', 'error'
    boards_synced   INTEGER DEFAULT 0,
    cards_synced    INTEGER DEFAULT 0,
    error_message   TEXT
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_cards_board ON trello.cards(board_id);
CREATE INDEX idx_cards_list ON trello.cards(list_id);
CREATE INDEX idx_cards_closed ON trello.cards(closed);
CREATE INDEX idx_lists_board ON trello.lists(board_id);
CREATE INDEX idx_labels_board ON trello.labels(board_id);
CREATE INDEX idx_checklists_card ON trello.checklists(card_id);

-- ============================================================
-- VIEWS (convenient for MCP/Claude queries)
-- ============================================================

-- Full card view with board name, list name, labels, members
CREATE VIEW trello.v_cards AS
SELECT
    c.id,
    c.trello_id,
    b.name AS board_name,
    l.name AS list_name,
    c.name AS card_name,
    c.description,
    c.due,
    c.due_complete,
    c.closed,
    c.url,
    c.last_activity,
    c.position,
    COALESCE(
        (SELECT string_agg(lb.name || COALESCE(':' || lb.color, ''), ', ' ORDER BY lb.name)
         FROM trello.card_labels cl
         JOIN trello.labels lb ON lb.id = cl.label_id
         WHERE cl.card_id = c.id),
        ''
    ) AS labels,
    COALESCE(
        (SELECT string_agg(m.full_name, ', ' ORDER BY m.full_name)
         FROM trello.card_members cm
         JOIN trello.members m ON m.id = cm.member_id
         WHERE cm.card_id = c.id),
        ''
    ) AS members,
    c.synced_at
FROM trello.cards c
JOIN trello.boards b ON b.id = c.board_id
JOIN trello.lists l ON l.id = c.list_id;

-- Board summary: cards per list
CREATE VIEW trello.v_board_summary AS
SELECT
    b.name AS board_name,
    l.name AS list_name,
    l.position AS list_position,
    COUNT(c.id) FILTER (WHERE NOT c.closed) AS open_cards,
    COUNT(c.id) FILTER (WHERE c.closed) AS closed_cards
FROM trello.boards b
JOIN trello.lists l ON l.board_id = b.id AND NOT l.closed
LEFT JOIN trello.cards c ON c.list_id = l.id
WHERE NOT b.closed
GROUP BY b.name, l.name, l.position
ORDER BY b.name, l.position;
