#!/bin/bash

# Protheus Webhook Hub - Script de Instalação
# Autor: Fernando Vernier

echo "🚀 Protheus Webhook Hub - Instalação"
echo "======================================"
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado!"
    echo "   Instale o Docker antes de continuar:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não encontrado!"
    echo "   Instale o Docker Compose antes de continuar:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker e Docker Compose encontrados"
echo ""

# Criar .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    cp .env.example .env
    echo "✅ Arquivo .env criado"
else
    echo "ℹ️  Arquivo .env já existe"
fi

echo ""
echo "🐳 Iniciando containers..."
docker-compose up -d

echo ""
echo "⏳ Aguardando serviços iniciarem (30 segundos)..."
sleep 30

echo ""
echo "🔍 Verificando status dos containers..."
docker-compose ps

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "📊 Acesse o painel web em: http://localhost:4200"
echo "🔧 API disponível em: http://localhost:8000"
echo "📚 Documentação da API: http://localhost:8000/docs"
echo ""
echo "📖 Próximos passos:"
echo "   1. Acesse http://localhost:4200"
echo "   2. Configure uma integração (Slack/Teams)"
echo "   3. Compile o fonte ADVPL no Protheus"
echo "   4. Configure o parâmetro MV_WEBHURL"
echo ""
echo "💡 Dica: Leia o QUICKSTART.md para começar!"
echo ""
echo "🆘 Problemas?"
echo "   - Ver logs: docker-compose logs -f"
echo "   - Reiniciar: docker-compose restart"
echo "   - Parar: docker-compose down"
echo ""
echo "🙏 Desenvolvido por Fernando Vernier"
echo "   https://github.com/ftvernier/erp-solutions"
