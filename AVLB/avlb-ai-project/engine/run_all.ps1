# AVLB AI All-in-One Launcher
Write-Host "[AI] Cleaning up previous sessions..." -ForegroundColor Yellow

# Безопасная очистка портов 8000 (Relay) и 8501 (Streamlit)
$ports = 8000, 8501
foreach ($port in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    }
}

Write-Host "[AI] Starting AVLB AI System..." -ForegroundColor Cyan

# Пути к исполняемым файлам внутри виртуального окружения
$PY = ".\.venv\Scripts\python.exe"
$ST = ".\.venv\Scripts\streamlit.exe"

# Проверка кошелька перед запуском
if (-not (Test-Path ".\test_keypair.json")) {
    Write-Host "[!] Keypair not found. Generating..." -ForegroundColor Yellow
    & $PY setup_wallet.py
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "$PY collector.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$PY relay_server.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$PY integrator.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$ST run app.py"

Write-Host "[OK] All components are starting in separate windows." -ForegroundColor Green
Write-Host "Dashboard: http://localhost:8501"
Write-Host "Relay API: http://localhost:8000"