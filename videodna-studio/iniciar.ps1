<#
.SYNOPSIS
    Inicia o VideoDNA Studio no Docker Desktop com um comando só.

.DESCRIPTION
    1. Confere se o Docker Desktop está instalado e rodando (e tenta abri-lo).
    2. Baixa as imagens base, uma de cada vez, com novas tentativas.
    3. Constrói as imagens do projeto, uma de cada vez, com novas tentativas.
    4. Sobe os serviços, espera ficarem prontos e abre o navegador.

    Rodar de novo é seguro: o que já foi baixado ou construído é reaproveitado,
    e as imagens são reconstruídas sozinhas quando o código muda (git pull).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\iniciar.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\iniciar.ps1 -Reconstruir
#>
[CmdletBinding()]
param(
    # Reconstrói as imagens do projeto mesmo que pareçam atualizadas.
    [switch]$Reconstruir,
    # Usa MinIO (armazenamento S3) em vez de arquivos locais. O primeiro uso compila o MinIO.
    [switch]$S3,
    # Não abre o navegador no final.
    [switch]$SemNavegador
)

# Compatível com o Windows PowerShell 5.1: nada de &&, ??, ternário ou -Parallel.
Set-StrictMode -Version 2.0
# Programas externos (docker) são checados pelo código de saída, não por exceções.
$ErrorActionPreference = 'Continue'

$Root = $PSScriptRoot
Set-Location -LiteralPath $Root

$ComposeFiles = @('-f', 'docker-compose.yml')
if ($S3) { $ComposeFiles += @('-f', 'docker-compose.s3.yml') }
$ApiUrl = 'http://localhost:8000'
$WebUrl = 'http://localhost:3000'
$OnWindows = ($env:OS -eq 'Windows_NT')

function Write-Step([string]$Message) {
    Write-Host ''
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Info([string]$Message) { Write-Host "    $Message" }

function Write-Warn([string]$Message) { Write-Host "    $Message" -ForegroundColor Yellow }

function Stop-WithError([string]$Message, [string[]]$Hints) {
    Write-Host ''
    Write-Host "ERRO: $Message" -ForegroundColor Red
    foreach ($hint in $Hints) { Write-Host "  - $hint" -ForegroundColor Yellow }
    Write-Host ''
    exit 1
}

# Roda `docker <args>` com novas tentativas e espera crescente: a primeira
# instalação baixa bastante coisa, e uma queda de rede não deve derrubar tudo.
# Sem valor de retorno de propósito: assim a saída do docker vai direto para o
# console, com as barras de progresso.
function Invoke-DockerWithRetry([string]$Description, [string[]]$Arguments, [int]$Attempts = 4) {
    for ($i = 1; $i -le $Attempts; $i++) {
        & docker @Arguments
        if ($LASTEXITCODE -eq 0) { return }
        if ($i -lt $Attempts) {
            $wait = [int][Math]::Min(60, 5 * [Math]::Pow(2, $i - 1))
            Write-Warn "Falhou ($Description). Nova tentativa em $wait s ($i de $Attempts)..."
            Start-Sleep -Seconds $wait
        }
    }
    Stop-WithError "Não foi possível $Description." @(
        'Se a mensagem acima fala de timeout, TLS ou DNS, é a rede: rode este script de novo (ele continua de onde parou).',
        'Persistindo: reinicie o Docker Desktop e, se usar VPN, desligue durante a instalação.',
        'Confira proxy em Docker Desktop > Settings > Resources > Proxies.'
    )
}

function Test-DockerRunning {
    & docker info *> $null
    return ($LASTEXITCODE -eq 0)
}

function Test-ImageExists([string]$Image) {
    & docker image inspect $Image *> $null
    return ($LASTEXITCODE -eq 0)
}

# Revisão do código-fonte gravada como label na imagem, para saber se ela está
# desatualizada depois de um `git pull`. Sem git (download em ZIP), vazio.
function Get-SourceRevision {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { return '' }
    $rev = & git -C $Root rev-parse HEAD 2> $null
    if ($LASTEXITCODE -ne 0 -or -not $rev) { return '' }
    $dirty = & git -C $Root status --porcelain -- . 2> $null
    if (-not $dirty) { return [string]$rev }
    # Local edits: fingerprint them, so each new edit still triggers a rebuild.
    $diff = (& git -C $Root diff HEAD -- . 2> $null | Out-String) + ($dirty | Out-String)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $bytes = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($diff))
    $hex = -join ($bytes[0..5] | ForEach-Object { $_.ToString('x2') })
    return "$rev-modificado-$hex"
}

function Get-ImageRevision([string]$Image) {
    # {{json ...}} evita aspas no template: o PowerShell 5.1 as remove ao chamar programas externos.
    $json = & docker image inspect --format '{{json .Config.Labels}}' $Image 2> $null
    if ($LASTEXITCODE -ne 0 -or -not $json -or $json -eq 'null') { return '' }
    $labels = ($json | Out-String) | ConvertFrom-Json
    $prop = $labels.PSObject.Properties['org.videodna.source']
    if ($prop) { return [string]$prop.Value }
    return ''
}

# Imagens base citadas nos Dockerfiles e no compose (lidas dos arquivos, para não ficarem desatualizadas).
function Get-BaseImages([string[]]$Dockerfiles, [string[]]$ComposeYamls) {
    $images = New-Object System.Collections.Generic.List[string]
    $stages = @{}
    foreach ($file in $Dockerfiles) {
        foreach ($line in Get-Content -LiteralPath $file) {
            if ($line -match '^\s*FROM\s+(\S+)(\s+AS\s+(\S+))?') {
                $image = $Matches[1]
                if ($Matches[3]) { $stages[$Matches[3].ToLower()] = $true }
                if (-not $stages.ContainsKey($image.ToLower()) -and -not $images.Contains($image)) { $images.Add($image) }
            }
        }
    }
    foreach ($file in $ComposeYamls) {
        foreach ($line in Get-Content -LiteralPath $file) {
            if ($line -match '^\s*image:\s*(\S+)\s*$' -and $Matches[1] -notlike 'videodna/*') {
                if (-not $images.Contains($Matches[1])) { $images.Add($Matches[1]) }
            }
        }
    }
    return ,$images.ToArray()
}

Write-Host ''
Write-Host 'VideoDNA Studio — instalação e início' -ForegroundColor Green
Write-Host 'Na primeira vez leva alguns minutos (baixa e prepara tudo). Nas próximas, segundos.'

# --- 1. Docker ------------------------------------------------------------------
Write-Step '1/4  Verificando o Docker Desktop'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Stop-WithError 'O Docker não está instalado neste computador.' @(
        'Instale o Docker Desktop: https://www.docker.com/products/docker-desktop/',
        'Abra o Docker Desktop, espere aparecer "Engine running" e rode este script de novo.'
    )
}
if (-not (Test-DockerRunning)) {
    if ($OnWindows) {
        $desktop = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
        if (Test-Path -LiteralPath $desktop) {
            Write-Info 'O Docker Desktop está fechado. Abrindo...'
            Start-Process -FilePath $desktop | Out-Null
        }
    }
    Write-Info 'Esperando o Docker ficar pronto (até 3 minutos)...'
    $deadline = (Get-Date).AddMinutes(3)
    while (-not (Test-DockerRunning)) {
        if ((Get-Date) -gt $deadline) {
            Stop-WithError 'O Docker Desktop não respondeu.' @(
                'Abra o Docker Desktop e espere aparecer "Engine running".',
                'Se ele mostrar um erro sobre WSL ou virtualização, siga a instrução dele e reinicie o computador.'
            )
        }
        Start-Sleep -Seconds 5
    }
}
& docker compose version *> $null
if ($LASTEXITCODE -ne 0) {
    Stop-WithError 'Este Docker não tem o comando "docker compose".' @('Atualize o Docker Desktop para a versão mais recente.')
}
Write-Info 'Docker pronto.'

# --- 2. Imagens base ---------------------------------------------------------------
Write-Step '2/4  Baixando as imagens base (uma de cada vez)'
$dockerfiles = @('apps/api/Dockerfile', 'apps/web/Dockerfile')
$composeYamls = @('docker-compose.yml')
if ($S3) {
    $dockerfiles += 'infra/minio/Dockerfile'
    $composeYamls += 'docker-compose.s3.yml'
}
foreach ($image in (Get-BaseImages $dockerfiles $composeYamls)) {
    if (Test-ImageExists $image) {
        Write-Info "ok  $image"
        continue
    }
    Write-Info "baixando $image"
    Invoke-DockerWithRetry "baixar a imagem $image" @('pull', $image)
}

# --- 3. Imagens do projeto -----------------------------------------------------------
Write-Step '3/4  Preparando as imagens do VideoDNA Studio'
$revision = Get-SourceRevision
$secretArgs = @()
if ($env:EXTRA_CA_CERT) {
    if (-not (Test-Path -LiteralPath $env:EXTRA_CA_CERT)) {
        Stop-WithError "EXTRA_CA_CERT aponta para um arquivo que não existe: $env:EXTRA_CA_CERT" @('Corrija o caminho ou remova a variável: Remove-Item Env:EXTRA_CA_CERT')
    }
    $secretArgs = @('--secret', "id=ca,src=$env:EXTRA_CA_CERT")
}
$nextApiUrl = $ApiUrl
if ($env:NEXT_PUBLIC_API_URL) { $nextApiUrl = $env:NEXT_PUBLIC_API_URL }

$builds = @(
    @{ Image = 'videodna/api:local'; Label = 'API e worker (Python + FFmpeg)';
       Args = @('-t', 'videodna/api:local', 'apps/api') },
    @{ Image = 'videodna/web:local'; Label = 'site (Next.js)';
       Args = @('-t', 'videodna/web:local', '-f', 'apps/web/Dockerfile', '--build-arg', "NEXT_PUBLIC_API_URL=$nextApiUrl", '.') }
)
if ($S3) {
    $builds += @{ Image = 'videodna/minio:local'; Label = 'MinIO (compila do código-fonte, demora na primeira vez)';
                  Args = @('-t', 'videodna/minio:local', 'infra/minio') }
}
foreach ($build in $builds) {
    $exists = Test-ImageExists $build.Image
    $current = $exists -and $revision -and ((Get-ImageRevision $build.Image) -eq $revision)
    if ($exists -and -not $Reconstruir -and ($current -or -not $revision)) {
        Write-Info "ok  $($build.Image)"
        continue
    }
    if ($exists -and -not $Reconstruir) { Write-Info "O código mudou desde a última vez: atualizando $($build.Label)" }
    else { Write-Info "construindo $($build.Label)" }
    $arguments = @('build', '--label', "org.videodna.source=$revision") + $secretArgs + $build.Args
    Invoke-DockerWithRetry "construir $($build.Label)" $arguments
}

# --- 4. Subir e esperar ----------------------------------------------------------
Write-Step '4/4  Iniciando os serviços'
& docker compose @ComposeFiles up -d --no-build --remove-orphans
if ($LASTEXITCODE -ne 0) {
    Stop-WithError 'Os serviços não subiram.' @(
        'Se a mensagem fala de porta ocupada (3000 ou 8000), feche o programa que usa essa porta e rode de novo.',
        'Para ver detalhes: docker compose logs api --tail 50'
    )
}

function Wait-Url([string]$Url, [string]$What, [int]$Minutes) {
    $deadline = (Get-Date).AddMinutes($Minutes)
    Write-Host -NoNewline "    Aguardando $What"
    while ((Get-Date) -lt $deadline) {
        try {
            $request = [System.Net.WebRequest]::Create($Url)
            $request.Proxy = $null          # localhost nunca passa por proxy
            $request.Timeout = 5000
            $response = $request.GetResponse()
            $code = [int]$response.StatusCode
            $response.Close()
            if ($code -ge 200 -and $code -lt 400) { Write-Host ' ok'; return $true }
        } catch {
            # ainda subindo
        }
        Write-Host -NoNewline '.'
        Start-Sleep -Seconds 3
    }
    Write-Host ''
    return $false
}

if (-not (Wait-Url "$ApiUrl/readyz" 'a API' 4)) {
    & docker compose @ComposeFiles logs api --tail 40
    Stop-WithError 'A API não ficou pronta a tempo.' @(
        'Veja as últimas linhas do log acima.',
        'Tente de novo: o primeiro início pode demorar mais enquanto o banco é criado.'
    )
}
if (-not (Wait-Url $WebUrl 'o site' 2)) {
    & docker compose @ComposeFiles logs web --tail 40
    Stop-WithError 'O site não ficou pronto a tempo.' @('Veja as últimas linhas do log acima.')
}

Write-Host ''
Write-Host "Pronto! O VideoDNA Studio está rodando em $WebUrl" -ForegroundColor Green
Write-Host '  Parar:             powershell -ExecutionPolicy Bypass -File .\parar.ps1'
Write-Host '  Acompanhar o log:  docker compose logs -f api worker'
Write-Host ''
if ($OnWindows -and -not $SemNavegador) { Start-Process $WebUrl }
