# Instalação e Configuração do Ambiente Certbot no Windows via WSL
Write-Host "🚀 Iniciando configuração do ambiente para geração do certificado SSL..."

# 1️⃣ Instalar o WSL e uma distribuição Linux (Ubuntu)
Write-Host "🔧 Instalando WSL e Ubuntu..."
wsl --install
Write-Host "WSL e Ubuntu instalados (reinicie se solicitado)"

# Instruções para o usuário entrar no WSL e configurar o Certbot
Write-Host "ℹAgora, abra o WSL (Ubuntu) e execute os seguintes comandos:"
Write-Host "------------------------------------------------------------"
Write-Host "sudo apt update"
Write-Host "sudo apt install certbot"
Write-Host "sudo certbot certonly --manual --preferred-challenges=dns -d seu-dominio.com"
Write-Host ""
Write-Host "Observação: Substitua 'seu-dominio.com' pelo seu domínio real"
Write-Host "O Certbot irá solicitar a criação de registros DNS para validação"
Write-Host ""
Write-Host "Após gerar o certificado, os arquivos estarão em:"
Write-Host "\\wsl$\Ubuntu\etc\letsencrypt\live\seu-dominio.com\"
Write-Host "Depois use o script de cópia e conversão para preparar os arquivos para o Protheus"
Write-Host "------------------------------------------------------------"
Write-Host "Ambiente pronto! Agora execute os comandos no WSL para gerar o certificado."
