param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("backend-tests", "frontend-build", "frontend-ui", "smoke", "cleanup")]
    [string]$Task
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $Root "backend\.venv\Scripts\python.exe"
$Pnpm = "pnpm"
$BundledRuntime = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies"
$BundledPython = Join-Path $BundledRuntime "python\python.exe"
$BundledPnpm = Join-Path $BundledRuntime "bin\pnpm.cmd"
$BundledNodeBin = Join-Path $BundledRuntime "node\bin"

if (-not (Test-Path $Python)) {
    if (Test-Path $BundledPython) {
        $Python = $BundledPython
    } else {
        $Python = "python"
    }
}

if (Test-Path $BundledPnpm) {
    $Pnpm = $BundledPnpm
    if (Test-Path $BundledNodeBin) {
        $env:PATH = "$BundledNodeBin;$env:PATH"
    }
}

switch ($Task) {
    "backend-tests" {
        Push-Location (Join-Path $Root "backend")
        & $Python -m pytest -q
        Pop-Location
    }
    "frontend-build" {
        Push-Location (Join-Path $Root "frontend")
        & $Pnpm build
        Pop-Location
    }
    "frontend-ui" {
        Push-Location (Join-Path $Root "frontend")
        & $Pnpm test:ui
        Pop-Location
    }
    "smoke" {
        & $Python (Join-Path $Root "scripts\smoke_check.py") --frontend
    }
    "cleanup" {
        & $Python (Join-Path $Root "scripts\cleanup_workspace.py")
    }
}
