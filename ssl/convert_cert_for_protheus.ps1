# Script para copiar e converter certificados Let's Encrypt para uso no Protheus
Write-Host "🚀 Iniciando cópia e conversão do certificado SSL para o Protheus..."

# Variáveis de caminho
$wslCertPath = "\\wsl$\Ubuntu\etc\letsencrypt\live\seu-dominio.com"
$windowsDestPath = "C:\totvs\certs"
$certFile = "cert.pem"
$keyFile = "privkey.pem"
$convertedKeyFile = "protheus.key"

# Verifica se o diretório de destino existe
if (!(Test-Path $windowsDestPath)) {
    Write-Host "📂 Criando diretório $windowsDestPath"
    New-Item -ItemType Directory -Path $windowsDestPath
}

# Copia os arquivos do WSL para o Windows
Write-Host "Copiando arquivos do WSL para o Windows..."
Copy-Item "$wslCertPath\$certFile" "$windowsDestPath\$certFile" -Force
Copy-Item "$wslCertPath\$keyFile" "$windowsDestPath\$keyFile" -Force

# Caminhos completos para os arquivos no Windows
$keyInputPath = "$windowsDestPath\$keyFile"
$keyOutputPath = "$windowsDestPath\$convertedKeyFile"

# Converte a chave privada para PKCS#1 usando OpenSSL (precisa estar instalado e no PATH)
Write-Host "Convertendo chave privada para PKCS#1..."
$opensslCommand = "openssl rsa -in `"$keyInputPath`" -out `"$keyOutputPath`""
Invoke-Expression $opensslCommand

Write-Host "Certificado pronto para uso no Protheus:"
Write-Host " - Certificado: $windowsDestPath\$certFile"
Write-Host " - Chave: $windowsDestPath\$convertedKeyFile"
