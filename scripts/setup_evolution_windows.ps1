$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repositoryRoot

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
}

$environmentText = Get-Content -LiteralPath ".env" -Raw
if ($environmentText -match "AUTHENTICATION_API_KEY=change-me") {
    $apiKey = [Guid]::NewGuid().ToString("N")
    $environmentText = $environmentText -replace "AUTHENTICATION_API_KEY=change-me", "AUTHENTICATION_API_KEY=$apiKey"
}
if ($environmentText -match "(?m)^WEBHOOK_SECRET=[\t ]*\r?$") {
    $webhookSecret = [Guid]::NewGuid().ToString("N")
    $environmentText = $environmentText -replace "(?m)^WEBHOOK_SECRET=[^\r\n]*", "WEBHOOK_SECRET=$webhookSecret"
}
$environmentText | Set-Content -LiteralPath ".env" -Encoding utf8

$previousErrorPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$wslOutput = & wsl.exe --status 2>&1 | Out-String
$wslExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorPreference
$wslText = $wslOutput -replace "`0", ""
if ($wslText -match "E_ACCESSDENIED|Acesso negado|Access is denied") {
    throw "WSL esta instalado, mas o Windows negou acesso nesta sessao. Reinicie o Windows e execute este script em um PowerShell aberto pelo seu usuario."
}
if ($wslExitCode -ne 0 -or $wslText -match "nao esta instalado|não está instalado") {
    throw "WSL nao esta instalado. Abra PowerShell como administrador, execute 'wsl --install' e reinicie o Windows."
}

$perUserDesktop = Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\Docker Desktop.exe"
$allUsersDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
$dockerDesktop = if (Test-Path -LiteralPath $perUserDesktop) {
    $perUserDesktop
} elseif (Test-Path -LiteralPath $allUsersDesktop) {
    $allUsersDesktop
} else {
    $null
}

if (-not $dockerDesktop) {
    throw "Docker Desktop nao foi encontrado. Instale pelo site oficial e execute este script novamente."
}

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCommand) {
    $perUserDocker = Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\docker.exe"
    $allUsersDocker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    if (Test-Path -LiteralPath $perUserDocker) {
        $env:PATH = "$(Split-Path -Parent $perUserDocker);$env:PATH"
    } elseif (Test-Path -LiteralPath $allUsersDocker) {
        $env:PATH = "$(Split-Path -Parent $allUsersDocker);$env:PATH"
    } else {
        Start-Process -FilePath $dockerDesktop
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            Start-Sleep -Seconds 2
            if (Test-Path -LiteralPath $perUserDocker) {
                $env:PATH = "$(Split-Path -Parent $perUserDocker);$env:PATH"
                break
            }
            if (Test-Path -LiteralPath $allUsersDocker) {
                $env:PATH = "$(Split-Path -Parent $allUsersDocker);$env:PATH"
                break
            }
        }
    }
}

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCommand) {
    throw "O Docker Desktop foi encontrado, mas o comando docker nao ficou disponivel. Abra o Docker Desktop pelo menu Iniciar, conclua a configuracao inicial e execute este script novamente."
}

$dockerReady = $false
$previousErrorPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    docker version *> $null
    if ($LASTEXITCODE -eq 0) {
        $dockerReady = $true
        break
    }
    if ($attempt -eq 0) {
        Start-Process -FilePath $dockerDesktop
    }
    Start-Sleep -Seconds 2
}
$ErrorActionPreference = $previousErrorPreference
if (-not $dockerReady) {
    throw "Docker Desktop nao ficou pronto em 120 segundos. Abra o aplicativo, conclua a tela inicial e tente novamente."
}

docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps

Write-Host ""
Write-Host "Evolution iniciada. Abra: http://localhost:8080/manager"
Write-Host "Crie/conecte a instancia 'affiliate' usando WHATSAPP-BAILEYS."
Write-Host "Deixe a opcao de ignorar grupos desligada."
Write-Host "Depois inicie o FastAPI e execute scripts.configure_webhook."
