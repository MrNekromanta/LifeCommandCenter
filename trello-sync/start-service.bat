@echo off
REM Trello Sync Service — auto-start script for Task Scheduler
cd /d c:\projects\AI\LifeCommandCenter\trello-sync
.venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8891
