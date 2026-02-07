#!/bin/bash
# Dashboard ERP Protheus 2.0 - Script de Instalação
# Autor: Fernando Vernier - https://www.linkedin.com/in/fernando-v-10758522/

set -e

echo "=========================================="
echo "Dashboard ERP Protheus 2.0 - Instalação"
echo "=========================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verifica se está rodando como root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ Não execute este script como root!${NC}"
    exit 1
fi

# Verifica Python
echo -e "${YELLOW}🔍 Verificando Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 não encontrado. Instale primeiro.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} encontrado${NC}"

# Verifica pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 não encontrado. Instale primeiro.${NC}"
    exit 1
fi

# Cria diretório de instalação
INSTALL_DIR="/opt/dashboard-erp-v2"
echo ""
echo -e "${YELLOW}📁 Diretório de instalação: ${INSTALL_DIR}${NC}"

if [ -d "$INSTALL_DIR" ]; then
    read -p "Diretório já existe. Deseja sobrescrever? (s/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${RED}❌ Instalação cancelada${NC}"
        exit 1
    fi
    sudo rm -rf "$INSTALL_DIR"
fi

# Cria diretório
echo -e "${YELLOW}📦 Criando diretório...${NC}"
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r . "$INSTALL_DIR/"
sudo chown -R $USER:$USER "$INSTALL_DIR"

cd "$INSTALL_DIR"

# Cria ambiente virtual
echo ""
echo -e "${YELLOW}🐍 Criando ambiente virtual...${NC}"
python3 -m venv venv
source venv/bin/activate

# Instala dependências
echo ""
echo -e "${YELLOW}📚 Instalando dependências...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Cria arquivo .env se não existir
if [ ! -f "dashboard.env" ]; then
    echo ""
    echo -e "${YELLOW}⚙️  Criando arquivo de configuração...${NC}"
    cp dashboard.env.example dashboard.env
    
    # Gera SECRET_KEY aleatória
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
    sed -i "s/seu-secret-key-super-seguro-aqui-mude-isso/$SECRET_KEY/" dashboard.env
    
    echo -e "${GREEN}✅ Arquivo dashboard.env criado${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANTE: Edite dashboard.env e altere as senhas!${NC}"
fi

# Inicializa banco de dados
echo ""
echo -e "${YELLOW}🗄️  Inicializando banco de dados...${NC}"
python3 -c "from models import Database; Database()"
echo -e "${GREEN}✅ Banco de dados criado${NC}"

# Configura sudoers
echo ""
echo -e "${YELLOW}🔐 Configurando sudoers...${NC}"
SUDOERS_FILE="/etc/sudoers.d/dashboard-erp"

SUDOERS_CONTENT="# Dashboard ERP Protheus
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl start *.service
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop *.service
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart *.service
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl is-active *.service
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl show *.service
$USER ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u *.service *
$USER ALL=(ALL) NOPASSWD: /usr/bin/kill -9 *"

echo "$SUDOERS_CONTENT" | sudo tee "$SUDOERS_FILE" > /dev/null
sudo chmod 440 "$SUDOERS_FILE"

echo -e "${GREEN}✅ Sudoers configurado${NC}"

# Cria script de inicialização
echo ""
echo -e "${YELLOW}🚀 Criando script de inicialização...${NC}"

cat > start.sh << 'EOF'
#!/bin/bash
cd /opt/dashboard-erp-v2
source venv/bin/activate
python3 app.py
EOF

chmod +x start.sh

# Cria serviço systemd
echo ""
read -p "Deseja criar serviço systemd para inicialização automática? (s/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    SYSTEMD_SERVICE="[Unit]
Description=Dashboard ERP Protheus 2.0
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/dashboard-erp-v2
ExecStart=/opt/dashboard-erp-v2/venv/bin/python /opt/dashboard-erp-v2/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"

    echo "$SYSTEMD_SERVICE" | sudo tee /etc/systemd/system/dashboard-erp.service > /dev/null
    sudo systemctl daemon-reload
    sudo systemctl enable dashboard-erp.service
    
    echo -e "${GREEN}✅ Serviço systemd criado${NC}"
    echo -e "${YELLOW}Para iniciar: sudo systemctl start dashboard-erp${NC}"
fi

# Resumo final
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Instalação concluída com sucesso!${NC}"
echo "=========================================="
echo ""
echo -e "📍 Diretório: ${INSTALL_DIR}"
echo -e "🌐 Acesse: http://$(hostname -I | awk '{print $1}'):8050"
echo ""
echo -e "${YELLOW}⚠️  PRÓXIMOS PASSOS:${NC}"
echo -e "1. Edite ${INSTALL_DIR}/dashboard.env"
echo -e "2. Altere as senhas padrão"
echo -e "3. Execute: cd ${INSTALL_DIR} && ./start.sh"
echo ""
echo -e "${GREEN}🎉 Aproveite o Dashboard ERP Protheus 2.0!${NC}"
echo ""
