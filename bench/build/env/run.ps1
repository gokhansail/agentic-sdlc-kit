# Forwards its arguments to tools/build_run.py of the kit repository; the repository path is read from
# runlog\setup.json, written by setup. Copied into the bench folder (ROOT) by setup.
$ErrorActionPreference = 'Stop'
$setupFile = Join-Path $PSScriptRoot 'runlog\setup.json'
if (-not (Test-Path $setupFile)) {
    Write-Error 'runlog\setup.json is missing: run setup first.'
    exit 2
}
$repo = (Get-Content -Raw $setupFile | ConvertFrom-Json).kit_repo
python (Join-Path $repo 'tools\build_run.py') @args --root $PSScriptRoot
exit $LASTEXITCODE
