# 🔒 Certificados SSL Let's Encrypt para Protheus no Windows com WSL

Scripts para:
- Instalar WSL e Certbot para gerar certificados SSL
- Copiar e converter os certificados para o formato exigido pelo Protheus (PKCS#1)

## 🚀 Uso
1️⃣ Execute `setup_certbot.ps1` para instalar o WSL, Certbot e gerar o certificado.  
2️⃣ Execute `convert_cert_for_protheus.ps1` para copiar e converter os arquivos para o Protheus.

📌 O Certbot gera os arquivos em `\\wsl$\Ubuntu\etc\letsencrypt\live\seu-dominio.com\`.
