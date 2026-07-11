# Launch the deployed Aegis Ascendant build on Windows (PowerShell 5.1).
# Prefers the console wrapper (debug builds) so stdout (e.g. --print-fps) is visible.
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GameArgs)

Set-Location $PSScriptRoot

$exe = Join-Path $PSScriptRoot 'AegisAscendant.console.exe'
if (-not (Test-Path $exe)) {
    $exe = Join-Path $PSScriptRoot 'AegisAscendant.exe'
}
if (-not (Test-Path $exe)) {
    Write-Error "No AegisAscendant executable found in $PSScriptRoot"
    exit 1
}

Write-Host "[run] launching $exe $GameArgs"
if ($GameArgs -and $GameArgs.Count -gt 0) {
    $p = Start-Process -FilePath $exe -ArgumentList $GameArgs -NoNewWindow -PassThru -Wait
} else {
    $p = Start-Process -FilePath $exe -NoNewWindow -PassThru -Wait
}
exit $p.ExitCode
