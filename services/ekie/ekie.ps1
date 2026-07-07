<#
    EKIE Control Panel — one master script to run the whole pipeline.

    A simple menu-driven launcher for everything you currently run by hand:
    the API, the sync worker (folder watcher), the async ingest worker, the live
    monitor, infrastructure, document cleanup, and the test suite.

    Usage:
        cd "D:\Octave\AI training\Enterprise-Knowledge-RAG-System"
        .\ekie.ps1

    Long-running services (API / workers / monitor) open in their own windows so
    this menu stays usable. One-off actions (list / purge / tests) run inline.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Paths (resolved relative to this script, so it works from anywhere) ------
$RepoRoot    = $PSScriptRoot
$ServiceRoot = Join-Path $RepoRoot 'services\ekie'
$ScriptsDir  = Join-Path $ServiceRoot 'scripts'
$EnvFile     = Join-Path $ServiceRoot '.env'
$Compose     = Join-Path $RepoRoot 'docker-compose.local.yml'

$VenvPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPython)) { $VenvPython = 'python' }

# Track services launched from this session so we can stop them later.
$script:Started = @()

# --- Helpers ------------------------------------------------------------------

function Get-AsyncMode {
    if (Test-Path $EnvFile) {
        $m = Select-String -Path $EnvFile -Pattern '^\s*EKIE_INGESTION__ASYNC_ENABLED\s*=\s*(\S+)' |
             Select-Object -First 1
        if ($m) { return $m.Matches[0].Groups[1].Value.Trim() }
    }
    return 'false'
}

function Set-AsyncMode([string]$Value) {
    if (-not (Test-Path $EnvFile)) { Write-Host "  .env not found: $EnvFile" -ForegroundColor Red; return }
    $lines = Get-Content $EnvFile
    if ($lines -match '^\s*EKIE_INGESTION__ASYNC_ENABLED\s*=') {
        $lines = $lines -replace '^(\s*EKIE_INGESTION__ASYNC_ENABLED\s*=\s*).*', "`${1}$Value"
    } else {
        $lines += "EKIE_INGESTION__ASYNC_ENABLED=$Value"
    }
    Set-Content -Path $EnvFile -Value $lines
    Write-Host "  Async mode set to: $Value" -ForegroundColor Green
}

function Start-Service([string]$Title, [string]$ScriptName, [string]$ExtraArgs = '') {
    $scriptPath = Join-Path $ScriptsDir $ScriptName
    if (-not (Test-Path $scriptPath)) { Write-Host "  Script not found: $scriptPath" -ForegroundColor Red; return }
    $inner = "`$Host.UI.RawUI.WindowTitle = '$Title'; & '$VenvPython' '$scriptPath' $ExtraArgs"
    $proc  = Start-Process powershell -ArgumentList '-NoExit', '-Command', $inner `
                -WorkingDirectory $ServiceRoot -PassThru
    $script:Started += [pscustomobject]@{ Title = $Title; Id = $proc.Id }
    Write-Host "  Launched '$Title' in a new window (PID $($proc.Id))." -ForegroundColor Green
}

function Invoke-Tool([string]$ScriptName, [string[]]$ToolArgs) {
    $scriptPath = Join-Path $ScriptsDir $ScriptName
    Push-Location $ServiceRoot
    try { & $VenvPython $scriptPath @ToolArgs }
    finally { Pop-Location }
}

function Test-Port([string]$TargetHost, [int]$Port) {
    try {
        $c = New-Object Net.Sockets.TcpClient
        $iar = $c.BeginConnect($TargetHost, $Port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(700)
        if ($ok -and $c.Connected) { $c.Close(); return $true }
        $c.Close(); return $false
    } catch { return $false }
}

function Write-StatusLine([string]$Name, [bool]$Up, [string]$Detail = '') {
    $tag = if ($Up) { '[ UP ]' } else { '[DOWN]' }
    $col = if ($Up) { 'Green' } else { 'Red' }
    Write-Host ("   {0,-16} " -f $Name) -NoNewline
    Write-Host $tag -ForegroundColor $col -NoNewline
    if ($Detail) { Write-Host "  $Detail" -ForegroundColor DarkGray } else { Write-Host '' }
}

function Show-Status {
    Write-Host "`n  Service health / ports:" -ForegroundColor Cyan
    $apiUp = $false; $apiDetail = ''
    try {
        $r = Invoke-RestMethod 'http://localhost:8001/health/live' -TimeoutSec 3
        $apiUp = $true; $apiDetail = "status=$($r.status)"
    } catch { $apiUp = $false }
    Write-StatusLine 'EKIE API (8001)'  $apiUp $apiDetail
    Write-StatusLine 'Qdrant (6333)'    (Test-Port 'localhost' 6333)
    Write-StatusLine 'MinIO (9005)'     (Test-Port 'localhost' 9005)
    Write-StatusLine 'SQL Server (1433)'(Test-Port 'localhost' 1433)
    Write-StatusLine 'Redis (6379)'     (Test-Port 'localhost' 6379)

    if ($script:Started.Count -gt 0) {
        Write-Host "`n  Services launched from this panel:" -ForegroundColor Cyan
        foreach ($s in $script:Started) {
            $alive = $null -ne (Get-Process -Id $s.Id -ErrorAction SilentlyContinue)
            Write-StatusLine $s.Title $alive "PID $($s.Id)"
        }
    }
}

function Stop-StartedServices {
    if ($script:Started.Count -eq 0) { Write-Host "  Nothing was started from this panel." -ForegroundColor Yellow; return }
    foreach ($s in $script:Started) {
        $p = Get-Process -Id $s.Id -ErrorAction SilentlyContinue
        if ($p) { Stop-Process -Id $s.Id -Force -ErrorAction SilentlyContinue; Write-Host "  Stopped '$($s.Title)' (PID $($s.Id))." -ForegroundColor Green }
    }
    $script:Started = @()
}

function Pause-Menu { Write-Host ''; Read-Host '  Press Enter to return to the menu' | Out-Null }

# --- Menu ---------------------------------------------------------------------

function Show-Menu {
    $mode = (Get-AsyncMode)
    $modeLabel = if ($mode -match '^(true|1|yes)$') { 'ASYNC (queue + ingest worker)' } else { 'SYNC (inline, legacy)' }
    $modeColor = if ($mode -match '^(true|1|yes)$') { 'Yellow' } else { 'Green' }

    Clear-Host
    Write-Host '=================================================================' -ForegroundColor Cyan
    Write-Host '                     EKIE  CONTROL  PANEL' -ForegroundColor Cyan
    Write-Host '=================================================================' -ForegroundColor Cyan
    Write-Host '  Ingestion mode: ' -NoNewline; Write-Host $modeLabel -ForegroundColor $modeColor
    Write-Host "  Repo: $RepoRoot" -ForegroundColor DarkGray
    Write-Host ''
    Write-Host '  SERVICES (each opens in its own window)' -ForegroundColor White
    Write-Host '    1  Start API                     (the brain / REST endpoints)'
    Write-Host '    2  Start Sync Worker             (watches the folder)'
    Write-Host '    3  Start Ingest Worker           (async doer; needed if ASYNC)'
    Write-Host '    4  Start Monitor                 (live dashboard)'
    Write-Host '    5  Start FULL STACK              (API + Sync + Ingest*if async + Monitor)'
    Write-Host ''
    Write-Host '  CONFIGURATION' -ForegroundColor White
    Write-Host "    6  Toggle Async mode             (currently: $mode)"
    Write-Host ''
    Write-Host '  INFRASTRUCTURE' -ForegroundColor White
    Write-Host '    7  Start Docker infra            (compose up -d)'
    Write-Host '    8  Show status / health'
    Write-Host ''
    Write-Host '  DOCUMENTS' -ForegroundColor White
    Write-Host '    9  List documents'
    Write-Host '   10  Purge orphaned documents      (wrong-folder / stale)'
    Write-Host '   11  Purge document by source path'
    Write-Host '   12  Drop empty repositories'
    Write-Host ''
    Write-Host '  MAINTENANCE' -ForegroundColor White
    Write-Host '   13  Run test suite'
    Write-Host '   14  Run setup (schema + buckets)'
    Write-Host '   15  Stop services started from here'
    Write-Host ''
    Write-Host '    Q  Quit' -ForegroundColor White
    Write-Host '-----------------------------------------------------------------' -ForegroundColor Cyan
}

# --- Main loop ----------------------------------------------------------------

while ($true) {
    Show-Menu
    $choice = (Read-Host '  Select an option').Trim()

    switch ($choice) {
        '1' { Start-Service 'EKIE-API'          'start_api.py';          Pause-Menu }
        '2' { Start-Service 'EKIE-Sync-Worker'  'start_worker.py';       Pause-Menu }
        '3' { Start-Service 'EKIE-Ingest-Worker' 'start_ingest_worker.py'; Pause-Menu }
        '4' { Start-Service 'EKIE-Monitor'      'monitor.py';            Pause-Menu }
        '5' {
            Start-Service 'EKIE-API' 'start_api.py'
            Start-Sleep -Seconds 4
            Start-Service 'EKIE-Sync-Worker' 'start_worker.py'
            if ((Get-AsyncMode) -match '^(true|1|yes)$') {
                Start-Service 'EKIE-Ingest-Worker' 'start_ingest_worker.py'
            } else {
                Write-Host '  (Async is OFF, so no ingest worker is needed.)' -ForegroundColor DarkGray
            }
            Start-Service 'EKIE-Monitor' 'monitor.py'
            Pause-Menu
        }
        '6' {
            $current = Get-AsyncMode
            $new = if ($current -match '^(true|1|yes)$') { 'false' } else { 'true' }
            Set-AsyncMode $new
            if ($new -eq 'true') {
                Write-Host '  Reminder: in ASYNC mode you must also run the Ingest Worker (option 3).' -ForegroundColor Yellow
            }
            Write-Host '  Restart the API for the change to take effect.' -ForegroundColor Yellow
            Pause-Menu
        }
        '7' {
            if (Test-Path $Compose) {
                Write-Host "  Starting infrastructure via $Compose ..." -ForegroundColor Cyan
                docker compose -f $Compose up -d
            } else { Write-Host "  Compose file not found: $Compose" -ForegroundColor Red }
            Pause-Menu
        }
        '8' { Show-Status; Pause-Menu }
        '9' { Invoke-Tool 'purge_documents.py' @('--list'); Pause-Menu }
        '10' {
            Write-Host '  This hard-deletes orphaned documents and their vectors.' -ForegroundColor Yellow
            Invoke-Tool 'purge_documents.py' @('--orphaned')
            Pause-Menu
        }
        '11' {
            $p = Read-Host '  Enter the document source path (as shown in the list)'
            if ($p) { Invoke-Tool 'purge_documents.py' @('--source-path', $p) }
            Pause-Menu
        }
        '12' { Invoke-Tool 'purge_documents.py' @('--drop-empty-repositories', '--yes'); Pause-Menu }
        '13' {
            Write-Host '  Running the EKIE test suite ...' -ForegroundColor Cyan
            Push-Location $ServiceRoot
            try { & $VenvPython -m pytest -q } finally { Pop-Location }
            Pause-Menu
        }
        '14' { Invoke-Tool 'setup.py' @(); Pause-Menu }
        '15' { Stop-StartedServices; Pause-Menu }
        { $_ -in @('q', 'Q') } {
            if ($script:Started.Count -gt 0) {
                $ans = Read-Host '  Stop services started from here before quitting? (y/N)'
                if ($ans -match '^(y|yes)$') { Stop-StartedServices }
            }
            Write-Host '  Goodbye.' -ForegroundColor Cyan
            break
        }
        default { Write-Host '  Invalid option.' -ForegroundColor Red; Start-Sleep -Milliseconds 800 }
    }
}
