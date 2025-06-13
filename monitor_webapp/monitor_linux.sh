#!/bin/bash

# Configurações
URL="https://seuprotheus.com.br/webapp"
LOG="/var/log/monitor_webapp.log"
TEMPO_LIMITE=5  # tempo em segundos para efetuar o monitoramento

# Configurações de E-mail
EMAIL_TO="destinatario@empresa.com"
EMAIL_FROM="monitor@empresa.com"

# Função para enviar e-mail
send_email() {
    local subject="$1"
    local body="$2"
    
    # Método 1: Usando mail (mais comum)
    echo "$body" | mail -s "$subject" -r "$EMAIL_FROM" "$EMAIL_TO"
    
    # Método 2: Usando sendmail (alternativa)
    # {
    #     echo "To: $EMAIL_TO"
    #     echo "From: $EMAIL_FROM"
    #     echo "Subject: $subject"
    #     echo ""
    #     echo "$body"
    # } | sendmail -t
    
    # Método 3: Usando ssmtp (para Gmail/Office365)
    # echo -e "To: $EMAIL_TO\nFrom: $EMAIL_FROM\nSubject: $subject\n\n$body" | ssmtp "$EMAIL_TO"
    
    if [ $? -eq 0 ]; then
        echo "$TIMESTAMP E-mail enviado com sucesso" >> "$LOG"
    else
        echo "$TIMESTAMP Erro ao enviar e-mail" >> "$LOG"
    fi
}

# Loop principal
while true; do
    # Executa curl e mede o tempo de resposta
    RESULT=$(curl -s -L -w "%{http_code} %{time_total}" -o /dev/null "$URL")
    HTTP_CODE=$(echo "$RESULT" | awk '{print $1}')
    TIME_TOTAL=$(echo "$RESULT" | awk '{print $2}')
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    
    if [ "$HTTP_CODE" == "200" ]; then
        echo "$TIMESTAMP Serviço OK (HTTP $HTTP_CODE, Tempo: ${TIME_TOTAL}s)" >> "$LOG"
        
        # Verifica se o tempo de resposta excede o limite
        COMPARE=$(echo "$TIME_TOTAL > $TEMPO_LIMITE" | bc)
        if [ "$COMPARE" -eq 1 ]; then
            echo "$TIMESTAMP LENTIDÃO - Tempo de resposta: ${TIME_TOTAL}s" >> "$LOG"
            
            SUBJECT="Alerta: Lentidão detectada na URL do Protheus"
            BODY="ALERTA DE LENTIDÃO DETECTADA

URL: $URL
Tempo de resposta: ${TIME_TOTAL}s (limite: ${TEMPO_LIMITE}s)
Horário: $TIMESTAMP

Verifique a causa da demora."
            
            send_email "$SUBJECT" "$BODY"
        fi
    else
        echo "$TIMESTAMP ERRO - Código HTTP: $HTTP_CODE" >> "$LOG"
        
        SUBJECT="🚨 CRÍTICO: Indisponibilidade na URL de Produção do Protheus"
        BODY="ALERTA DE INDISPONIBILIDADE CRÍTICA

URL: $URL
Código HTTP: $HTTP_CODE
Horário: $TIMESTAMP

Verifique imediatamente!"
        
        send_email "$SUBJECT" "$BODY"
    fi
    
    sleep 60
done
