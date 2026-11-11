$ErrorActionPreference = "Stop"

Write-Host "Instalando WSL. O Windows pode solicitar uma reinicializacao."
wsl.exe --install

if ($LASTEXITCODE -ne 0) {
    throw "O Windows nao concluiu a instalacao do WSL. Confirme que este PowerShell foi aberto como administrador."
}

Write-Host "WSL instalado. Reinicie o Windows antes de instalar o Docker Desktop."
Read-Host "Pressione Enter para fechar"
