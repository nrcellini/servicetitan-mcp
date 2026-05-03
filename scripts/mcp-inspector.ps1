# MCP Inspector with a subprocess command that works from any cwd:
# - Absolute paths for the server file and --with-editable
# - mcp[cli] (not bare mcp) so `mcp run` has Typer in the Inspector-spawned env
# - By default, picks free ports from 6274 / 6277 so stale Inspectors do not block startup
#
# Pin ports explicitly:
#   .\scripts\mcp-inspector.ps1 -NoAutoPort -ClientPort 6284 -ServerPort 6287
param(
    [switch] $NoAutoPort,
    [int] $ClientPort = 6274,
    [int] $ServerPort = 6277
)
$ErrorActionPreference = "Stop"

. "$PSScriptRoot\inspector-ports.ps1"

$ports = Resolve-InspectorPorts -ClientPreferred $ClientPort -ServerPreferred $ServerPort -NoAuto:$NoAutoPort
$env:CLIENT_PORT = "$($ports.ClientPort)"
$env:SERVER_PORT = "$($ports.ServerPort)"

Write-Host "MCP Inspector: UI port CLIENT_PORT=$($ports.ClientPort), proxy SERVER_PORT=$($ports.ServerPort)" -ForegroundColor Cyan

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ServerFile = (Resolve-Path (Join-Path $RepoRoot "src\server.py")).Path
Set-Location $RepoRoot

$npx = $null
foreach ($c in @("npx.cmd", "npx.exe", "npx")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        $npx = $c
        break
    }
}
if (-not $npx) {
    throw "npx not found. Install Node.js and ensure npx is on PATH."
}

$npxArgs = @(
    "-y",
    "@modelcontextprotocol/inspector",
    "uv", "run",
    "--with", "mcp[cli]",
    "--with-editable", $RepoRoot,
    "mcp", "run", $ServerFile
)

& $npx @npxArgs
exit $LASTEXITCODE
