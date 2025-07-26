# 🔐 Portal de Reset de Senha - Protheus

Portal web para reset de senha do ERP Protheus usando a API SCIM oficial da TOTVS.

## ✨ Funcionalidades

- 🔒 Reset seguro com código de verificação por email
- ⚡ Interface responsiva que funciona no celular
- 🛡️ Rate limiting para prevenir ataques
- 📧 Envio automático de códigos por email
- ⏱️ Códigos temporários com expiração de 15 minutos
- 🐳 Deploy fácil com Docker

## 🚀 Instalação

### Docker (Recomendado)
```bash
cp .env.example .env
nano .env  # Configure suas credenciais
docker-compose up -d
curl http://localhost:8000/health
```

### Python Local
```bash
pip install -r requirements.txt
export PROTHEUS_URL="http://seu-servidor:8080/rest"
export PROTHEUS_USER="admin"
export PROTHEUS_PASS="sua-senha"
export SMTP_USER="seu-email@gmail.com"
export SMTP_PASS="sua-senha-app"
uvicorn main:app --host 0.0.0.0 --port 8000
```

## ⚙️ Configuração Gmail

1. Ative 2FA no Gmail
2. Gere senha de app: https://myaccount.google.com/apppasswords
3. Use essa senha no `SMTP_PASS`

## 🔧 Teste

```bash
curl http://localhost:8000/health
# Deve retornar: {"status": "ok", "protheus_connection": "connected"}
```

---

**Desenvolvido por [Fernando Vernier](https://www.linkedin.com/in/fernando-v-10758522/)**
