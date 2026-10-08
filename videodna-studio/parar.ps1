<#
.SYNOPSIS
    Para o VideoDNA Studio. Seus projetos e vídeos continuam guardados.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\parar.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\parar.ps1 -ApagarDados
#>
[CmdletBinding()]
param(
    # Apaga também o banco e todos os vídeos enviados (pede confirmação).
    [switch]$ApagarDados
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot

# Inclui o arquivo do MinIO para parar tudo, em qualquer modo em que tenha sido iniciado.
$files = @('-f', 'docker-compose.yml', '-f', 'docker-compose.s3.yml')

if ($ApagarDados) {
    Write-Host 'Isto apaga TODOS os projetos, vídeos enviados e resultados gerados.' -ForegroundColor Yellow
    $answer = Read-Host 'Digite APAGAR para confirmar'
    if ($answer -cne 'APAGAR') {
        Write-Host 'Nada foi apagado.'
        exit 0
    }
    & docker compose @files down --volumes --remove-orphans
} else {
    & docker compose @files down --remove-orphans
}
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Não foi possível parar os serviços. O Docker Desktop está aberto?' -ForegroundColor Red
    exit 1
}
Write-Host ''
if ($ApagarDados) {
    Write-Host 'VideoDNA Studio parado e dados apagados.' -ForegroundColor Green
} else {
    Write-Host 'VideoDNA Studio parado. Seus projetos continuam guardados.' -ForegroundColor Green
}
Write-Host 'Para iniciar de novo: powershell -ExecutionPolicy Bypass -File .\iniciar.ps1'
