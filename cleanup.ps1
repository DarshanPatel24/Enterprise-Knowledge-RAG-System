<#
.SYNOPSIS
    Safe repository cleanup for EK-RAG. Removes generated/reproducible artifacts only.

.DESCRIPTION
    Tiered, opt-in cleanup.
      Tier 1 (with -Apply): caches, build output, and logs. Always safe; auto-regenerated.
      Tier 2 (with -Deep):  node_modules, virtual environments, egg-info. Safe but need reinstall.
    Never touches data/model caches (services/*/storage, services/ekdc/models), .git, notebooks,
    demo_*.py scripts, or docs reviews.
    Default is a DRY RUN (lists only). Pass -Apply to actually delete.

.EXAMPLE
    .\cleanup.ps1                 # preview Tier 1 (deletes nothing)
    .\cleanup.ps1 -Apply          # delete Tier 1
    .\cleanup.ps1 -Apply -Deep    # delete Tier 1 + Tier 2 (then reinstall deps)
#>
[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$Deep
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

# Paths containing any of these segments are protected/skipped and never removed by
# Tier 1. (Tier 2 removes the whole .venv/venv/node_modules dirs explicitly.)
$excludeRegex = '\\(storage|models|\.git|\.venv|venv|node_modules)\\'

$tier1Dirs  = @("__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", ".next", "out", "test-results", "playwright-report")
$tier1Files = @("*.pyc", "*.pyo", "*.tsbuildinfo", "*.log")
$tier2Dirs  = @("node_modules", ".venv", "venv", "*.egg-info")

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

Write-Host "Tier 1 -- caches / build output / logs (safe, auto-regenerated):" -ForegroundColor Cyan
Remove-Targets -Paths (Find-Dirs -Names $tier1Dirs) -Label "Tier1 dirs"
Remove-Targets -Paths (Find-Files -Patterns $tier1Files) -Label "Tier1 files"

if ($Deep) {
    Write-Host ""
    Write-Host "Tier 2 -- dependencies / environments (reinstall required afterward):" -ForegroundColor Cyan
    Remove-Targets -Paths (Find-Dirs -Names $tier2Dirs) -Label "Tier2 dirs"
    Write-Host ""
    Write-Host "After -Deep cleanup, reinstall before running: pip install -r requirements.txt (+ per service); cd apps/web-ui; npm ci" -ForegroundColor Magenta
}

Write-Host ""
Write-Host "Protected (never touched): services/*/storage, services/ekdc/models, .git, notebooks, demo_*.py, docs reviews." -ForegroundColor DarkGray
if (-not $Apply) {
    Write-Host "This was a preview. Re-run with -Apply to delete." -ForegroundColor Cyan
}
