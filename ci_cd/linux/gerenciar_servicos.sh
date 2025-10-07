#!/bin/bash

# Função para iniciar os serviços
iniciar_servicos() {
    echo "Iniciando serviços..."
    for servico in appserver_broker_rest appserver_broker_webapp appserver_portal_01 appserver_compilar appserver_slave_01 appserver_slave_02 appserver_slave_03 appserver_slave_04 appserver_slave_05 appserver_slave_06 appserver_slave_07 appserver_slave_08 appserver_slave_09 appserver_slave_10 
    do
        sudo systemctl start "$servico.service"
        if [ $? -ne 0 ]; then
            echo "Erro ao iniciar o serviço $servico"
        else
            # Monitorar até que o serviço esteja ativo
            while [ "$(systemctl is-active "$servico.service")" != "active" ]; do
                sleep 1  # Aguarde 1 segundo antes de verificar novamente
            done
            echo "Serviço $servico iniciado com sucesso."
        fi
    done
}

# Função para parar os serviços com monitoramento e forçar encerramento após 30 segundos
parar_servicos() {
    echo "Parando serviços..."
    for servico in monitorar_webapp appserver_broker_rest appserver_broker_webapp appserver_portal_01 appserver_compilar appserver_slave_01 appserver_slave_02 appserver_slave_03 appserver_slave_04 appserver_slave_05 appserver_slave_06 appserver_slave_07 appserver_slave_08 appserver_slave_09 appserver_slave_10
    do
        sudo systemctl stop "$servico.service"
        if [ $? -ne 0 ]; then
            echo "Erro ao parar o serviço $servico"
        else
            # Monitorar até que o serviço esteja inativo, com limite de 30 segundos
            tempo=0
            while [ "$(systemctl is-active "$servico.service")" != "inactive" ]; do
                sleep 1
                tempo=$((tempo + 1))
                if [ $tempo -ge 30 ]; then
                    echo "Tempo limite atingido ao parar o serviço $servico. Forçando encerramento..."
                    # Obter o PID do serviço e forçar o encerramento
                    pid=$(systemctl show -p MainPID --value "$servico.service")
                    if [ -n "$pid" ] && [ "$pid" -ne 0 ]; then
                        sudo kill -9 "$pid"
                        echo "Serviço $servico forçado a parar com kill -9."
                    else
                        echo "Não foi possível obter o PID para $servico. Tentando novamente..."
                        # Tentar encontrar o PID usando pgrep como fallback
                        pid=$(pgrep -f "$servico")
                        if [ -n "$pid" ]; then
                            sudo kill -9 "$pid"
                            echo "Serviço $servico forçado a parar com kill -9 usando pgrep."
                        else
                            echo "Falha ao identificar o processo para $servico."
                        fi
                    fi
                    break
                fi
            done
            # Verificar o status final após o tempo limite
            if [ "$(systemctl is-active "$servico.service")" = "inactive" ]; then
                echo "Serviço $servico parado com sucesso."
            else
                echo "Falha ao parar o serviço $servico. Status atual: $(systemctl is-active "$servico.service")"
            fi
        fi
    done
}

# Função para iniciar somente o appserver_compilar (modo exclusivo)
modo_exclusivo() {
    echo "Iniciando modo exclusivo com appserver_compilar..."

    servico="appserver_compilar"
    sudo systemctl start "$servico.service"
    if [ $? -ne 0 ]; then
        echo "Erro ao iniciar o serviço $servico"
    else
        while [ "$(systemctl is-active "$servico.service")" != "active" ]; do
            sleep 1
        done
        echo "Serviço $servico iniciado em modo exclusivo com sucesso."
    fi
}

# Função para reiniciar os serviços
reiniciar_servicos() {
    echo "Reiniciando serviços..."
    parar_servicos
    echo "Aguardando 2 segundos antes de iniciar novamente..."
    sleep 2
    iniciar_servicos
}

# Verificar argumento de entrada
case "$1" in
    iniciar)
        iniciar_servicos
        ;;
    parar)
        parar_servicos
        ;;
    reiniciar)
        reiniciar_servicos
        ;;
    exclusivo)
        modo_exclusivo
        ;;
    *)
        echo "Uso: $0 {iniciar|parar|reiniciar|exclusivo}"
        echo ""
        echo "Comandos disponíveis:"
        echo "  iniciar    - Inicia todos os serviços"
        echo "  parar      - Para todos os serviços"
        echo "  reiniciar  - Reinicia todos os serviços"
        echo "  exclusivo  - Inicia apenas appserver_compilar"
        exit 1
        ;;
esac
