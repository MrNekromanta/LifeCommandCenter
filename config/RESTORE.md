# Claude Desktop Config — Backup & Restore

## Struktura

```
config/
  claude_desktop_config.json     # zamaskowana wersja (git-safe, placeholdery zamiast sekretow)
  backup_claude_config.ps1       # skrypt backup z timestampem
  backups/                       # lokalne backupy z timestampem (w .gitignore)
    claude_desktop_config_2026-03-14_120000.json
    ...
```

## Jak wykonac backup (manualnie)

```powershell
cd C:\projects\AI\LifeCommandCenter\config
.\backup_claude_config.ps1
```

Backup laduje do `config\backups\claude_desktop_config_YYYY-MM-DD_HHmmss.json`.
Skrypt zachowuje max 30 backupow, starsze usuwa automatycznie.

## Jak odtworzyc config po awarii / reinstall

1. Znajdz najnowszy backup:
   ```
   config\backups\claude_desktop_config_<najnowszy timestamp>.json
   ```
   Lub uzyj zamaskowanego szablonu z `config\claude_desktop_config.json`.

2. Uzupelnij placeholdery sekretami z **Bitwarden**:
   - `<BITWARDEN: Trello API Key>` — klucz API Trello
   - `<BITWARDEN: Trello Token>` — token Trello
   - `<BITWARDEN: Postgres RO haslo>` — haslo uzytkownika `claude_ro` (PostgreSQL)

3. Skopiuj odtworzony plik do:
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```
   czyli: `C:\Users\Krzysiek\AppData\Roaming\Claude\claude_desktop_config.json`

4. Zrestartuj Claude Desktop.

5. Weryfikacja — w Claude Desktop sprawdz czy MCP servery sa aktywne:
   - trello-db (read-only SQL do Postgres)
   - trello (write MCP, @delorenj)
   - lcc-rag (RAG graph)

## Sekrety — gdzie sa w Bitwarden

Wpisy Bitwarden do sprawdzenia:
- `Trello API` (lub podobne) — api key + token
- `Postgres LCC` / `claude_ro` — haslo read-only uzytkownika

## Uwagi

- Plik `config\backups\` jest w `.gitignore` — backupy z sekretami NIE trafiaja do git.
- Zamaskowany `claude_desktop_config.json` jest commitowany — sluzy jako szablon.
- Przy kazdej zmianie konfiguracji MCP: zaktualizuj tez zamaskowany template w repo.
