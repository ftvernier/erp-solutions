# Configurações
$URL = "https://seuprotheus.com.br/webapp"
$LOG = "C:\Logs\monitor_webapp.log"
$TEMPO_LIMITE = 5  # tempo em segundos para efetuar o monitoramento

# Configurações de E-mail
$EmailFrom = "seu-email@empresa.com"
$EmailTo = "destinatario@empresa.com"
$SmtpServer = "smtp.office365.com"  # Altere conforme seu servidor SMTP
$SmtpPort = 587
$SmtpUser = "seu-email@empresa.com"
$SmtpPassword = "sua-senha-aqui"

# Criar diretório de log se não existir
$LogDir = Split-Path -Path $LOG -Parent
if (!(Test-Path -Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

# Função para enviar e-mail
function Send-AlertEmail {
    param (
        [string]$Subject,
        [string]$Body
    )
    
    try {
        $SecurePassword = ConvertTo-SecureString $SmtpPassword -AsPlainText -Force
        $Credential = New-Object System.Management.Automation.PSCredential ($SmtpUser, $SecurePassword)
        
        $MailMessage = @{
            From = $EmailFrom
            To = $EmailTo
            Subject = $Subject
            Body = $Body
            SmtpServer = $SmtpServer
            Port = $SmtpPort
            UseSsl = $true
            Credential = $Credential
        }
        
        Send-MailMessage @MailMessage
        Write-Host "E-mail enviado com sucesso!" -ForegroundColor Green
    }
    catch {
        Write-Host "Erro ao enviar e-mail: $_" -ForegroundColor Red
        Add-Content -Path $LOG -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ❌ ERRO AO ENVIAR E-MAIL: $_"
    }
}

# Loop principal
while ($true) {
    try {
        # Medir tempo de resposta
        $StartTime = Get-Date
        $Response = Invoke-WebRequest -Uri $URL -UseBasicParsing -TimeoutSec 30
        $EndTime = Get-Date
        
        $HttpCode = $Response.StatusCode
        $TimeTotal = ($EndTime - $StartTime).TotalSeconds
        $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        
        if ($HttpCode -eq 200) {
            $LogMessage = "$Timestamp Serviço OK (HTTP $HttpCode, Tempo: $($TimeTotal.ToString('F2'))s)"
            Add-Content -Path $LOG -Value $LogMessage
            Write-Host $LogMessage -ForegroundColor Green
            
            # Verifica se o tempo de resposta excede o limite
            if ($TimeTotal -gt $TEMPO_LIMITE) {
                $LogMessage = "$Timestamp ⚠️ LENTIDÃO - Tempo de resposta: $($TimeTotal.ToString('F2'))s"
                Add-Content -Path $LOG -Value $LogMessage
                Write-Host $LogMessage -ForegroundColor Yellow
                
                $EmailSubject = "Alerta: Lentidão detectada na URL do Protheus"
                $EmailBody = @"
ALERTA DE LENTIDÃO DETECTADA

URL: $URL
Tempo de resposta: $($TimeTotal.ToString('F2'))s (limite: ${TEMPO_LIMITE}s)
Horário: $Timestamp

Verifique a causa da demora.
"@
                Send-AlertEmail -Subject $EmailSubject -Body $EmailBody
            }
        }
        else {
            $LogMessage = "$Timestamp ❌ ERRO - Código HTTP: $HttpCode"
            Add-Content -Path $LOG -Value $LogMessage
            Write-Host $LogMessage -ForegroundColor Red
            
            $EmailSubject = "CRÍTICO: Indisponibilidade na URL de Produção do Protheus"
            $EmailBody = @"
ALERTA DE INDISPONIBILIDADE CRÍTICA

URL: $URL
Código HTTP: $HttpCode
Horário: $Timestamp

Verifique imediatamente!
"@
            Send-AlertEmail -Subject $EmailSubject -Body $EmailBody
        }
    }
    catch {
        $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $LogMessage = "$Timestamp ❌ ERRO - Falha na requisição: $_"
        Add-Content -Path $LOG -Value $LogMessage
        Write-Host $LogMessage -ForegroundColor Red
        
        $EmailSubject = "CRÍTICO: Falha ao acessar URL do Protheus"
        $EmailBody = @"
ALERTA DE FALHA CRÍTICA

URL: $URL
Erro: $_
Horário: $Timestamp

Verifique imediatamente!
"@
        Send-AlertEmail -Subject $EmailSubject -Body $EmailBody
    }
    
    # Aguardar 60 segundos antes da próxima verificação
    Start-Sleep -Seconds 60
}
