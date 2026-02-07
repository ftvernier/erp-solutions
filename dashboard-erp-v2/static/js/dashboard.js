// Dashboard ERP Protheus 2.0 - JavaScript
// Autor: Fernando (Solfácil)

(function() {
    'use strict';
    
    // ========== CONSTANTS ==========
    const API_BASE = '/api';
    const REFRESH_INTERVAL = 30000; // 30 segundos
    
    // ========== UTILITY FUNCTIONS ==========
    
    /**
     * Faz requisição fetch com autenticação
     */
    async function apiRequest(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
            ...options
        };
        
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, defaultOptions);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.erro || 'Erro na requisição');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
    
    /**
     * Formata bytes para unidade legível
     */
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    /**
     * Formata timestamp para formato legível
     */
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('pt-BR');
    }
    
    /**
     * Debounce function
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // ========== DASHBOARD FUNCTIONS ==========
    
    /**
     * Atualiza status de um serviço específico
     */
    async function atualizarStatusServico(servico) {
        try {
            const data = await apiRequest(`/status/${servico}`);
            
            if (data.success) {
                // Atualiza UI do serviço
                const row = document.querySelector(`[data-service="${servico}"]`);
                if (row) {
                    atualizarLinhaServico(row, data.servico);
                }
            }
        } catch (error) {
            console.error(`Erro ao atualizar ${servico}:`, error);
        }
    }
    
    /**
     * Atualiza linha da tabela de serviço
     */
    function atualizarLinhaServico(row, servicoData) {
        // Atualiza status badge
        const statusCell = row.querySelector('.badge');
        if (statusCell) {
            statusCell.className = servicoData.ativo ? 
                'badge bg-success' : 'badge bg-danger';
            statusCell.innerHTML = servicoData.ativo ? 
                '<i class="bi bi-check-circle-fill me-1"></i>Ativo' : 
                '<i class="bi bi-x-circle-fill me-1"></i>Parado';
        }
        
        // Atualiza métricas
        const cells = row.querySelectorAll('td');
        if (cells.length >= 6) {
            // CPU
            cells[3].innerHTML = `<span class="badge ${
                servicoData.cpu_percent > 80 ? 'bg-danger' : 
                servicoData.cpu_percent > 50 ? 'bg-warning' : 'bg-success'
            }">${servicoData.cpu_percent}%</span>`;
            
            // Memória
            cells[4].innerHTML = `<span class="badge ${
                servicoData.memoria_percent > 80 ? 'bg-danger' : 
                servicoData.memoria_percent > 50 ? 'bg-warning' : 'bg-success'
            }">${servicoData.memoria_mb.toFixed(1)} MB</span>`;
            
            // Threads
            cells[5].textContent = servicoData.threads;
        }
    }
    
    /**
     * Carrega métricas históricas de um serviço
     */
    async function carregarMetricasServico(servico, container) {
        try {
            const data = await apiRequest(`/metricas/${servico}?limite=50`);
            
            if (data.success && data.metricas.length > 0) {
                renderizarGraficoMetricas(container, data.metricas);
            }
        } catch (error) {
            console.error(`Erro ao carregar métricas de ${servico}:`, error);
        }
    }
    
    /**
     * Renderiza gráfico de métricas usando Chart.js
     */
    function renderizarGraficoMetricas(container, metricas) {
        // Prepara dados
        const labels = metricas.map(m => formatTimestamp(m.timestamp));
        const cpuData = metricas.map(m => m.cpu_percent);
        const memData = metricas.map(m => m.memory_percent);
        
        // Cria canvas
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);
        
        // Cria gráfico
        new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'CPU %',
                        data: cpuData,
                        borderColor: 'rgb(79, 70, 229)',
                        backgroundColor: 'rgba(79, 70, 229, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Memória %',
                        data: memData,
                        borderColor: 'rgb(16, 185, 129)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Histórico de Performance'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
    
    /**
     * Exporta histórico para CSV
     */
    async function exportarHistorico(dias = 30) {
        try {
            window.location.href = `/export/historico?dias=${dias}`;
            showToast('success', 'Exportação', 'Download iniciado');
        } catch (error) {
            showToast('error', 'Erro', 'Falha ao exportar histórico');
        }
    }
    
    /**
     * Filtro de pesquisa em tempo real
     */
    function setupSearchFilter() {
        const searchInput = document.getElementById('searchServices');
        if (!searchInput) return;
        
        const debouncedSearch = debounce((termo) => {
            const rows = document.querySelectorAll('.service-row');
            let visibleCount = 0;
            
            rows.forEach(row => {
                const serviceName = row.dataset.service.toLowerCase();
                const match = serviceName.includes(termo.toLowerCase());
                
                row.style.display = match ? '' : 'none';
                if (match) visibleCount++;
            });
            
            // Atualiza contador (se existir)
            const counter = document.getElementById('visibleServicesCount');
            if (counter) {
                counter.textContent = visibleCount;
            }
        }, 300);
        
        searchInput.addEventListener('input', (e) => {
            debouncedSearch(e.target.value);
        });
    }
    
    /**
     * Configuração de tooltips Bootstrap
     */
    function setupTooltips() {
        const tooltipTriggerList = [].slice.call(
            document.querySelectorAll('[data-bs-toggle="tooltip"]')
        );
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    /**
     * Sistema de notificações sound
     */
    function playNotificationSound(type = 'info') {
        // Implementar se ENABLE_SOUND_ALERTS estiver ativo
        // const audio = new Audio(`/static/sounds/${type}.mp3`);
        // audio.play();
    }
    
    /**
     * Monitora alertas ativos
     */
    async function monitorarAlertas() {
        try {
            const data = await apiRequest('/alertas?ativos=true');
            
            if (data.success && data.alertas.length > 0) {
                // Atualiza badge de alertas
                const badge = document.getElementById('alertasBadge');
                if (badge) {
                    badge.textContent = data.alertas.length;
                    badge.style.display = 'inline-block';
                }
                
                // Mostra notificação se houver alertas críticos
                const criticos = data.alertas.filter(a => a.severidade === 'critical');
                if (criticos.length > 0) {
                    showToast('error', 'Alerta Crítico', 
                        `${criticos.length} alerta(s) crítico(s) detectado(s)`);
                    playNotificationSound('critical');
                }
            }
        } catch (error) {
            console.error('Erro ao monitorar alertas:', error);
        }
    }
    
    // ========== INITIALIZATION ==========
    
    document.addEventListener('DOMContentLoaded', function() {
        // Setup search filter
        setupSearchFilter();
        
        // Setup tooltips
        setupTooltips();
        
        // Monitora alertas periodicamente
        monitorarAlertas();
        setInterval(monitorarAlertas, 60000); // A cada 1 minuto
        
        // Log de inicialização
        console.log('Dashboard ERP Protheus 2.0 inicializado');
    });
    
    // ========== EXPOSE GLOBAL FUNCTIONS ==========
    
    window.dashboardUtils = {
        apiRequest,
        formatBytes,
        formatTimestamp,
        atualizarStatusServico,
        carregarMetricasServico,
        exportarHistorico
    };
    
})();
