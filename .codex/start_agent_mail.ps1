$ErrorActionPreference = "Stop"

$agentMailDir = Join-Path $env:USERPROFILE ".local\share\mcp_agent_mail"
if (-not (Test-Path $agentMailDir)) {
    throw "Agent Mail is not installed at $agentMailDir"
}

$existing = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue |
    Where-Object { $_.State -eq "Listen" } |
    Select-Object -First 1

if ($existing) {
    Write-Output "Agent Mail is already listening on http://127.0.0.1:8765/api/ (PID $($existing.OwningProcess))."
    exit 0
}

$logDir = Join-Path $agentMailDir "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$command = "Set-Location '$agentMailDir'; uv run python -m mcp_agent_mail.cli serve-http --host 127.0.0.1 --port 8765 --path /api/"
$process = Start-Process -FilePath "powershell.exe" `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $command) `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $logDir "server.out.log") `
    -RedirectStandardError (Join-Path $logDir "server.err.log") `
    -PassThru

Start-Sleep -Seconds 5
$health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/health/readiness" -TimeoutSec 10
Write-Output "Agent Mail started on http://127.0.0.1:8765/api/ (PID $($process.Id)); readiness=$($health.status)."
