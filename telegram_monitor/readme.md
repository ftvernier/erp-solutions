# 🤖 Monitor Protheus - Alertas Inteligentes via Telegram

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-blue.svg)](https://core.telegram.org/bots/api)
[![ERP](https://img.shields.io/badge/ERP-TOTVS%20Protheus-green.svg)](https://www.totvs.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Sistema de alertas automáticos que monitora seu ERP Protheus e envia notificações em tempo real via Telegram para grupos de gestores.**

## 🎯 O Problema

- ❌ Gestores precisam entrar no Protheus constantemente para verificar informações
- ❌ Problemas críticos (estoque baixo, inadimplência) passam despercebidos
- ❌ Relatórios são gerados manualmente e enviados por email
- ❌ Falta de visibilidade em tempo real para a equipe de gestão
- ❌ Perda de tempo com consultas repetitivas no sistema

## ✅ A Solução

**Monitor Protheus** é um sistema que:
- 🔔 **Monitora automaticamente** seu banco do Protheus
- 📱 **Envia alertas instantâneos** via Telegram
- 👥 **Notifica grupos inteiros** de gestores simultaneamente
- ⚡ **Funciona 24/7** sem intervenção manual
- 🎯 **Alertas inteligentes** segmentados por área

## 🚀 Funcionalidades

### 📊 Alertas Automáticos
- **Estoque Baixo**: Produtos abaixo do mínimo
- **Vendas Diárias**: Relatórios de faturamento e metas
- **Inadimplência**: Clientes em atraso
- **Metas Batidas**: Celebrações automáticas
- **Status do Sistema**: Monitoramento de saúde

### 🎯 Benefícios
- ⚡ **Tempo Real**: Informações instantâneas
- 👥 **Colaborativo**: Grupos podem discutir os alertas
- 📱 **Mobile First**: Funciona em qualquer dispositivo
- 🆓 **Gratuito**: Usando API gratuita do Telegram
- 🔧 **Personalizável**: Fácil de adaptar para suas necessidades

## 📋 Pré-requisitos

- Python 3.7 ou superior
- Acesso ao banco de dados do Protheus
- Conta no Telegram
- Biblioteca `requests` do Python

## 🛠️ Instalação e Configuração

### Passo 1: Instalar Dependências

```bash
# Instalar dependências necessárias
pip install requests pyodbc python-dotenv
```

### Passo 2: Criar Bot no Telegram

1. **Abra o Telegram** e procure por `@BotFather`
2. **Inicie conversa** e digite `/newbot`
3. **Escolha um nome** para seu bot: `Monitor Protheus`
4. **Escolha um username**: `monitor_protheus_bot` (deve terminar com "_bot")
5. **Copie o token** fornecido (ex: `987654321:AAEhF0dK-SJl8oO3Kd9sEf_GhI2jKlMnOp`)

```
🤖 Exemplo de resposta do BotFather:
Done! Congratulations on your new bot. You have access to the HTTP API via the following token:

987654321:AAEhF0dK-SJl8oO3Kd9sEf_GhI2jKlMnOp

Keep your token secure and store it safely, it can be used by anyone to control your bot.
```

### Passo 3: Criar Grupo e Configurar Bot

1. **Crie um novo grupo** no Telegram
   - Nome sugerido: "📊 Alertas Protheus - Gestão"
   
2. **Adicione o bot ao grupo**
   - Vá em "Adicionar Membros"
   - Procure pelo username do seu bot
   - Adicione ao grupo

3. **Dar permissões de admin ao bot** (IMPORTANTE)
   - Clique no nome do grupo
   - Vá em "Editar"
   - Clique em "Administradores"
   - Clique no seu bot
   - Marque: ✅ "Enviar mensagens"
   - Salve as alterações

4. **Adicione os gestores** que devem receber os alertas

### Passo 4: Descobrir o Chat ID do Grupo

1. **Envie uma mensagem qualquer no grupo** (ex: "Teste")

2. **Execute o script para capturar o ID:**

```python
# id.py
import requests

def obter_chat_id():
    bot_token = "SEU_TOKEN_AQUI"  # Token do BotFather
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)
    print(response.json())

obter_chat_id()
```

3. **Execute o script:**
```bash
python3 id.py
```

4. **Copie o Chat ID** (será um número negativo, ex: `-1001567890123`)

```json
{
  "ok": true,
  "result": [
    {
      "update_id": 123456,
      "message": {
        "message_id": 1,
        "from": {"id": 987654321, "first_name": "Seu Nome"},
        "chat": {"id": -1001567890123, "type": "group"},  ← ESTE É O CHAT ID
        "date": 1234567890,
        "text": "Teste"
      }
    }
  ]
}
```

### Passo 5: Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# .env
TELEGRAM_TOKEN=987654321:AAEhF0dK-SJl8oO3Kd9sEf_GhI2jKlMnOp
TELEGRAM_CHAT_ID=-1001567890123

# Banco Protheus
DB_SERVER=seu_servidor_protheus
DB_DATABASE=PROTHEUS
DB_USERNAME=usuario
DB_PASSWORD=senha
```

### Passo 6: Teste a Configuração

Execute o script de teste para verificar se tudo está funcionando:

```bash
python3 teste_grupo.py
```

Se tudo estiver correto, você receberá uma mensagem no grupo do Telegram! 🎉

## 📁 Estrutura do Projeto

```
monitor-protheus/
├── README.md
├── .env                    # Configurações (não committar!)
├── .gitignore
├── requirements.txt
├── id.py                   # Script para capturar Chat ID
├── teste_grupo.py          # Script de teste dos alertas
├── config.py               # Configurações do sistema
├── database.py             # Conexão com Protheus
├── alertas.py              # Lógica dos alertas
├── telegram_bot.py         # Funções do Telegram
└── main.py                 # Script principal
```

## 🎮 Como Usar

### Teste Imediato
```bash
# Teste básico
python3 teste_grupo.py

# Escolha a opção 5 para demo completo
```

### Execução Automática
```bash
# Executar monitoramento contínuo
python3 main.py
```

### Exemplos de Alertas

#### 🚨 Alerta de Estoque Baixo
```
🚨 ALERTA CRÍTICO - ESTOQUE BAIXO

📦 Produtos Abaixo do Mínimo:

🔴 MOUSE001 - Mouse Gamer RGB
   └ Atual: 2 unidades | Mínimo: 10
   └ 📍 Filial 01 - MATRIZ

⚠️ AÇÃO NECESSÁRIA: Gerar pedidos de compra urgentes
⏰ 25/06/2025 às 14:30:15
```

#### 💰 Relatório de Vendas
```
💰 RELATÓRIO DE VENDAS DIÁRIO

📅 25/06/2025
💵 Faturamento: R$ 42.847,65
🎯 Performance: 122,4% da meta ✅

🏆 TOP VENDEDORES:
1️⃣ João Silva - R$ 15.450,00 (36,1%)
2️⃣ Maria Santos - R$ 12.230,50 (28,5%)
```

## ⚙️ Configurações Avançadas

### Horários dos Alertas
```python
# config.py
HORARIOS_VENDAS = [9, 14, 18]  # 9h, 14h, 18h
INTERVALO_ESTOQUE = 3600       # 1 hora
DIA_COBRANCA = 1              # Segunda-feira
```

### Múltiplos Grupos
```python
DESTINATARIOS = {
    "gestao_geral": "-1001567890123",
    "financeiro": "-1001234567890",
    "vendas": "-1001987654321",
    "estoque": "-1001122334455"
}
```

## 🔧 Personalização

### Adicionar Novo Alerta
```python
def alerta_personalizado():
    query = "SELECT * FROM SUA_TABELA WHERE CONDICAO"
    # Sua lógica aqui
    
    mensagem = f"""
    🔔 SEU ALERTA PERSONALIZADO
    
    Dados: {resultado}
    ⏰ {datetime.now()}
    """
    
    enviar_telegram(mensagem)
```

### Integração com Outras Tabelas
```python
# Consultas personalizadas para diferentes módulos
QUERIES = {
    "estoque": "SELECT B1_COD, B2_QATU FROM SB1010...",
    "vendas": "SELECT F2_VALBRUT FROM SF2010...",
    "financeiro": "SELECT E1_SALDO FROM SE1010..."
}
```

## 🚨 Solução de Problemas

### ❌ "Chat not found"
- Verifique se o bot foi adicionado ao grupo
- Confirme se o Chat ID está correto (deve ser negativo)
- Certifique-se que o bot tem permissão de admin

### ❌ "Forbidden: bot was kicked from the group"
- Re-adicione o bot ao grupo
- Dê permissões de administrador
- Execute novamente o script

### ❌ "Unauthorized"
- Verifique se o token está correto
- Regenere o token no @BotFather se necessário

### ❌ Conexão com Banco
- Verifique as credenciais do banco
- Confirme se o servidor está acessível
- Teste a conexão manualmente

## 🔐 Segurança

- ✅ **Token seguro**: Nunca commite o token no Git
- ✅ **Variáveis ambiente**: Use arquivo `.env`
- ✅ **Regeneração**: Regenere tokens periodicamente
- ✅ **Permissões**: Bot apenas com permissões necessárias

## 📈 Roadmap

- [ ] Interface web para configuração
- [ ] Comandos interativos (/vendas, /estoque)
- [ ] Alertas por WhatsApp
- [ ] Dashboard visual
- [ ] Integração com Power BI
- [ ] Notificações por email backup
- [ ] Alertas baseados em IA/ML

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## 👨‍💻 Autor

**Fernando Vernier**
- GitHub: https://github.com/ftvernier/erp-solutions
- LinkedIn: https://www.linkedin.com/in/fernando-v-10758522/

## 🙏 Agradecimentos

- Comunidade Protheus pela troca de experiências
- Equipe de desenvolvimento que colaborou nos testes

## ⭐ Dê uma Estrela!

Se este projeto te ajudou, considere dar uma ⭐ no GitHub!

---

## 📞 Suporte

Encontrou algum problema? 
- 🐛 Abra uma [Issue](https://github.com/seu-usuario/monitor-protheus/issues)
- 💬 Entre em contato via LinkedIn
- 📧 Envie um email

---

<div align="center">

**🚀 Transforme seu Protheus em um sistema inteligente que fala com você! 🚀**

</div>
