param(
    [ValidateSet('sequential', 'parallel', 'compare')]
    [string]$Mode = 'compare',
    [ValidateRange(1, 20)]
    [int]$Repeats = 1,
    [ValidateRange(1, 16)]
    [int]$Workers = 4
)

$ErrorActionPreference = 'Stop'
$demoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$demoBenchmark = Join-Path $PSScriptRoot 'benchmark_excel.py'
$demoResults = Join-Path $demoRoot 'output/pmi-paralelismo/demo'
New-Item -ItemType Directory -Force -Path $demoResults | Out-Null
$demoFilename = "${Mode}-$(Get-Date -Format 'yyyyMMdd-HHmmss-fff').json"
Push-Location $demoRoot
try {
    Write-Host "WorkMy: $Mode, $Workers workers, $Repeats repetição(ões)."
    & docker compose run --rm --no-deps `
        --volume "${demoBenchmark}:/app/scripts/benchmark_excel.py:ro" `
        --volume "${demoResults}:/results" `
        fastapi python /app/scripts/benchmark_excel.py `
        --username workmy_carga --reference 2026-10-08 --periods total `
        --repeats $Repeats --mode $Mode --workers $Workers --batch-size 25000 `
        --output "/results/$demoFilename"
    if ($LASTEXITCODE -ne 0) {
        throw "O benchmark falhou. Conferir o erro acima."
    }
    Write-Host "Evidência salva em: $(Join-Path $demoResults $demoFilename)"
} finally {
    Pop-Location
}
