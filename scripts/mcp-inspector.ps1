# MCP Inspector with a subprocess command that works from any cwd:
# - Absolute paths for the server file and --with-editable
# - mcp[cli] (not bare mcp) so `mcp run` has Typer in the Inspector-spawned env
#
# If 6274 / 6277 are still in use, pass different ports (see modelcontextprotocol/inspector README):
#   .\scripts\mcp-inspector.ps1 -ClientPort 6284 -ServerPort 6287
param(
    [int] $ClientPort = 6274,
    [int] $ServerPort = 6277
)
$ErrorActionPreference = "Stop"
$env:CLIENT_PORT = "$ClientPort"
$env:SERVER_PORT = "$ServerPort"
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
