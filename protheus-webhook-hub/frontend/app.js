// Configuração da API
const API_URL = 'http://localhost:8000';

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadConfigs();
    checkAPIHealth();
    
    // Auto-refresh a cada 30 segundos
    setInterval(() => {
        loadStats();
        checkAPIHealth();
    }, 30000);
    
    // Form handler
    document.getElementById('addConfigForm').addEventListener('submit', handleAddConfig);
    
    // Update URL help text based on destination type
    document.getElementById('configDestType').addEventListener('change', updateUrlHelp);
});

// API Health Check
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        const statusEl = document.getElementById('apiStatus');
        if (data.status === 'healthy') {
            statusEl.innerHTML = '🟢 Online';
        } else {
            statusEl.innerHTML = '🟡 Parcial';
        }
    } catch (error) {
        document.getElementById('apiStatus').innerHTML = '🔴 Offline';
    }
}

// Load Statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();
        
        document.getElementById('totalConfigs').textContent = data.configs.total;
        document.getElementById('activeConfigs').textContent = data.configs.active;
        document.getElementById('totalLogs').textContent = data.logs.total;
        document.getElementById('successLogs').textContent = data.logs.success;
        document.getElementById('failedLogs').textContent = data.logs.failed;
        document.getElementById('queueSize').textContent = data.queue.size;
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

// Load Configurations
async function loadConfigs() {
    const container = document.getElementById('configsList');
    container.innerHTML = '<p class="loading">Carregando...</p>';
    
    try {
        const response = await fetch(`${API_URL}/configs`);
        const configs = await response.json();
        
        if (configs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>Nenhuma configuração encontrada</h3>
                    <p>Clique em "Nova Configuração" para começar</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = configs.map(config => `
            <div class="config-card">
                <div class="config-header">
                    <div>
                        <div class="config-name">${config.name}</div>
                        <span class="badge ${config.active ? 'badge-success' : 'badge-danger'}">
                            ${config.active ? 'Ativo' : 'Inativo'}
                        </span>
                    </div>
                    <div class="config-actions">
                        <button class="btn btn-danger" onclick="deleteConfig(${config.id})">🗑️ Excluir</button>
                    </div>
                </div>
                <div class="config-details">
                    <div class="config-detail">
                        <label>Tipo de Evento</label>
                        <span>${config.event_type}</span>
                    </div>
                    <div class="config-detail">
                        <label>Tipo de Destino</label>
                        <span class="badge badge-info">${config.destination_type}</span>
                    </div>
                    <div class="config-detail">
                        <label>URL de Destino</label>
                        <span style="word-break: break-all; font-size: 0.85rem;">${config.destination_url}</span>
                    </div>
                    <div class="config-detail">
                        <label>Criado em</label>
                        <span>${new Date(config.created_at).toLocaleString('pt-BR')}</span>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Erro ao carregar configurações:', error);
        container.innerHTML = '<p class="error">Erro ao carregar configurações</p>';
    }
}

// Load Logs
async function loadLogs() {
    const container = document.getElementById('logsList');
    const statusFilter = document.getElementById('statusFilter').value;
    
    container.innerHTML = '<p class="loading">Carregando...</p>';
    
    try {
        let url = `${API_URL}/logs?limit=50`;
        if (statusFilter) {
            url += `&status=${statusFilter}`;
        }
        
        const response = await fetch(url);
        const logs = await response.json();
        
        if (logs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>Nenhum log encontrado</h3>
                    <p>Os eventos processados aparecerão aqui</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = logs.map(log => {
            const statusClass = {
                'success': 'badge-success',
                'failed': 'badge-danger',
                'pending': 'badge-warning'
            }[log.status] || 'badge-info';
            
            const statusText = {
                'success': '✅ Sucesso',
                'failed': '❌ Falha',
                'pending': '⏳ Pendente'
            }[log.status] || log.status;
            
            return `
                <div class="log-card">
                    <div class="log-header">
                        <div>
                            <strong>${log.event_type}</strong>
                            <span class="badge ${statusClass}">${statusText}</span>
                        </div>
                        <div class="log-time">
                            ${new Date(log.created_at).toLocaleString('pt-BR')}
                        </div>
                    </div>
                    ${log.destination_url ? `<p><strong>Destino:</strong> ${log.destination_url}</p>` : ''}
                    ${log.error_message ? `<p style="color: var(--danger-color);"><strong>Erro:</strong> ${log.error_message}</p>` : ''}
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Erro ao carregar logs:', error);
        container.innerHTML = '<p class="error">Erro ao carregar logs</p>';
    }
}

// Tab Navigation
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}Tab`).classList.add('active');
    event.target.classList.add('active');
    
    // Load data if needed
    if (tabName === 'logs') {
        loadLogs();
    }
}

// Modal Functions
function showAddConfigModal() {
    document.getElementById('addConfigModal').classList.add('active');
}

function closeAddConfigModal() {
    document.getElementById('addConfigModal').classList.remove('active');
    document.getElementById('addConfigForm').reset();
}

function updateUrlHelp() {
    const destType = document.getElementById('configDestType').value;
    const helpText = document.getElementById('urlHelp');
    
    const helpTexts = {
        'slack': 'Cole aqui a URL do Incoming Webhook do Slack (https://hooks.slack.com/services/...)',
        'teams': 'Cole aqui a URL do Incoming Webhook do Microsoft Teams',
        'custom': 'Insira a URL do seu webhook customizado'
    };
    
    helpText.textContent = helpTexts[destType] || '';
}

// Handle Add Config
async function handleAddConfig(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('configName').value,
        event_type: document.getElementById('configEventType').value,
        destination_type: document.getElementById('configDestType').value,
        destination_url: document.getElementById('configDestUrl').value,
        active: document.getElementById('configActive').checked
    };
    
    try {
        const response = await fetch(`${API_URL}/configs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            closeAddConfigModal();
            loadConfigs();
            loadStats();
            alert('✅ Configuração criada com sucesso!');
        } else {
            const error = await response.json();
            alert('❌ Erro ao criar configuração: ' + JSON.stringify(error));
        }
    } catch (error) {
        console.error('Erro ao criar configuração:', error);
        alert('❌ Erro ao criar configuração: ' + error.message);
    }
}

// Delete Config
async function deleteConfig(configId) {
    if (!confirm('Tem certeza que deseja excluir esta configuração?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/configs/${configId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadConfigs();
            loadStats();
            alert('✅ Configuração excluída com sucesso!');
        } else {
            alert('❌ Erro ao excluir configuração');
        }
    } catch (error) {
        console.error('Erro ao excluir configuração:', error);
        alert('❌ Erro ao excluir configuração: ' + error.message);
    }
}

// Test Webhook
async function sendTestWebhook() {
    const eventType = document.getElementById('testEventType').value;
    const eventDataText = document.getElementById('testEventData').value;
    const resultDiv = document.getElementById('testResult');
    
    if (!eventType) {
        alert('❌ Por favor, informe o tipo de evento');
        return;
    }
    
    let eventData;
    try {
        eventData = JSON.parse(eventDataText);
    } catch (error) {
        alert('❌ JSON inválido nos dados do evento');
        return;
    }
    
    const payload = {
        event_type: eventType,
        data: eventData,
        source: 'web_test'
    };
    
    try {
        const response = await fetch(`${API_URL}/webhook`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        resultDiv.style.display = 'block';
        if (response.ok) {
            resultDiv.className = 'test-result success';
            resultDiv.innerHTML = `
                <strong>✅ Webhook enviado com sucesso!</strong><br><br>
                Status: ${result.status}<br>
                Log ID: ${result.log_id}<br>
                Mensagem: ${result.message}
            `;
            
            // Refresh stats
            setTimeout(() => {
                loadStats();
            }, 1000);
        } else {
            resultDiv.className = 'test-result error';
            resultDiv.innerHTML = `
                <strong>❌ Erro ao enviar webhook</strong><br><br>
                ${JSON.stringify(result, null, 2)}
            `;
        }
    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'test-result error';
        resultDiv.innerHTML = `
            <strong>❌ Erro na requisição</strong><br><br>
            ${error.message}
        `;
    }
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('addConfigModal');
    if (event.target === modal) {
        closeAddConfigModal();
    }
}
