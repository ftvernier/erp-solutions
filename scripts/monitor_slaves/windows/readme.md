# 🔧 Monitor de Serviços Protheus para Windows

[![PowerShell](https://img.shields.io/badge/PowerShell-5.1+-blue.svg)](https://docs.microsoft.com/en-us/powershell/)
[![Windows](https://img.shields.io/badge/Windows-Server%202016+-green.svg)](https://www.microsoft.com/windows-server)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Um script PowerShell robusto para monitoramento automático e reinício de serviços do ERP Protheus em ambiente Windows. O script detecta serviços problemáticos, executa reinicializações inteligentes e mantém logs detalhados de todas as operações.

## 📋 Índice

- [Características](#-características)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Usar](#-como-usar)
- [Sistema de Monitoramento](#-sistema-de-monitoramento)
- [Sistema de Logs](#-sistema-de-logs)
- [Janelas de Manutenção](#-janelas-de-manutenção)
- [Exemplos de Uso](#-exemplos-de-uso)
- [Agendamento Automático](#-agendamento-automático)
- [Solução de Problemas](#-solução-de-problemas)
- [Contribuição](#-contribuição)

## 🚀 Características

- **Monitoramento Automático**: Verifica continuamente o status dos serviços Protheus
- **Detecção Inteligente**: Identifica serviços travados, não responsivos ou em estado de erro
- **Reinício Seguro**: Executa parada forçada e reinicialização controlada dos serviços
- **Logs Detalhados**: Sistema duplo de logging com registros de ações e status
- **Janela de Manutenção**: Pausa automática durante períodos de manutenção programada
- **Manutenção Manual**: Suporte para pausar o monitoramento durante intervenções manuais
- **Modo Teste**: Execução sem alterações reais para validação
- **Interface Colorida**: Output visual com cores para facilitar o acompanhamento

## 📋 Pré-requisitos

- **Sistema Operacional**: Windows Server 2016+ ou Windows 10+
- **PowerShell**: Versão 5.1 ou superior
- **Privilégios**: Executar como Administrador
- **Serviços**: Serviços Protheus configurados como serviços Windows
- **Espaço em Disco**: ~50MB para logs (configurável)

## 📦 Instalação

1. **Clone o repositório ou baixe o script**:
```powershell
# Via Git
git clone https://github.com/seu-usuario/protheus-monitor.git
cd protheus-monitor

# Ou baixe diretamente o arquivo protheus_monitor.ps1
```

2. **Crie o diretório de logs**:
```powershell
New-Item -Path "C:\Logs" -ItemType Directory -Force
```

3. **Configure as permissões de execução** (se necessário):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## ⚙️ Configuração

### Configuração dos Serviços

Edite o array `$Script:SERVICES` no início do script para incluir os nomes dos seus serviços Protheus:

```powershell
$Script:SERVICES = @(
    "ProtheusAppServer01",
    "ProtheusAppServer02", 
    "ProtheusAppServer03",
    "ProtheusDBAccess",
    "ProtheusWebServer",
    # Adicione seus serviços aqui
)
```

### Configuração do Caminho dos Logs

Por padrão, os logs são salvos em `C:\Logs\protheus_monitor.log`. Para alterar:

```powershell
$Script:LOG_FILE = "D:\MeuCaminho\protheus_monitor.log"
```

## 🖥️ Como Usar

### Sintaxe Básica

```powershell
.\protheus_monitor.ps1 [opções]
```

### Opções Disponíveis

| Parâmetro | Descrição |
|-----------|-----------|
| `-Help` | Exibe ajuda e instruções de uso |
| `-Verbose` | Ativa modo verboso com logs detalhados |
| `-Test` | Modo teste - não reinicia serviços, apenas simula |
| `-Status` | Mostra apenas o status atual dos serviços |

### Exemplos de Comandos

```powershell
# Execução normal (monitoramento ativo)
.\protheus_monitor.ps1

# Modo teste (sem reinicializações)
.\protheus_monitor.ps1 -Test

# Verificar apenas status dos serviços
.\protheus_monitor.ps1 -Status

# Modo verboso (logs detalhados)
.\protheus_monitor.ps1 -Verbose
```

## 🔍 Sistema de Monitoramento

### Estados Considerados Problemáticos

O script monitora e intervém nos seguintes estados:

- **Stopped**: Serviço parado
- **StopPending**: Serviço tentando parar
- **StartPending**: Serviço tentando iniciar
- **PausePending**: Serviço tentando pausar
- **ContinuePending**: Serviço tentando continuar

### Detecção de Serviços Travados

O sistema verifica:

1. **Processos não responsivos**: Usando `$processo.Responding`
2. **CPU excessivo**: Processos com uso > 95% de CPU
3. **Estado de processo**: Verificação via WMI
4. **Tempo de resposta**: Timeout em operações de controle

### Processo de Reinicialização

Quando um problema é detectado:

1. **Parada Gentil**: Tentativa de `CloseMainWindow()`
2. **Parada Forçada**: `Stop-Service -Force`
3. **Kill de Processos**: `Stop-Process -Force` se necessário
4. **Limpeza**: Remoção de arquivos temporários
5. **Inicialização**: `Start-Service`
6. **Verificação**: Confirmação do status final

## 📊 Sistema de Logs

### Estrutura de Logs

O script utiliza um **sistema duplo de logging**:

#### 1. Log Principal
Mensagens gerais de execução e status:
```
[2025-07-30 14:30:15] 🚀 Iniciando monitoramento dos serviços Protheus
[2025-07-30 14:30:16] Verificando: ProtheusAppServer01
[2025-07-30 14:30:17] ✅ ProtheusAppServer01 está funcionando normalmente (Running)
```

#### 2. Log de Ações Detalhadas
Registro específico de cada ação executada:
```
[2025-07-30 14:30:18] [SERVIDOR01] AÇÃO: DETECTAR_PROBLEMA | SERVIÇO: ProtheusAppServer03 | STATUS: AVISO | DETALHES: Estado problemático: Stopped
[2025-07-30 14:30:21] [SERVIDOR01] AÇÃO: REINICIAR_SERVICO | SERVIÇO: ProtheusAppServer03 | STATUS: SUCESSO | DETALHES: Estado problemático: Stopped
```

### Tipos de Ações Registradas

| Ação | Descrição |
|------|-----------|
| `DETECTAR_PROBLEMA` | Problema identificado em um serviço |
| `REINICIAR_SERVICO` | Tentativa de reinicialização |
| `VERIFICAR_POS_REINICIO` | Verificação após reinício |
| `MODO_TESTE` | Ações simuladas em modo teste |
| `VERIFICAR_STATUS` | Verificações de rotina (verbose) |
| `RESUMO_MONITORAMENTO` | Sumário da execução |
| `ALERTA_SISTEMICO` | Problemas sistêmicos detectados |

### Códigos de Status

| Status | Cor | Significado |
|--------|-----|-------------|
| `SUCESSO` | 🟢 Verde | Operação executada com êxito |
| `FALHA` | 🔴 Vermelho | Operação falhou |
| `AVISO` | 🟡 Amarelo | Situação que requer atenção |
| `INFO` | ⚪ Branco | Informação geral |

### Localização dos Logs

- **Arquivo**: `C:\Logs\protheus_monitor.log`
- **Encoding**: UTF-8
- **Rotação**: Manual (recomenda-se rotação semanal/mensal)

## 🕐 Janelas de Manutenção

### Manutenção Programada

O script pausa automaticamente durante:
- **Dia**: Sábados
- **Horário**: 21:59 às 22:05
- **Comportamento**: Script termina sem executar monitoramento

### Manutenção Manual

Para pausar temporariamente o monitoramento:

```powershell
# Criar arquivo de manutenção manual
$timestamp = [int64](Get-Date -UFormat %s)
$timestamp | Out-File "$env:TEMP\protheus_manual_maintenance"

# Ou criar arquivo vazio para manutenção indefinida
New-Item "$env:TEMP\protheus_manual_maintenance" -ItemType File
```

**Características**:
- **Duração máxima**: 2 horas (remove automaticamente)
- **Arquivo vazio**: Manutenção indefinida
- **Localização**: `%TEMP%\protheus_manual_maintenance`

## 💡 Exemplos de Uso

### Cenário 1: Monitoramento de Rotina

```powershell
# Execução diária agendada
.\protheus_monitor.ps1

# Output esperado:
# ✅ Todos os serviços estão funcionando corretamente
```

### Cenário 2: Detecção de Problema

```powershell
.\protheus_monitor.ps1

# Output quando há problemas:
# ⚠️ ProtheusAppServer03 precisa ser reiniciado: Estado problemático: Stopped
# ✅ ProtheusAppServer03 reiniciado com sucesso
```

### Cenário 3: Modo Teste

```powershell
.\protheus_monitor.ps1 -Test

# Output em modo teste:
# 🧪 MODO TESTE: ProtheusAppServer02 seria reiniciado por: Serviço travado/não responsivo
```

### Cenário 4: Verificação de Status

```powershell
.\protheus_monitor.ps1 -Status

# Output:
# Status dos Serviços Protheus:
# ==============================
# ProtheusAppServer01        Status: Running         StartType: Automatic
# ProtheusAppServer02        Status: Stopped         StartType: Manual
```

## ⏰ Agendamento Automático

### Usando Task Scheduler (Recomendado)

```powershell
# Criar tarefa agendada para execução a cada 15 minutos
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Scripts\protheus_monitor.ps1"
$Trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 365) -At (Get-Date)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "ProtheusMonitor" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal
```

### Agendamento via CRON (alternativo)

Para ambientes com subsistema Linux ou ferramentas CRON:

```bash
# A cada 15 minutos
*/15 * * * * powershell.exe -File "C:\Scripts\protheus_monitor.ps1"
```

## 🔧 Solução de Problemas

### Problema: "Execution Policy"

**Erro**: `execution of scripts is disabled on this system`

**Solução**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problema: Permissões Insuficientes

**Erro**: `Access denied` ou falhas em `Start-Service`

**Solução**:
- Execute o PowerShell como Administrador
- Verifique permissões do usuário nos serviços

### Problema: Serviços Não Encontrados

**Erro**: Serviços listados como `NOT_FOUND`

**Solução**:
1. Verifique os nomes exatos dos serviços:
```powershell
Get-Service | Where-Object {$_.Name -like "*protheus*"}
```

2. Atualize o array `$Script:SERVICES` com os nomes corretos

### Problema: Logs Não Sendo Criados

**Possíveis causas**:
- Diretório `C:\Logs` não existe
- Permissões insuficientes de escrita

**Solução**:
```powershell
# Criar diretório com permissões
New-Item -Path "C:\Logs" -ItemType Directory -Force
icacls "C:\Logs" /grant "Users:(OI)(CI)F"
```

### Problema: Script Não Para Serviços Travados

**Investigação**:
```powershell
# Verificar processos manualmente
Get-Process | Where-Object {$_.ProcessName -like "*protheus*"}

# Verificar serviços
Get-Service | Where-Object {$_.Name -like "*protheus*"} | Format-Table Name, Status, StartType
```

## 📈 Monitoramento e Alertas

### Métricas Importantes

Monitore estas métricas nos logs:

1. **Taxa de Reinicializações**: > 3 serviços reiniciados = possível problema sistêmico
2. **Frequência de Problemas**: Serviços que reiniciam constantemente
3. **Tempo de Recuperação**: Tempo entre detecção e resolução
4. **Falhas de Reinicialização**: Serviços que não conseguem reiniciar

### Alertas Automáticos

O script gera alertas para:

- **ALERTA_SISTEMICO**: Quando > 3 serviços precisam reinício
- **Falhas repetidas**: Serviços que falham ao reiniciar
- **Processos não responsivos**: Detecção de travamentos

## 🔄 Rotação de Logs

### Rotação Manual

```powershell
# Script para rotação semanal
$logFile = "C:\Logs\protheus_monitor.log"
$backupFile = "C:\Logs\protheus_monitor_$(Get-Date -Format 'yyyyMMdd').log"

if (Test-Path $logFile) {
    Move-Item $logFile $backupFile
    # Opcional: compactar logs antigos
    Compress-Archive -Path $backupFile -DestinationPath "$backupFile.zip"
    Remove-Item $backupFile
}
```

### Rotação Automática

Adicione ao Task Scheduler para executar semanalmente:

```powershell
# Manter apenas últimos 30 dias de logs
Get-ChildItem "C:\Logs\protheus_monitor*.log" | 
Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | 
Remove-Item -Force
```

## 🤝 Contribuição

### Como Contribuir

1. **Fork** o repositório
2. **Crie** uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add: Nova funcionalidade'`)
4. **Push** para a branch (`git push origin feature/MinhaFeature`)
5. **Abra** um Pull Request

### Padrões de Código

- Use comentários em português para facilitar manutenção
- Mantenha funções com responsabilidade única
- Adicione logs para novas funcionalidades
- Teste em ambiente de desenvolvimento antes do PR

### Reportar Bugs

Use as [Issues do GitHub](https://github.com/seu-usuario/protheus-monitor/issues) incluindo:

- Versão do Windows e PowerShell
- Log completo do erro
- Passos para reproduzir
- Configuração dos serviços

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.


⭐ **Se este projeto foi útil, considere dar uma estrela no GitHub!**

**Desenvolvido com ❤️ para a comunidade Protheus**
