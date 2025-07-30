# Script para monitorar e reiniciar servicos do ERP Protheus
# Compativel com Windows Server e Windows 10/11
# Autor: Fernando Vernier

#Requires -RunAsAdministrator

param(
    [switch]$Help,
    [switch]$Verbose,
    [switch]$Test,
    [switch]$Status
)

# Configuracoes
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

# Estados considerados problematicos
$Script:FAILED_STATES = @("Stopped", "StopPending", "StartPending", "PausePending", "ContinuePending")

# Variaveis globais
$Script:VERBOSE_MODE = $Verbose
$Script:TEST_MODE = $Test
$Script:STATUS_ONLY = $Status

# Funcao para logging detalhado de acoes
function Write-ActionLog {
    param(
        [string]$ServiceName,
        [string]$Action,
        [string]$Status,
        [string]$Details = ""
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $hostname = $env:COMPUTERNAME
    
    $logEntry = "[$timestamp] [$hostname] ACAO: $Action | SERVICO: $ServiceName | STATUS: $Status"
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
        Write-Warning "Erro ao escrever no log de acoes: $($_.Exception.Message)"
    }
}

# Funcao para verificar se esta na janela de manutencao
function Test-MaintenanceWindow {
    $currentDay = (Get-Date).DayOfWeek.value__
    $currentTime = Get-Date -Format "HHmm"
    
    # Sabado = 6, entre 21:59 e 22:05
    if ($currentDay -eq 6 -and [int]$currentTime -ge 2159 -and [int]$currentTime -le 2205) {
        return $true
    }
    
    return $false
}

# Funcao para verificar se ha manutencao manual em andamento
function Test-ManualMaintenance {
    $maintenanceFile = "$env:TEMP\protheus_manual_maintenance"
    
    if (Test-Path $maintenanceFile) {
        try {
            $maintenanceStart = Get-Content $maintenanceFile -ErrorAction SilentlyContinue
            $currentTime = [int64](Get-Date -UFormat %s)
            
            Write-LogMessage "Debug: Arquivo de manutencao manual encontrado: $maintenanceStart"
            
            # Se arquivo existe mas esta vazio, considera como manutencao ativa
            if ([string]::IsNullOrEmpty($maintenanceStart)) {
                Write-LogMessage "Debug: Arquivo vazio - manutencao ativa"
                return $true
            }
            
            # Verifica se a manutencao manual nao esta muito antiga (maximo 2 horas)
            $timeDiff = $currentTime - [int64]$maintenanceStart
            Write-LogMessage "Debug: Tempo decorrido: $timeDiff segundos"
            
            if ($timeDiff -lt 7200) {
                Write-LogMessage "Debug: Manutencao manual valida - pausando monitor"
                return $true
            }
            else {
                # Remove arquivo antigo automaticamente
                Remove-Item $maintenanceFile -Force -ErrorAction SilentlyContinue
                Write-LogMessage "Arquivo de manutencao manual expirado removido automaticamente"
            }
        }
        catch {
            Write-LogMessage "Erro ao processar timestamp do arquivo de manutencao: $($_.Exception.Message)"
        }
    }
    else {
        Write-LogMessage "Debug: Arquivo de manutencao manual nao encontrado"
    }
    
    return $false
}

# Funcao para logging
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

# Funcao para configurar logging
function Initialize-Logging {
    $logDir = Split-Path $Script:LOG_FILE -Parent
    
    if (-not (Test-Path $logDir)) {
        try {
            New-Item -Path $logDir -ItemType Directory -Force | Out-Null
        }
        catch {
            Write-Error "Erro ao criar diretorio de log: $($_.Exception.Message)"
            exit 1
        }
    }
    
    # Cria arquivo de log se nao existir
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

# Funcao para verificar o status de um servico
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

# Funcao para verificar se o servico esta travado
function Test-ServiceHanging {
    param([string]$ServiceName)
    
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if (-not $service) {
            return $false
        }
        
        # Obtem processos relacionados ao servico
        $serviceWmi = Get-WmiObject -Class Win32_Service | Where-Object { $_.Name -eq $ServiceName }
        
        if ($serviceWmi -and $serviceWmi.ProcessId -and $serviceWmi.ProcessId -ne 0) {
            try {
                $process = Get-Process -Id $serviceWmi.ProcessId -ErrorAction SilentlyContinue
                
                if ($process) {
                    Write-LogMessage "Debug $ServiceName - PID: $($process.Id), Respondendo: $($process.Responding)"
                    
                    # Verifica condicoes de travamento
                    if ($process.Responding -eq $false) {
                        Write-LogMessage "AVISO: $ServiceName detectado como nao responsivo"
                        return $true
                    }
                }
            }
            catch {
                Write-LogMessage "Erro ao verificar processo: $($_.Exception.Message)"
            }
        }
        
        return $false
    }
    catch {
        Write-LogMessage "Erro ao verificar se servico esta travado: $($_.Exception.Message)"
        return $false
    }
}

# Funcao para obter processos relacionados a um servico
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
        Write-LogMessage "Erro ao obter processos do servico: $($_.Exception.Message)"
        return @()
    }
}

# Funcao para kill forcado de processos
function Stop-ServiceProcesses {
    param([string]$ServiceName)
    
    Write-LogMessage "Executando stop forcado para processos do $ServiceName"
    
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
    
    # Verifica processos remanescentes e usa kill forcado
    $remainingProcesses = Get-ServiceProcesses -ServiceName $ServiceName
    if ($remainingProcesses.Count -gt 0) {
        Write-LogMessage "Executando kill forcado para processos persistentes: $($remainingProcesses.Id -join ', ')"
        foreach ($proc in $remainingProcesses) {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                $killedCount++
                Write-LogMessage "KILL forcado executado para PID $($proc.Id)"
            }
            catch {
                Write-LogMessage "Erro no kill forcado para PID $($proc.Id): $($_.Exception.Message)"
            }
        }
        Start-Sleep -Seconds 2
    }
    
    Write-LogMessage "Stop forcado concluido. $killedCount processos encerrados"
    return $killedCount
}

# Funcao para reiniciar um servico
function Restart-ProtheusService {
    param(
        [string]$ServiceName,
        [string]$RestartReason = ""
    )
    
    Write-LogMessage "Reiniciando servico: $ServiceName"
    
    $serviceInfo = Get-ServiceStatus -ServiceName $ServiceName
    $forceKillNeeded = $false
    
    # Condicoes que indicam necessidade de kill forcado
    if ($serviceInfo.Status -in @("Stopped", "StopPending", "StartPending") -or
        $RestartReason -like "*travado*" -or 
        $RestartReason -like "*nao responsivo*") {
        $forceKillNeeded = $true
        Write-LogMessage "Servico em estado critico - kill forcado sera necessario"
    }
    
    # Se kill forcado e necessario, executa antes
    if ($forceKillNeeded) {
        Stop-ServiceProcesses -ServiceName $ServiceName
    }
    
    try {
        # Para o servico
        Write-LogMessage "Parando servico $ServiceName..."
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        
        # Verifica se ainda ha processos rodando
        $remainingProcesses = Get-ServiceProcesses -ServiceName $ServiceName
        if ($remainingProcesses.Count -gt 0) {
            Write-LogMessage "Processos remanescentes detectados apos Stop-Service"
            Stop-ServiceProcesses -ServiceName $ServiceName
        }
        
        # Aguarda limpeza completa
        Start-Sleep -Seconds 2
        
        # Limpa possiveis arquivos temporarios
        try {
            $tempFiles = Get-ChildItem -Path $env:TEMP -Filter "*$ServiceName*" -ErrorAction SilentlyContinue
            foreach ($file in $tempFiles) {
                Remove-Item $file.FullName -Force -ErrorAction SilentlyContinue
            }
        }
        catch {
            # Ignora erros de limpeza
        }
        
        # Inicia o servico
        Write-LogMessage "Iniciando servico $ServiceName..."
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 3
        
        # Verifica se realmente esta rodando
        $newServiceInfo = Get-ServiceStatus -ServiceName $ServiceName
        
        if ($newServiceInfo.Status -eq "Running") {
            Write-LogMessage "Servico $ServiceName reiniciado com sucesso"
            Write-ActionLog -ServiceName $ServiceName -Action "REINICIAR_SERVICO" -Status "SUCESSO" -Details $RestartReason
            return $true
        }
        else {
            Write-LogMessage "Servico $ServiceName nao ficou ativo apos reinicio: $($newServiceInfo.Status)"
            Write-ActionLog -ServiceName $ServiceName -Action "REINICIAR_SERVICO" -Status "FALHA" -Details "Servico nao ficou ativo apos reinicio: $($newServiceInfo.Status)"
            return $false
        }
    }
    catch {
        Write-LogMessage "Falha ao reiniciar o servico $ServiceName - Erro: $($_.Exception.Message)"
        Write-ActionLog -ServiceName $ServiceName -Action "REINICIAR_SERVICO" -Status "FALHA" -Details "Erro: $($_.Exception.Message)"
        return $false
    }
}

# Funcao para verificar conectividade de rede
function Test-NetworkConnectivity {
    try {
        $result = Test-NetConnection -ComputerName "8.8.8.8" -Port 53 -WarningAction SilentlyContinue
        if (-not $result.TcpTestSucceeded) {
            Write-LogMessage "Possivel problema de conectividade de rede detectado"
            return $false
        }
        return $true
    }
    catch {
        Write-LogMessage "Erro ao verificar conectividade: $($_.Exception.Message)"
        return $false
    }
}

# Funcao principal de monitoramento
function Start-ServiceMonitoring {
    $restartCount = 0
    $totalServices = $Script:SERVICES.Count
    
    Write-LogMessage "Iniciando verificacao de $totalServices servicos do Protheus"
    
    foreach ($serviceName in $Script:SERVICES) {
        Write-LogMessage "Verificando: $serviceName"
        
        $serviceInfo = Get-ServiceStatus -ServiceName $serviceName
        
        if (-not $serviceInfo.Exists) {
            Write-LogMessage "Servico $serviceName nao encontrado no sistema"
            continue
        }
        
        $needsRestart = $false
        $reason = ""
        
        # Verifica se esta em estado problematico
        if ($serviceInfo.Status -in $Script:FAILED_STATES) {
            $needsRestart = $true
            $reason = "Estado problematico: $($serviceInfo.Status)"
        }
        
        # Verifica se esta travado (mesmo que rodando)
        if (-not $needsRestart -and $serviceInfo.Status -eq "Running") {
            if (Test-ServiceHanging -ServiceName $serviceName) {
                $needsRestart = $true
                $reason = "Servico travado/nao responsivo"
            }
        }
        
        # Reinicia se necessario
        if ($needsRestart) {
            Write-LogMessage "$serviceName precisa ser reiniciado: $reason"
            Write-ActionLog -ServiceName $serviceName -Action "DETECTAR_PROBLEMA" -Status "AVISO" -Details $reason
            
            if (-not $Script:TEST_MODE) {
                if (Restart-ProtheusService -ServiceName $serviceName -RestartReason $reason) {
                    $restartCount++
                    Start-Sleep -Seconds 5
                    
                    # Verifica se realmente ficou ativo
                    $newServiceInfo = Get-ServiceStatus -ServiceName $serviceName
                    if ($newServiceInfo.Status -eq "Running") {
                        Write-LogMessage "$serviceName esta funcionando corretamente apos reinicio"
                        Write-ActionLog -ServiceName $serviceName -Action "VERIFICAR_POS_REINICIO" -Status "SUCESSO" -Details "Servico funcionando normalmente"
                    }
                    else {
                        Write-LogMessage "$serviceName ainda apresenta problemas apos reinicio: $($newServiceInfo.Status)"
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
            Write-LogMessage "$serviceName esta funcionando normalmente ($($serviceInfo.Status))"
            if ($Script:VERBOSE_MODE) {
                Write-ActionLog -ServiceName $serviceName -Action "VERIFICAR_STATUS" -Status "OK" -Details "Status: $($serviceInfo.Status)"
            }
        }
    }
    
    if ($restartCount -gt 0) {
        Write-LogMessage "Resumo: $restartCount de $totalServices servicos foram $(if($Script:TEST_MODE){'marcados para reinicio'}else{'reiniciados'})"
        Write-ActionLog -ServiceName "SISTEMA" -Action "RESUMO_MONITORAMENTO" -Status "INFO" -Details "$restartCount de $totalServices servicos processados"
        
        # Se muitos servicos foram reiniciados, pode indicar problema sistemico
        if ($restartCount -gt 3) {
            Write-LogMessage "ATENCAO: Muitos servicos foram reiniciados. Verifique logs do sistema e recursos"
            Write-ActionLog -ServiceName "SISTEMA" -Action "ALERTA_SISTEMICO" -Status "AVISO" -Details "Muitos servicos reiniciados ($restartCount) - possivel problema sistemico"
        }
    }
    else {
        Write-LogMessage "Todos os servicos estao funcionando corretamente"
        Write-ActionLog -ServiceName "SISTEMA" -Action "MONITORAMENTO_COMPLETO" -Status "SUCESSO" -Details "Todos os $totalServices servicos funcionando normalmente"
    }
}

# Funcao para mostrar uso do script
function Show-Usage {
    Write-Host "Uso: .\protheus_monitor.ps1 [opcoes]"
    Write-Host ""
    Write-Host "Opcoes:"
    Write-Host "  -Help           Mostra esta ajuda"
    Write-Host "  -Verbose        Modo verboso (mais detalhes no log)"
    Write-Host "  -Test           Modo teste (nao reinicia servicos, apenas verifica)"
    Write-Host "  -Status         Mostra apenas o status atual dos servicos"
    Write-Host ""
    Write-Host "Exemplos:"
    Write-Host "  .\protheus_monitor.ps1                    # Executa verificacao normal"
    Write-Host "  .\protheus_monitor.ps1 -Test             # Executa em modo teste"
    Write-Host "  .\protheus_monitor.ps1 -Status           # Mostra apenas status"
    Write-Host "  .\protheus_monitor.ps1 -Verbose          # Modo detalhado"
    Write-Host ""
    Write-Host "Logs:"
    Write-Host "  Log principal: C:\Logs\protheus_monitor.log"
    Write-Host "  Acoes detalhadas sao registradas com timestamp e status"
    Write-Host ""
    Write-Host "Requisitos:"
    Write-Host "  Execute como Administrador"
    Write-Host "  PowerShell 5.1 ou superior"
}

# Funcao para mostrar apenas status
function Show-ServiceStatus {
    Write-Host "Status dos Servicos Protheus:"
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

# Funcao principal
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
    
    # Verifica se ha manutencao manual em andamento
    if (Test-ManualMaintenance) {
        Write-LogMessage "Manutencao manual em andamento - Script pausado"
        exit 0
    }
    
    # Verifica se esta na janela de manutencao programada
    if (Test-MaintenanceWindow) {
        $currentTime = Get-Date -Format "HH:mm"
        Write-LogMessage "Janela de manutencao programada ativa (Sabado $currentTime) - Script pausado"
        exit 0
    }
    
    # Configura logging
    Initialize-Logging
    
    # Log do inicio da execucao
    Write-LogMessage "=========================================="
    Write-LogMessage "Iniciando monitoramento dos servicos Protheus"
    
    if ($Script:TEST_MODE) {
        Write-LogMessage "MODO TESTE: Servicos nao serao reiniciados"
    }
    
    # Verifica conectividade
    Test-NetworkConnectivity | Out-Null
    
    # Executa monitoramento
    Start-ServiceMonitoring
    
    Write-LogMessage "Monitoramento concluido"
    Write-LogMessage "=========================================="
}

# Verifica se esta sendo executado como administrador
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Este script deve ser executado como Administrador!"
    Write-Host "Clique com o botao direito no PowerShell e selecione 'Executar como administrador'"
    exit 1
}

# Executa o script
Main
