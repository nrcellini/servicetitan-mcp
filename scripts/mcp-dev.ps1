# Run `mcp dev` with stable server path, editable project, and free Inspector ports
# (avoids "PORT IS IN USE" on 6274 / 6277 when an old Inspector is still running).
#
# Usage (from anywhere):
#   .\scripts\mcp-dev.ps1
# Pin ports explicitly:
#   .\scripts\mcp-dev.ps1 -NoAutoPort -ClientPort 6284 -ServerPort 6287
param(
    [switch] $NoAutoPort,
    [int] $ClientPort = 6274,
    [int] $ServerPort = 6277
)
$ErrorActionPreference = "Stop"

. "$PSScriptRoot\inspector-ports.ps1"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ServerFile = (Resolve-Path (Join-Path $RepoRoot "src\server.py")).Path
Set-Location $RepoRoot

$ports = Resolve-InspectorPorts -ClientPreferred $ClientPort -ServerPreferred $ServerPort -NoAuto:$NoAutoPort
$env:CLIENT_PORT = "$($ports.ClientPort)"
$env:SERVER_PORT = "$($ports.ServerPort)"

Write-Host "MCP Inspector: UI port CLIENT_PORT=$($ports.ClientPort), proxy SERVER_PORT=$($ports.ServerPort)" -ForegroundColor Cyan

uv run --extra dev mcp dev --with-editable $RepoRoot $ServerFile
exit $LASTEXITCODE
