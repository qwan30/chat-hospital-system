param(
    [Parameter(Mandatory = $true)]
    [string]$Name
)

$ErrorActionPreference = "Stop"

$hookMap = @{
    "session_start" = "session_start.py"
    "user_prompt_submit" = "user_prompt_submit.py"
    "pre_tool_use_policy" = "pre_tool_use_policy.py"
    "permission_request" = "permission_request.py"
    "post_tool_use_review" = "post_tool_use_review.py"
    "stop_continue" = "stop_continue.py"
}

if (-not $hookMap.ContainsKey($Name)) {
    Write-Error "Unknown Codex hook: $Name"
    exit 1
}

$scriptPath = Join-Path $PSScriptRoot $hookMap[$Name]
$python = Get-Command python -ErrorAction SilentlyContinue

if (-not $python) {
    Write-Error "Python was not found on PATH for Codex hook: $Name"
    exit 1
}

$stdinText = [Console]::In.ReadToEnd()
if ($stdinText.Length -gt 0) {
    $stdinText | & $python.Source $scriptPath
} else {
    & $python.Source $scriptPath
}

exit $LASTEXITCODE
