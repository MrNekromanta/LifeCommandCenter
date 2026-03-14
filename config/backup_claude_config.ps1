# backup_claude_config.ps1
# Backup claude_desktop_config.json z timestampem
# Uzycie: .\backup_claude_config.ps1
# Opcjonalnie: dodaj do Windows Task Scheduler (daily)

$source = "$env:APPDATA\Claude\claude_desktop_config.json"
$backupDir = "$PSScriptRoot\backups"
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$dest = "$backupDir\claude_desktop_config_$timestamp.json"

# Upewnij sie ze katalog backupow istnieje
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

# Sprawdz czy plik zrodlowy istnieje
if (-not (Test-Path $source)) {
    Write-Error "Nie znaleziono pliku: $source"
    exit 1
}

# Kopiuj
Copy-Item -Path $source -Destination $dest
Write-Host "Backup OK: $dest"

# Zachowaj tylko ostatnie 30 backupow
$backups = Get-ChildItem -Path $backupDir -Filter "claude_desktop_config_*.json" |
    Sort-Object LastWriteTime -Descending
if ($backups.Count -gt 30) {
    $backups | Select-Object -Skip 30 | Remove-Item
    Write-Host "Usunieto stare backupy (zachowano 30)"
}
