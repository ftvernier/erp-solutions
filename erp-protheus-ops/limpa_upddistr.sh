#!/bin/bash

echo "========================================================================"
echo "========================================================================"
echo "Limpando arquivos - UPDDISTR"
echo "========================================================================"
echo "========================================================================"

# Deleta arquivos de forma recursiva
find /totvs/p12prd/protheus_data -type f -name "*.cdx" -exec rm -v {} \;
find /totvs/p12prd/protheus_data -type f -name "*.int" -exec rm -v {} \;
find /totvs/p12prd/protheus_data -type f -name "*.ind" -exec rm -v {} \;
find /totvs/p12prd/protheus_data -type f -name "*.lck" -exec rm -v {} \;
find /totvs/p12prd/protheus_data -type f -name "*.idx" -exec rm -v {} \;
find /totvs/p12prd/protheus_data -type f -name "*.log" -exec rm -v {} \;
find /totvs/p12prd/protheus_data -type f -name "*.tmp" -exec rm -v {} \;
find /totvs/p12prd/protheus_data -type f -name "*.mem" -exec rm -v {} \;
find /totvs/p12prd/protheus_data -type f -name "sc??????.dtc" -exec rm -v {} \;
find /totvs/p12prd/protheus_data -type f -name "sc?????.dtc" -exec rm -v {} \;
find /totvs/p12prd/protheus_data -type f -name "sc*.log" -exec rm -v {} \;
find /totvs/p12prd/protheus_data -type f -name "*.lcx" -exec rm -v {} \;
find /totvs/p12prd/protheus_data/semaforo -type f -name "*.lcx" -exec rm -v {} \;
find /totvs/p12prd/protheus_data/system -type f -name "_schdtsk.dtc" -exec rm -v {} \;
find /totvs/p12prd/protheus_data/system -type f -name "_schdtsk.cdx" -exec rm -v {} \;
find /totvs/p12prd/protheus_data/system -type f -name "*.vrf" -exec rm -v {} \;
find /totvs/p12prd/protheus_data/system/systemload -type f -name "*.dbf" -exec rm -v {} \;
find /totvs/p12prd/protheus_data/system/systemload -type f -name "*.dtc" -exec rm -v {} \;
find /totvs/p12prd/protheus_data/system/systemload -type f -name "*.idx" -exec rm -v {} \;

# Diretórios para limpeza de logs e backups
directories=(
  /totvs/p12prd/bin/appserver_slave_{01..10}
  /totvs/p12prd/bin/appserver_wf_{01_faturamento,02_compras,03_financeiro,05_inncash,06_logfat,07_transmite}
  /totvs/p12prd/bin/appserver_wsrest_{01,02,03}
  /totvs/p12prd/bin/appserver_broker
  /totvs/p12prd/bin/appserver_broker_portal
  /totvs/p12prd/bin/appserver_broker_rest
  /totvs/p12prd/bin/appserver_broker_webapp
)


# Remove arquivos de logs e backups nos diretórios especificados
for dir in "${directories[@]}"; do
  find "$dir" -type f \( -name "*.tsk" -o -name "*.log" -o -name "*.bak" \) -exec rm -v {} \;
done

echo "Processo de limpeza concluído."
