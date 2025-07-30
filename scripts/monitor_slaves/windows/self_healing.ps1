# Script para monitorar e reiniciar serviços do ERP Protheus
# Compatível com Windows Server
# Autor: Fernando Vernier
# Data: $(Get-Date -Format "yyyy-MM-dd")

#Requires -RunAsAdministrator

param(
    [switch]$Help,
    [switch]$Verbose,
    [switch]$Test,
    [switch]$Status
)

# Configurações
$Script:LOG_FILE = "C:\Logs\protheus_monitor.log"
$Script:SERVICES = @(
    "ProtheusAppServer01",
    "ProtheusAppServer02", 
    "ProtheusAppServer03",
    "ProtheusAppServer04",
    "ProtheusAppServer05",
    "ProtheusAppServer06",
    "ProtheusAppServer07",
    "ProtheusAppServer08",
    "ProtheusAppServer09",
    "ProtheusAppServer10"
)

# Estados considerados problemáticos
$Script:FAILED_STATES = @("Stopped", "StopPending", "StartPending", "PausePending", "ContinuePending")

# Variáveis globais
$Script:VERBOSE_MODE = $Verbose
$Script:TEST_MODE = $Test
$Script:STATUS_ONLY = $Status

# Função para logging detalhado de ações
function Write-ActionLog {
    param(
        [string]$ServiceName,
        [string]$Action,
        [string]$Status,
        [string]$Details = ""
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $hostname = $env:COMPUTERNAME
    
    $logEntry = "[$timestamp] [$hostname] AÇÃO: $Action | SERVIÇO: $ServiceName | STATUS: $Status"
    if (-not [string]::IsNullOrEmpty($Details)) {
        $logEntry += " | DETALHES: $Details"
    }
    
    # Exibe no console com cor baseada no status
    switch ($Status) {
        "SUCESSO" { Write-Host $logEntry -ForegroundColor Green }
        "FALHA" { Write-Host $logEntry -ForegroundColor Red }
        "AVISO" { Write-Host $logEntry -ForegroundColor Yellow }
        default { Write-Host $logEntry -ForegroundColor White }
    }
    
    # Escreve no arquivo de log
    try {
        Add-Content -Path $Script:LOG_FILE -Value $logEntry -Encoding UTF8
    }
    catch {
        Write-Warning "Erro ao escrever no log de ações: $($_.Exception.Message)"
    }
}

# Função para logging
function Write-LogMessage {
    param([string]$Message)
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    
    # Exibe no console
    Write-Host $logEntry
    
    # Escreve no arquivo de log
    try {
        Add-Content -Path $Script:LOG_FILE -Value $logEntry -Encoding UTF8
    }
    catch {
        Write-Warning "Erro ao escrever no log: $($_.Exception.Message)"
    }
}
function Test-MaintenanceWindow {
    $currentDay = (Get-Date).DayOfWeek.value__  # 0=Sunday, 1=Monday, ..., 6=Saturday
    $currentTime = Get-Date -Format "HHmm"
    
    # Sábado = 6, entre 21:59 e 22:05
    if ($currentDay -eq 6 -and [int]$currentTime -ge 2159 -and [int]$currentTime -le 2205) {
        return $true  # Está na janela de manutenção
    }
    
    return $false  # Não está na janela de manutenção
}

# Função para verificar se há manutenção manual em andamento
function Test-ManualMaintenance {
    $maintenanceFile = "$env:TEMP\protheus_manual_maintenance"
    
    if (Test-Path $maintenanceFile) {
        $maintenanceStart = Get-Content $maintenanceFile -ErrorAction SilentlyContinue
        $currentTime = [int64](Get-Date -UFormat %s)
        
        Write-LogMessage "Debug: Arquivo de manutenção manual encontrado: $maintenanceStart"
        
        # Se arquivo existe mas está vazio, considera como manutenção ativa
        if ([string]::IsNullOrEmpty($maintenanceStart)) {
            Write-LogMessage "Debug: Arquivo vazio - manutenção ativa"
            return $true
        }
        
        # Verifica se a manutenção manual não está muito antiga (máximo 2 horas)
        try {
            $timeDiff = $currentTime - [int64]$maintenanceStart
            Write-LogMessage "Debug: Tempo decorrido: $timeDiff segundos"
            
            if ($timeDiff -lt 7200) {  # 7200 segundos = 2 horas
                Write-LogMessage "Debug: Manutenção manual válida - pausando monitor"
                return $true  # Manutenção manual ativa
            }
            else {
                # Remove arquivo antigo automaticamente
                Remove-Item $maintenanceFile -Force -ErrorAction SilentlyContinue
                Write-LogMessage "Arquivo de manutenção manual expirado removido automaticamente"
            }
        }
        catch {
            Write-LogMessage "Erro ao processar timestamp do arquivo de manutenção: $($_.Exception.Message)"
        }
    }
    else {
        Write-LogMessage "Debug: Arquivo de manutenção manual não encontrado"
    }
    
    return $false  # Não há manutenção manual
}

# Função para logging
function Write-LogMessage {
    param([string]$Message)
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    
    # Exibe no console
    Write-Host $logEntry
    
    # Escreve no arquivo de log
    try {
        Add-Content -Path $Script:LOG_FILE -Value $logEntry -Encoding UTF8
    }
    catch {
        Write-Warning "Erro ao escrever no log: $($_.Exception.Message)"
    }
}

# Função para configurar logging
function Initialize-Logging {
    $logDir = Split-Path $Script:LOG_FILE -Parent
    
    if (-not (Test-Path $logDir)) {
        try {
            New-Item -Path $logDir -ItemType Directory -Force | Out-Null
        }
        catch {
            Write-Error "Erro ao criar diretório de log: $($_.Exception.Message)"
            exit 1
        }
    }
    
    # Cria arquivo de log se não existir
    if (-not (Test-Path $Script:LOG_FILE)) {
        try {
            New-Item -Path $Script:LOG_FILE -ItemType File -Force | Out-Null
        }
        catch {
            Write-Error "Erro ao criar arquivo de log: $($_.Exception.Message)"
            exit 1
        }
    }
}

# Função para verificar o status de um serviço
function Get-ServiceStatus {
    param([string]$ServiceName)
    
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            return @{
                Status = $service.Status.ToString()
                StartType = $service.StartType.ToString()
                Exists = $true
            }
        }
        else {
            return @{
                Status = "NotFound"
                StartType = "Unknown"
                Exists = $false
            }
        }
    }
    catch {
        return @{
            Status = "Error"
            StartType = "Unknown"
            Exists = $false
            Error = $_.Exception.Message
        }
    }
}

# Função para verificar se o serviço está travado
function Test-ServiceHanging {
    param([string]$ServiceName)
    
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if (-not $service) {
            return $false
        }
        
        # Obtém processos relacionados ao serviço
        $processes = Get-WmiObject -Class Win32_Service | Where-Object { $_.Name -eq $ServiceName } | ForEach-Object {
            if ($_.ProcessId -and $_.ProcessId -ne 0) {
                Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
            }
        }
        
        foreach ($proc in $processes) {
            if ($proc) {
                $cpuUsage = (Get-Counter "\Process($($proc.ProcessName))\% Processor Time" -ErrorAction SilentlyContinue).CounterSamples.CookedValue
                
                Write-LogMessage "🔧 Debug $ServiceName - PID: $($proc.Id), CPU: $([math]::Round($cpuUsage, 2))%, Respondendo: $($proc.Responding)"
                
                # Verifica condições de travamento
                if ($proc.Responding -eq $false) {
                    Write-LogMessage "$ServiceName detectado como não responsivo"
                    return $true
                }
                
                # CPU muito alta (>95%)
                if ($cpuUsage -gt 95) {
                    Write-LogMessage "$ServiceName com CPU muito alta: $([math]::Round($cpuUsage, 2))%"
                    return $true
                }
            }
        }
        
        return $false
    }
    catch {
        Write-LogMessage "Erro ao verificar se serviço está travado: $($_.Exception.Message)"
        return $false
    }
}

# Função para obter PIDs relacionados a um serviço
function Get-ServiceProcesses {
    param([string]$ServiceName)
    
    $processes = @()
    
    try {
        $service = Get-WmiObject -Class Win32_Service | Where-Object { $_.Name -eq $ServiceName }
        if ($service -and $service.ProcessId -and $service.ProcessId -ne 0) {
            $mainProcess = Get-Process -Id $service.ProcessId -ErrorAction SilentlyContinue
            if ($mainProcess) {
                $processes += $mainProcess
            }
        }
        
        # Procura por processos relacionados pelo nome
        $relatedProcesses = Get-Process | Where-Object { $_.ProcessName -like "*$ServiceName*" -or $_.ProcessName -like "*protheus*" }
        $processes += $relatedProcesses
        
        return ($processes | Sort-Object Id -Unique)
    }
    catch {
        Write-LogMessage "Erro ao obter processos do serviço: $($_.Exception.Message)"
        return @()
    }
}

# Função para kill forçado de processos
function Stop-ServiceProcesses {
    param([string]$ServiceName)
    
    Write-LogMessage "Executando stop forçado para processos do $ServiceName"
    
    $processes = Get-ServiceProcesses -ServiceName $ServiceName
    $killedCount = 0
    
    if ($processes.Count -eq 0) {
        Write-LogMessage "Nenhum processo encontrado para $ServiceName"
        return 0
    }
    
    # Tenta encerramento gentil primeiro
    Write-LogMessage "Tentando encerramento gentil para PIDs: $($processes.Id -join ', ')"
    foreach ($proc in $processes) {
        try {
            $proc.CloseMainWindow() | Out-Null
            Start-Sleep -Seconds 2
            if (-not $proc.HasExited) {
                $proc.Close()
            }
            $killedCount++
            Write-LogMessage "Processo PID $($proc.Id) encerrado gentilmente"
        }
        catch {
            Write-LogMessage "Erro ao encerrar processo PID $($proc.Id): $($_.Exception.Message)"
        }
    }
    
    # Aguarda um pouco
    Start-Sleep -Seconds 5
    
    # Verifica processos remanescentes e usa kill forçado
    $remainingProcesses = Get-ServiceProcesses -ServiceName $ServiceName
    if ($remainingProcesses.Count -gt 0) {
        Write-LogMessage "🔪 Executando kill forçado para processos persistentes: $($remainingProcesses.Id -join ', ')"
        foreach ($proc in $remainingProcesses) {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                $killedCount++
                Write-LogMessage "KILL forçado executado para PID $($proc.Id)"
            }
            catch {
                Write-LogMessage "Erro no kill forçado para PID $($proc.Id): $($_.Exception.Message)"
            }
        }
        Start-Sleep -Seconds 2
    }
    
    Write-LogMessage "Stop forçado concluído. $killedCount processos encerrados"
    return $killedCount
}

# Função para reiniciar um serviço
function Restart-ProtheusService {
    param(
        [string]$ServiceName,
        [string]$RestartReason = ""
    )
    
    Write-LogMessage "Reiniciando serviço: $ServiceName"
    
    $serviceInfo = Get-ServiceStatus -ServiceName $ServiceName
    $forceKillNeeded = $false
    
    # Condições que indicam necessidade de kill forçado
    if ($serviceInfo.Status -in @("Stopped", "StopPending", "StartPending") -or
        $RestartReason -like "*travado*" -or 
        $RestartReason -like "*não responsivo*") {
        $forceKillNeeded = $true
        Write-LogMessage "Serviço em estado crítico - kill forçado será necessário"
    }
    
    # Se kill forçado é necessário, executa antes
    if ($forceKillNeeded) {
        Stop-ServiceProcesses -ServiceName $ServiceName
    }
    
    try {
        # Para o serviço
        Write-LogMessage "Parando serviço $ServiceName..."
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        
        # Verifica se ainda há processos rodando
        $remainingProcesses = Get-ServiceProcesses -ServiceName $ServiceName
        if ($remainingProcesses.Count -gt 0) {
            Write-LogMessage "Processos remanescentes detectados após Stop-Service"
            Stop-ServiceProcesses -ServiceName $ServiceName
        }
        
        # Aguarda limpeza completa
        Start-Sleep -Seconds 2
        
        # Limpa possíveis arquivos temporários
        $tempFiles = Get-ChildItem -Path $env:TEMP -Filter "*$ServiceName*" -ErrorAction SilentlyContinue
        foreach ($file in $tempFiles) {
            try {
                Remove-Item $file.FullName -Force -ErrorAction SilentlyContinue
            }
            catch {
                # Ignora erros de limpeza
            }
        }
        
        # Inicia o serviço
        Write-LogMessage "Iniciando serviço $ServiceName..."
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 3
        
        # Verifica se realmente está rodando
        $newServiceInfo = Get-ServiceStatus -ServiceName $ServiceName
        
        if ($newServiceInfo.Status -eq "Running") {
            Write-LogMessage "Serviço $ServiceName reiniciado com sucesso"
            
            # Envia notificação para o Slack
            if (-not $Script:TEST_MODE) {
                Send-SlackNotification -ServiceName $ServiceName -Status "success" -Reason $RestartReason
            }
            
            return $true
        }
        else {
            Write-LogMessage "Serviço $ServiceName não ficou ativo após reinício: $($newServiceInfo.Status)"
            
            if (-not $Script:TEST_MODE) {
                Send-SlackNotification -ServiceName $ServiceName -Status "failed" -Reason "Serviço não ficou ativo após reinício: $($newServiceInfo.Status)"
            }
            
            return $false
        }
    }
    catch {
        Write-LogMessage "Falha ao reiniciar o serviço $ServiceName - Erro: $($_.Exception.Message)"
        Write-ActionLog -ServiceName $ServiceName -Action "REINICIAR_SERVICO" -Status "FALHA" -Details "Erro: $($_.Exception.Message)"
        return $false
    }
}

# Função para verificar conectividade de rede
function Test-NetworkConnectivity {
    try {
        $result = Test-NetConnection -ComputerName "8.8.8.8" -Port 53 -WarningAction SilentlyContinue
        if (-not $result.TcpTestSucceeded) {
            Write-LogMessage "Possível problema de conectividade de rede detectado"
            return $false
        }
        return $true
    }
    catch {
        Write-LogMessage "Erro ao verificar conectividade: $($_.Exception.Message)"
        return $false
    }
}

# Função principal de monitoramento
function Start-ServiceMonitoring {
    $restartCount = 0
    $totalServices = $Script:SERVICES.Count
    
    Write-LogMessage "Iniciando verificação de $totalServices serviços do Protheus"
    
    foreach ($serviceName in $Script:SERVICES) {
        Write-LogMessage "Verificando: $serviceName"
        
        $serviceInfo = Get-ServiceStatus -ServiceName $serviceName
        
        if (-not $serviceInfo.Exists) {
            Write-LogMessage "Serviço $serviceName não encontrado no sistema"
            continue
        }
        
        $needsRestart = $false
        $reason = ""
        
        # Verifica se está em estado problemático
        if ($serviceInfo.Status -in $Script:FAILED_STATES) {
            $needsRestart = $true
            $reason = "Estado problemático: $($serviceInfo.Status)"
        }
        
        # Verifica se está travado (mesmo que rodando)
        if (-not $needsRestart -and $serviceInfo.Status -eq "Running") {
            if (Test-ServiceHanging -ServiceName $serviceName) {
                $needsRestart = $true
                $reason = "Serviço travado/não responsivo"
            }
        }
        
        # Reinicia se necessário
        if ($needsRestart) {
            Write-LogMessage "🔧 $serviceName precisa ser reiniciado: $reason"
            Write-ActionLog -ServiceName $serviceName -Action "DETECTAR_PROBLEMA" -Status "AVISO" -Details $reason
            
            if (-not $Script:TEST_MODE) {
                if (Restart-ProtheusService -ServiceName $serviceName -RestartReason $reason) {
                    $restartCount++
                    Start-Sleep -Seconds 5
                    
                    # Verifica se realmente ficou ativo
                    $newServiceInfo = Get-ServiceStatus -ServiceName $serviceName
                    if ($newServiceInfo.Status -eq "Running") {
                        Write-LogMessage "$serviceName está funcionando corretamente após reinício"
                        Write-ActionLog -ServiceName $serviceName -Action "VERIFICAR_POS_REINICIO" -Status "SUCESSO" -Details "Serviço funcionando normalmente"
                    }
                    else {
                        Write-LogMessage "$serviceName ainda apresenta problemas após reinício: $($newServiceInfo.Status)"
                        Write-ActionLog -ServiceName $serviceName -Action "VERIFICAR_POS_REINICIO" -Status "AVISO" -Details "Status: $($newServiceInfo.Status)"
                    }
                }
            }
            else {
                Write-LogMessage "MODO TESTE: $serviceName seria reiniciado por: $reason"
                Write-ActionLog -ServiceName $serviceName -Action "MODO_TESTE" -Status "INFO" -Details "Seria reiniciado por: $reason"
                $restartCount++
            }
        }
        else {
            Write-LogMessage "$serviceName está funcionando normalmente ($($serviceInfo.Status))"
            if ($Script:VERBOSE_MODE) {
                Write-ActionLog -ServiceName $serviceName -Action "VERIFICAR_STATUS" -Status "OK" -Details "Status: $($serviceInfo.Status)"
            }
        }
    }
    
    if ($restartCount -gt 0) {
        Write-LogMessage "📊 Resumo: $restartCount de $totalServices serviços foram $(if($Script:TEST_MODE){'marcados para reinício'}else{'reiniciados'})"
        Write-ActionLog -ServiceName "SISTEMA" -Action "RESUMO_MONITORAMENTO" -Status "INFO" -Details "$restartCount de $totalServices serviços processados"
        
        # Se muitos serviços foram reiniciados, pode indicar problema sistêmico
        if ($restartCount -gt 3) {
            Write-LogMessage "ATENÇÃO: Muitos serviços foram reiniciados. Verifique logs do sistema e recursos"
            Write-ActionLog -ServiceName "SISTEMA" -Action "ALERTA_SISTEMICO" -Status "AVISO" -Details "Muitos serviços reiniciados ($restartCount) - possível problema sistêmico"
        }
    }
    else {
        Write-LogMessage "Todos os serviços estão funcionando corretamente"
        Write-ActionLog -ServiceName "SISTEMA" -Action "MONITORAMENTO_COMPLETO" -Status "SUCESSO" -Details "Todos os $totalServices serviços funcionando normalmente"
    }
}

# Função para mostrar uso do script
function Show-Usage {
    Write-Host @"
Uso: .\protheus_monitor.ps1 [opções]

Opções:
  -Help           Mostra esta ajuda
  -Verbose        Modo verboso (mais detalhes no log)
  -Test           Modo teste (não reinicia serviços, apenas verifica)
  -Status         Mostra apenas o status atual dos serviços

Exemplos:
  .\protheus_monitor.ps1                    # Executa verificação normal
  .\protheus_monitor.ps1 -Test             # Executa em modo teste
  .\protheus_monitor.ps1 -Status           # Mostra apenas status
  .\protheus_monitor.ps1 -Verbose          # Modo detalhado

Logs:
  - Log principal: C:\Logs\protheus_monitor.log
  - Ações detalhadas são registradas com timestamp e status

Requisitos:
  - Execute como Administrador
  - PowerShell 5.1 ou superior
"@
}

# Função para mostrar apenas status
function Show-ServiceStatus {
    Write-Host "Status dos Serviços Protheus:"
    Write-Host "=============================="
    
    foreach ($serviceName in $Script:SERVICES) {
        $serviceInfo = Get-ServiceStatus -ServiceName $serviceName
        
        if ($serviceInfo.Exists) {
            Write-Host ("{0,-30} Status: {1,-15} StartType: {2}" -f $serviceName, $serviceInfo.Status, $serviceInfo.StartType)
        }
        else {
            Write-Host ("{0,-30} Status: {1,-15}" -f $serviceName, "NOT_FOUND")
        }
    }
}

# Função principal
function Main {
    # Verifica se deve mostrar ajuda
    if ($Help) {
        Show-Usage
        exit 0
    }
    
    # Verifica se deve mostrar apenas status
    if ($Script:STATUS_ONLY) {
        Show-ServiceStatus
        exit 0
    }
    
    # Verifica se há manutenção manual em andamento
    if (Test-ManualMaintenance) {
        Write-LogMessage "Manutenção manual em andamento - Script pausado"
        exit 0
    }
    
    # Verifica se está na janela de manutenção programada
    if (Test-MaintenanceWindow) {
        $currentTime = Get-Date -Format "HH:mm"
        Write-LogMessage "Janela de manutenção programada ativa (Sábado $currentTime) - Script pausado"
        exit 0
    }
    
    # Configura logging
    Initialize-Logging
    
    # Log do início da execução
    Write-LogMessage "=========================================="
    Write-LogMessage "Iniciando monitoramento dos serviços Protheus"
    
    if ($Script:TEST_MODE) {
        Write-LogMessage "MODO TESTE: Serviços não serão reiniciados"
    }
    
    # Verifica conectividade
    Test-NetworkConnectivity | Out-Null
    
    # Executa monitoramento
    Start-ServiceMonitoring
    
    Write-LogMessage "Monitoramento concluído"
    Write-LogMessage "=========================================="
}

# Verifica se está sendo executado como administrador
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Este script deve ser executado como Administrador!"
    Write-Host "Clique com o botão direito no PowerShell e selecione 'Executar como administrador'"
    exit 1
}

# Executa o script
Main
