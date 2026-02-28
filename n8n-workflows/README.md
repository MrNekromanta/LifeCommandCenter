# LCC Daily Digest — n8n Workflow Setup

## Pliki
- `daily-digest.json` — workflow do importu w n8n

## Wymagane credentials w n8n

### 1. Postgres (Trello data)
Istniejący credential "Postgres account" — sprawdź czy wskazuje na:
- **Host:** `crypto-postgres` (nazwa kontenera w Docker network)
- **Port:** `5432`
- **Database:** `trello_sync`
- **User:** `postgres`
- **Password:** (z .env crypto-rebalancer)
- **Schema:** `trello`

Jeśli istniejący credential wskazuje na inną bazę (np. n8n_db), utwórz nowy:
**Name:** `LCC Trello Postgres`

### 2. Telegram Bot
Utwórz nowy credential typu "Telegram API":
- **Access Token:** (z .env crypto-rebalancer, TELEGRAM_BOT_TOKEN)
- **Name:** `LCC Telegram Bot`

## Import workflow

1. Otwórz n8n: http://localhost:5678
2. Menu → Import from File → wybierz `daily-digest.json`
3. Otwórz workflow, kliknij node "Query Trello Data":
   - Przypisz credential Postgres (LCC Trello Postgres lub istniejący)
4. Kliknij node "Send to Telegram":
   - Przypisz credential Telegram
5. Kliknij **Test workflow** (przycisk Execute)
6. Sprawdź Telegram — powinien przyjść digest
7. Jeśli OK → Toggle **Active** (prawy górny róg)

## Opis workflow

```
Daily 8:00 (cron)
    → Query Trello Data (Postgres — trello.v_cards)
    → Format Digest (Code — formatuje wiadomość)
    → Send to Telegram
```

### Co zawiera digest:
- 🔢 Podsumowanie: ile kart In Progress / Blocked / Ready / Backlog
- 🔵 Lista kart In Progress z info ile dni
- 🔴 Karty zablokowane
- ⚠️ WIP alert (>3 karty In Progress)
- 🟡 Stale cards (>14 dni bez aktywności w In Progress/Ready)
- ✅ "Czysto" jeśli nic aktywnego + sugestia

### Timezone
Workflow ustawiony na `Europe/Warsaw`. Trigger: codziennie 8:00.
