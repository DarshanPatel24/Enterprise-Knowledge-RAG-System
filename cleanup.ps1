<#
.SYNOPSIS
    Safe repository cleanup for EK-RAG. Removes generated/reproducible artifacts only.

.DESCRIPTION
    Tiered, opt-in cleanup.
      Tier 1 (with -Apply):      caches, test output, and logs. Always safe; auto-regenerated.
      Tier 2 (with -Deep):       node_modules, virtual environments, egg-info, and the web
                                 UI build (.next/out). Safe but need reinstall/rebuild.
      Tier 3 (with -ResetData):  DESTRUCTIVE local data reset. Wipes the Docker
                                 stack volumes (Qdrant vectors, MinIO objects, Redis,
                                 Langfuse) via `docker compose down -v`. Forces a
                                 re-ingest afterwards. Downloaded model weights are
                                 NOT touched, and the SQL Server control plane is
                                 NOT auto-dropped (manual step is printed).
    Never touches data/model caches (services/*/storage including the local Qdrant
    vector store, services/*/storage/hf, services/ekdc/models), any .env* config,
    .git, notebooks, demo_*.py scripts, or docs reviews for Tier 1 / Tier 2.
    Default is a DRY RUN (lists only). Pass -Apply to actually delete.

.EXAMPLE
    .\cleanup.ps1                     # preview Tier 1 (deletes nothing)
    .\cleanup.ps1 -Apply              # delete Tier 1
    .\cleanup.ps1 -Apply -Deep        # delete Tier 1 + Tier 2 (then reinstall deps)
    .\cleanup.ps1 -ResetData          # preview the data reset (nothing happens)
    .\cleanup.ps1 -Apply -ResetData   # wipe Docker volumes (prompts to confirm)
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$Deep,
    [switch]$ResetData
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

# Paths containing any of these segments are protected/skipped and never removed by
# Tier 1. (Tier 2 removes the whole .venv/venv/node_modules/.next dirs explicitly:
# each dir's own path has no trailing separator, so it is not matched here.)
$excludeRegex = '\\(storage|models|\.git|\.venv|venv|node_modules|\.next)\\'

$tier1Dirs  = @("__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", "test-results", "playwright-report")
$tier1Files = @("*.pyc", "*.pyo", "*.tsbuildinfo", "*.log")
$tier2Dirs  = @("node_modules", ".venv", "venv", "*.egg-info", ".next", "out")

function Find-Dirs {
    param([string[]]$Names)
    $found = foreach ($name in $Names) {
        Get-ChildItem -Path $root -Recurse -Directory -Force -Filter $name -ErrorAction SilentlyContinue
    }
    $found | Where-Object { $_.FullName -notmatch $excludeRegex } |
        Select-Object -ExpandProperty FullName -Unique
}

function Find-Files {
    param([string[]]$Patterns)
    $found = foreach ($pattern in $Patterns) {
        Get-ChildItem -Path $root -Recurse -File -Force -Filter $pattern -ErrorAction SilentlyContinue
    }
    $found | Where-Object { $_.FullName -notmatch $excludeRegex } |
        Select-Object -ExpandProperty FullName -Unique
}

function Remove-Targets {
    param([string[]]$Paths, [string]$Label)
    if (-not $Paths -or $Paths.Count -eq 0) {
        Write-Host "  ($Label) nothing found." -ForegroundColor DarkGray
        return
    }
    foreach ($path in $Paths) {
        if ($Apply) {
            try {
                Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction Stop
                Write-Host "  removed: $path" -ForegroundColor Green
            }
            catch {
                $msg = $_.Exception.Message
                Write-Host "  FAILED : $path -- $msg" -ForegroundColor Red
            }
        }
        else {
            Write-Host "  would remove: $path" -ForegroundColor Yellow
        }
    }
}

if ($Apply) { $mode = "APPLY" } else { $mode = "DRY RUN (nothing deleted; pass -Apply to delete)" }
Write-Host "EK-RAG cleanup -- mode: $mode" -ForegroundColor Cyan
Write-Host ""

Write-Host "Tier 1 -- caches / test output / logs (safe, auto-regenerated):" -ForegroundColor Cyan
Remove-Targets -Paths (Find-Dirs -Names $tier1Dirs) -Label "Tier1 dirs"
Remove-Targets -Paths (Find-Files -Patterns $tier1Files) -Label "Tier1 files"

if ($Deep) {
    Write-Host ""
    Write-Host "Tier 2 -- dependencies / environments / web build (reinstall/rebuild required afterward):" -ForegroundColor Cyan
    Remove-Targets -Paths (Find-Dirs -Names $tier2Dirs) -Label "Tier2 dirs"
    Write-Host ""
    Write-Host "After -Deep cleanup, reinstall before running:" -ForegroundColor Magenta
    Write-Host "  - Root:        pip install -r requirements.txt" -ForegroundColor Magenta
    Write-Host "  - Per service: pip install -e 'services/<svc>[dev,mssql,storage]' (the mssql extra installs pyodbc for EKIE)" -ForegroundColor Magenta
    Write-Host "  - Web UI:      cd apps/web-ui; npm ci; npm run build (build only needed for 'npm run start')" -ForegroundColor Magenta
}

if ($ResetData) {
    Write-Host ""
    Write-Host "Tier 3 -- DESTRUCTIVE local data reset (Docker volumes):" -ForegroundColor Red
    $composeFile = "docker-compose.local.yml"
    if (-not (Test-Path (Join-Path $root $composeFile))) {
        Write-Host "  $composeFile not found; skipping data reset." -ForegroundColor DarkGray
    }
    elseif ($Apply) {
        Write-Host "  This runs 'docker compose -f $composeFile down -v' and PERMANENTLY deletes" -ForegroundColor Red
        Write-Host "  all Qdrant vectors, MinIO objects, Redis cache, and Langfuse data." -ForegroundColor Red
        Write-Host "  Downloaded model weights are kept. You must re-ingest documents afterward." -ForegroundColor Red
        $confirm = Read-Host "  Type RESET to proceed"
        if ($confirm -eq "RESET") {
            docker compose -f $composeFile down -v
            Write-Host "  Docker volumes wiped. Bring the stack back with:" -ForegroundColor Green
            Write-Host "    docker compose -f $composeFile up -d" -ForegroundColor Green
            Write-Host "  Then reset the SQL Server control plane (drops + recreates tables) and re-ingest." -ForegroundColor Yellow
        }
        else {
            Write-Host "  Confirmation not received; data reset aborted." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  would run: docker compose -f $composeFile down -v (wipes Qdrant/MinIO/Redis/Langfuse volumes)" -ForegroundColor Yellow
        Write-Host "  model weights kept; re-run with -Apply -ResetData to execute (you will be prompted to confirm)." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Protected (never touched): services/*/storage (incl. local Qdrant vectors), services/*/storage/hf (model weights), services/ekdc/models, all .env* config, .git, notebooks, demo_*.py, docs reviews." -ForegroundColor DarkGray
if (-not $Apply) {
    Write-Host "This was a preview. Re-run with -Apply to delete." -ForegroundColor Cyan
}
