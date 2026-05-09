#Requires -Version 5.1
<#
.SYNOPSIS
    OmniPlay-MC one-click launcher — opens four titled windows in the right order.

.DESCRIPTION
    1. Runs preflight.py first; aborts if any check FAIL.
    2. Opens "MC server"   — starts Fabric via start_server.bat
    3. Opens "Convex dev"  — runs npx convex dev at repo root
    4. Opens "Dashboard"   — runs npm run dev in dashboard/
    5. Opens "Brain shell" — activates .venv and cds to repo root, ready
       for: python brain\run_agent.py --demo --log-level INFO

    Run from any working directory.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Resolve repo root regardless of cwd
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# ── Helpers ──────────────────────────────────────────────────────────────────

function Write-Header([string]$msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Open-Window([string]$Title, [string]$Command) {
    Start-Process powershell -ArgumentList `
        "-NoExit", `
        "-Command", `
        "`$host.UI.RawUI.WindowTitle = '$Title'; $Command"
}

# ── Step 0: Preflight ────────────────────────────────────────────────────────

Write-Header "Running preflight checks..."

$python = Join-Path $Repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    # Fall back to whatever python is on PATH
    $python = "python"
}

$preflightScript = Join-Path $Repo "scripts\preflight.py"
& $python $preflightScript
$preflightExit = $LASTEXITCODE

if ($preflightExit -ne 0) {
    Write-Host ""
    Write-Host "[start_all] Preflight reported failures. Fix them and re-run start_all.ps1." -ForegroundColor Red
    exit 1
}

# ── Step 1: Minecraft server ─────────────────────────────────────────────────

Write-Header "Opening MC server window (Fabric; waiting 25 s to boot)..."

$startServerBat = Join-Path $Repo "scripts\start_server.bat"
Open-Window "MC server" "Set-Location '$Repo'; cmd /c '$startServerBat'"

Write-Host "  Waiting 25 s for Fabric to boot..." -ForegroundColor DarkGray
Start-Sleep -Seconds 25

# ── Step 2: Convex dev ───────────────────────────────────────────────────────

Write-Header "Opening Convex dev window..."

Open-Window "Convex dev" "Set-Location '$Repo'; npx convex dev"

Write-Host "  Waiting 5 s..." -ForegroundColor DarkGray
Start-Sleep -Seconds 5

# ── Step 3: Dashboard ────────────────────────────────────────────────────────

Write-Header "Opening Dashboard window (http://localhost:3000)..."

$dashDir = Join-Path $Repo "dashboard"
Open-Window "Dashboard" "Set-Location '$dashDir'; npm run dev"

Write-Host "  Waiting 6 s for Next.js to compile..." -ForegroundColor DarkGray
Start-Sleep -Seconds 6

# ── Step 4: Brain shell ──────────────────────────────────────────────────────

Write-Header "Opening Brain shell window (venv pre-activated)..."

$venvActivate = Join-Path $Repo ".venv\Scripts\Activate.ps1"
$brainCmd = ". '$venvActivate'; Set-Location '$Repo'; Write-Host 'Brain shell ready.' -ForegroundColor Green; Write-Host 'Run: python brain\run_agent.py --demo --log-level INFO' -ForegroundColor Yellow"
Open-Window "Brain shell" $brainCmd

# ── Done ─────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "All windows launched." -ForegroundColor Green
Write-Host ""
Write-Host "  MC server  → see 'MC server' window (wait for 'Done!' in its log)"
Write-Host "  Convex     → see 'Convex dev' window"
Write-Host "  Dashboard  → http://localhost:3000"
Write-Host "  Brain      → switch to 'Brain shell' and run:"
Write-Host "               python brain\run_agent.py --demo --log-level INFO" -ForegroundColor Yellow
Write-Host ""
