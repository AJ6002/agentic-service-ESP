<#
.SYNOPSIS
    Automated Newman Test Runner for ESP APM Platform
.DESCRIPTION
    Runs standalone Postman collections against real Server 184 (:8085 KB, :8090 Data/Cards/ML)
    and Local Agent Service (:8091). Pinpoints API failures vs Gateway vs Agent Service issues.
.PARAMETER Suite
    Which test suite to run: 'kb', 'historian', 'ml', 'agent', or 'all' (default: 'all')
#>
param(
    [ValidateSet('kb', 'historian', 'ml', 'agent', 'all')]
    [string]$Suite = 'all'
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvFile = Join-Path $ScriptDir "newman_environment.json"

# Check if newman is available
$NewmanCmd = Get-Command newman -ErrorAction SilentlyContinue
if (-not $NewmanCmd) {
    $NpxCmd = Get-Command npx -ErrorAction SilentlyContinue
    if ($NpxCmd) {
        $RunnerPrefix = "npx newman run"
    } else {
        Write-Error "Neither 'newman' nor 'npx' found in PATH. Please run 'npm install -g newman' or install Node.js."
        exit 1
    }
} else {
    $RunnerPrefix = "newman run"
}

function Run-Collection($CollectionName, $File) {
    Write-Host "`n========================================================" -ForegroundColor Cyan
    Write-Host " Running Suite: $CollectionName" -ForegroundColor Cyan
    Write-Host " File: $File" -ForegroundColor DarkCyan
    Write-Host "========================================================`n" -ForegroundColor Cyan
    
    $FilePath = Join-Path $ScriptDir $File
    $cmd = "$RunnerPrefix `"$FilePath`" -e `"$EnvFile`" --color on"
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n[FAIL] Suite $CollectionName reported failures!" -ForegroundColor Red
        return $false
    }
    Write-Host "`n[PASS] Suite $CollectionName completed successfully!" -ForegroundColor Green
    return $true
}

$AllPassed = $true

if ($Suite -eq 'kb' -or $Suite -eq 'all') {
    $res = Run-Collection "01. Knowledge Base Service (:8085)" "01_knowledge_base_suite.postman_collection.json"
    if (-not $res) { $AllPassed = $false }
}

if ($Suite -eq 'historian' -or $Suite -eq 'all') {
    $res = Run-Collection "02. Historian, Live & Events (:8090)" "02_historian_live_events_suite.postman_collection.json"
    if (-not $res) { $AllPassed = $false }
}

if ($Suite -eq 'ml' -or $Suite -eq 'all') {
    $res = Run-Collection "03. ML Diagnostics, KPIs & Cards (:8090)" "03_ml_kpi_cards_suite.postman_collection.json"
    if (-not $res) { $AllPassed = $false }
}

if ($Suite -eq 'agent' -or $Suite -eq 'all') {
    $res = Run-Collection "04. Agent Service End-to-End (:8091)" "04_agent_service_query_suite.postman_collection.json"
    if (-not $res) { $AllPassed = $false }
}

Write-Host "`n========================================================" -ForegroundColor Cyan
if ($AllPassed) {
    Write-Host " ALL TEST SUITES PASSED! Platform APIs Healthy." -ForegroundColor Green
} else {
    Write-Host " TEST SUITE RUN COMPLETED WITH FAILURES." -ForegroundColor Red
    Write-Host " Standalone runs isolate whether failure is on Server 184 or Agent Service." -ForegroundColor Yellow
}
Write-Host "========================================================`n" -ForegroundColor Cyan
