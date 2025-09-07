#!/usr/bin/python3.10
from flask import Flask, render_template_string, request, redirect, url_for, Response, g, flash, jsonify
from functools import wraps
import subprocess
import os
from dotenv import load_dotenv
import time

# Carrega as variáveis do arquivo dashboard.env
load_dotenv(dotenv_path='dashboard.env')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Usuários e permissões
USUARIOS = {
    "squad-erp": {
        "senha": os.getenv("USER_SQUAD_ERP_PASS"),
        "permissoes": "admin"
    },
    "viewer-erp": {
        "senha": os.getenv("USER_VIEWER_ERP_PASS"),
        "permissoes": "visualizacao"
    }
}

# ========== Configurações ==========
SERVICOS = [
    "appserver_broker_rest", "appserver_broker_webapp",
    "appserver_portal_01", "appserver_compilar",
    "appserver_slave_01", "appserver_slave_02", "appserver_slave_03", "appserver_slave_04",
    "appserver_slave_05", "appserver_slave_06", "appserver_slave_07", "appserver_slave_08",
    "appserver_slave_09", "appserver_slave_10", "appserver_tss"
]

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard ERP Protheus</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: #4f46e5;
            --secondary-color: #6366f1;
            --success-color: #10b981;
            --danger-color: #ef4444;
            --warning-color: #f59e0b;
            --card-bg: #ffffff;
            --border-color: #e2e8f0;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: var(--text-primary);
        }

        .main-container {
            min-height: 100vh;
            padding: 2rem 0;
        }

        .dashboard-header {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
        }

        .dashboard-title {
            font-weight: 700;
            font-size: 2rem;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        .dashboard-subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
            margin-bottom: 1.5rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
            text-align: center;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }

        .stat-number {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .controls-section {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
        }

        .btn-modern {
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            position: relative;
            overflow: hidden;
        }

        .btn-modern:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }

        .btn-modern:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn-primary-modern {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
        }

        .btn-success-modern {
            background: linear-gradient(135deg, var(--success-color), #059669);
            color: white;
        }

        .btn-danger-modern {
            background: linear-gradient(135deg, var(--danger-color), #dc2626);
            color: white;
        }

        /* Estilos para o filtro de busca */
        .search-section {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
        }

        .search-input-container {
            position: relative;
            max-width: 500px;
        }

        .search-input {
            width: 100%;
            padding: 1rem 1rem 1rem 3rem;
            border: 2px solid var(--border-color);
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: #f8fafc;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--primary-color);
            background: white;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }

        .search-icon {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
            font-size: 1.1rem;
        }

        .clear-search {
            position: absolute;
            right: 1rem;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 0.5rem;
            border-radius: 50%;
            transition: all 0.3s ease;
            display: none;
        }

        .clear-search:hover {
            background: #f1f5f9;
            color: var(--danger-color);
        }

        .clear-search.show {
            display: block;
        }

        .filter-stats {
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .services-container {
            background: var(--card-bg);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
        }

        .services-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 1.5rem;
        }

        .services-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0;
        }

        .service-item {
            border-bottom: 1px solid var(--border-color);
            padding: 1.5rem;
            transition: all 0.3s ease;
            position: relative;
        }

        .service-item:last-child {
            border-bottom: none;
        }

        .service-item:hover {
            background: #f8fafc;
        }

        .service-item.hidden {
            display: none;
        }

        .service-item.loading {
            background: #f0f9ff;
            border-left: 4px solid var(--primary-color);
        }

        .service-row {
            display: grid;
            grid-template-columns: 2fr 1fr 2fr;
            gap: 1rem;
            align-items: center;
        }

        @media (max-width: 768px) {
            .service-row {
                grid-template-columns: 1fr;
                gap: 1rem;
                text-align: center;
            }
        }

        .service-name {
            font-weight: 500;
            color: var(--text-primary);
            font-size: 1rem;
        }

        .service-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            justify-content: center;
        }

        .status-badge {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 500;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s ease;
        }

        .status-active {
            background: #dcfce7;
            color: #166534;
        }

        .status-inactive {
            background: #fee2e2;
            color: #991b1b;
        }

        .status-loading {
            background: #dbeafe;
            color: #1d4ed8;
        }

        .service-actions {
            display: flex;
            gap: 0.5rem;
            justify-content: center;
            flex-wrap: wrap;
        }

        .action-btn {
            padding: 0.5rem 0.75rem;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.3s ease;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.25rem;
            font-size: 0.875rem;
            position: relative;
            overflow: hidden;
        }

        .action-btn:hover:not(:disabled) {
            transform: translateY(-1px);
        }

        .action-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .action-btn.loading {
            pointer-events: none;
        }

        .btn-start {
            background: var(--success-color);
            color: white;
        }

        .btn-stop {
            background: var(--danger-color);
            color: white;
        }

        .btn-restart {
            background: var(--warning-color);
            color: white;
        }

        .btn-kill {
            background: #6b7280;
            color: white;
        }

        .refresh-controls {
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .form-select-modern {
            border: 2px solid var(--border-color);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            background: white;
            transition: all 0.3s ease;
        }

        .form-select-modern:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
            outline: none;
        }

        .auto-refresh-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            background: #dcfce7;
            border: 1px solid var(--success-color);
            font-size: 0.875rem;
            color: var(--success-color);
            min-width: 100px;
        }

        .auto-refresh-status.paused {
            background: #fef3c7;
            border-color: var(--warning-color);
            color: var(--warning-color);
        }

        .modal-modern .modal-content {
            border: none;
            border-radius: 16px;
            box-shadow: var(--shadow-lg);
        }

        .modal-modern .modal-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border-radius: 16px 16px 0 0;
        }

        .permission-badge {
            background: #ddd6fe;
            color: #5b21b6;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }

        .viewer-badge {
            background: #fef3c7;
            color: #92400e;
        }

        .no-results {
            text-align: center;
            padding: 3rem 2rem;
            color: var(--text-secondary);
        }

        .no-results i {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }

        /* Loading Spinner */
        .loading-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Toast Notifications */
        .toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        }

        .toast-custom {
            background: white;
            border-radius: 12px;
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border-color);
            min-width: 300px;
            animation: slideIn 0.3s ease-out;
        }

        .toast-custom .toast-header {
            border-bottom: 1px solid var(--border-color);
            padding: 1rem;
        }

        .toast-custom .toast-body {
            padding: 1rem;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        /* Progress Overlay */
        .progress-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9998;
        }

        .progress-card {
            background: white;
            padding: 2rem;
            border-radius: 16px;
            text-align: center;
            box-shadow: var(--shadow-lg);
            min-width: 300px;
        }

        .progress-spinner {
            width: 50px;
            height: 50px;
            border: 4px solid var(--border-color);
            border-top: 4px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
    </style>
</head>
<body>
    <!-- Progress Overlay -->
    <div class="progress-overlay" id="progressOverlay">
        <div class="progress-card">
            <div class="progress-spinner"></div>
            <h5>Executando Ação</h5>
            <p class="text-muted mb-0" id="progressText">Aguarde enquanto processamos sua solicitação...</p>
        </div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container"></div>

    <div class="main-container">
        <div class="container">
            <div class="dashboard-header">
                <div class="d-flex justify-content-between align-items-start flex-wrap gap-3">
                    <div>
                        <h1 class="dashboard-title">
                            <i class="bi bi-server text-primary"></i>
                            Dashboard ERP Protheus
                        </h1>
                        <p class="dashboard-subtitle">Ambiente de Produção - Monitoramento em tempo real</p>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        {% if g.permissao == 'admin' %}
                        <span class="permission-badge">
                            <i class="bi bi-person-check"></i>
                            Administrador
                        </span>
                        {% else %}
                        <span class="permission-badge viewer-badge">
                            <i class="bi bi-eye"></i>
                            Somente Visualização
                        </span>
                        {% endif %}
                    </div>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number text-success">{{ stats.ativos }}</div>
                    <div class="stat-label">Serviços Ativos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number text-danger">{{ stats.parados }}</div>
                    <div class="stat-label">Serviços Parados</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number text-primary">{{ stats.total }}</div>
                    <div class="stat-label">Total de Serviços</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number text-warning">{{ stats.uptime }}%</div>
                    <div class="stat-label">Uptime</div>
                </div>
            </div>

            <!-- Seção de Filtro/Busca -->
            <div class="search-section">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
                    <div class="search-input-container">
                        <i class="bi bi-search search-icon"></i>
                        <input 
                            type="text" 
                            id="searchInput" 
                            class="search-input" 
                            placeholder="Digite para filtrar serviços..." 
                            autocomplete="off"
                        >
                        <button type="button" class="clear-search" id="clearSearch" onclick="limparBusca()">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
                    <div class="filter-stats">
                        <i class="bi bi-funnel"></i>
                        Mostrando <span id="visibleCount">{{ stats.total }}</span> de {{ stats.total }} serviços
                    </div>
                </div>
            </div>

            {% if g.permissao == 'admin' %}
            <div class="controls-section">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
                    <div class="d-flex gap-2 flex-wrap">
                        <button class="btn btn-success-modern btn-modern" onclick="executarAcaoGlobal('iniciar_todos')">
                            <i class="bi bi-play-circle-fill"></i>
                            Iniciar Todos
                        </button>
                        <button class="btn btn-danger-modern btn-modern" onclick="executarAcaoGlobal('parar_todos')">
                            <i class="bi bi-stop-circle-fill"></i>
                            Parar Todos
                        </button>
                    </div>
                    
                    <div class="refresh-controls">
                        <label for="tempoRefresh" class="form-label mb-0">Atualização:</label>
                        <select id="tempoRefresh" class="form-select-modern" onchange="alterarTempo()">
                            <option value="10000" selected>10 segundos</option>
                            <option value="20000">20 segundos</option>
                            <option value="30000">30 segundos</option>
                            <option value="60000">1 minuto</option>
                        </select>
                        
                        <button class="btn btn-warning btn-modern" id="toggleAutoRefresh" onclick="toggleAutoRefresh()">
                            <i class="bi bi-pause-circle"></i>
                            Pausar
                        </button>
                        
                        <div class="auto-refresh-status" id="autoRefreshStatus">
                            <i class="bi bi-arrow-clockwise"></i>
                            <span id="countdown">10s</span>
                        </div>
                        
                        <button class="btn btn-primary-modern btn-modern" onclick="atualizarManual()">
                            <i class="bi bi-arrow-clockwise"></i>
                            Atualizar
                        </button>
                    </div>
                </div>
            </div>
            {% else %}
            <div class="controls-section">
                <div class="alert alert-info mb-0">
                    <i class="bi bi-info-circle"></i>
                    Você está em modo somente visualização. Para executar ações nos serviços, entre com uma conta de administrador.
                </div>
            </div>
            {% endif %}

            <div class="services-container">
                <div class="services-header">
                    <h3 class="services-title">
                        <i class="bi bi-list-check"></i>
                        Status dos Serviços (<span id="servicesCount">{{ stats.total }}</span> serviços)
                    </h3>
                </div>
                
                {% for nome, status, pid in servicos %}
                <div class="service-item" data-service="{{ nome }}" data-service-name="{{ nome|lower }}" id="service-{{ nome }}">
                    <div class="service-row">
                        <div class="service-name">{{ nome }}</div>
                        <div class="service-status">
                            <span class="status-badge {{ 'status-active' if status else 'status-inactive' }}" id="status-{{ nome }}">
                                <i class="bi bi-{{ 'check-circle-fill' if status else 'x-circle-fill' }}" id="status-icon-{{ nome }}"></i>
                                <span id="status-text-{{ nome }}">{{ 'Ativo' if status else 'Parado' }}</span>
                            </span>
                        </div>
                        <div class="service-actions" id="actions-{{ nome }}">
                            {% if g.permissao == 'admin' %}
                                <button class="action-btn btn-start" onclick="executarAcao('{{ nome }}', 'start')">
                                    <i class="bi bi-play-fill"></i> Iniciar
                                </button>
                                <button class="action-btn btn-stop" onclick="executarAcao('{{ nome }}', 'stop')">
                                    <i class="bi bi-stop-fill"></i> Parar
                                </button>
                                <button class="action-btn btn-restart" onclick="executarAcao('{{ nome }}', 'restart')">
                                    <i class="bi bi-arrow-clockwise"></i> Reiniciar
                                </button>
                                {% if status and pid != "0" %}
                                <button class="action-btn btn-kill" onclick="executarAcao('{{ nome }}', 'kill', '{{ pid }}')">
                                    <i class="bi bi-exclamation-triangle-fill"></i> Kill
                                </button>
                                {% endif %}
                            {% else %}
                                <span class="text-muted">
                                    <i class="bi bi-eye-slash"></i>
                                    Somente visualização
                                </span>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}

                <!-- Mensagem quando não há resultados -->
                <div id="noResults" class="no-results" style="display: none;">
                    <i class="bi bi-search"></i>
                    <h5>Nenhum serviço encontrado</h5>
                    <p>Tente ajustar o termo de busca ou limpar o filtro.</p>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        // VARIÁVEIS GLOBAIS
        let autoRefreshAtivo = true;
        let tempoRefresh = 10000; // 10 segundos padrão
        let timerRefresh = null;
        let timerCountdown = null;
        let segundosRestantes = 10;
        let isExecutingAction = false;

        // AO CARREGAR A PÁGINA
        document.addEventListener('DOMContentLoaded', function() {
            // 1. RESTAURAR FILTRO SALVO
            const filtroSalvo = localStorage.getItem('filtroERP');
            if (filtroSalvo) {
                document.getElementById('searchInput').value = filtroSalvo;
                filtrarServicos();
            }

            // 2. INICIAR AUTO-REFRESH
            iniciarAutoRefresh();

            // 3. EVENTOS DE FILTRO
            document.getElementById('searchInput').addEventListener('input', filtrarServicos);
        });

        // ========== FEEDBACK VISUAL ==========

        function mostrarToast(tipo, titulo, mensagem) {
            const icons = {
                'success': 'bi-check-circle-fill text-success',
                'error': 'bi-x-circle-fill text-danger',
                'warning': 'bi-exclamation-triangle-fill text-warning',
                'info': 'bi-info-circle-fill text-primary'
            };

            const toastHtml = `
                <div class="toast toast-custom" role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="true" data-bs-delay="5000">
                    <div class="toast-header">
                        <i class="${icons[tipo]} me-2"></i>
                        <strong class="me-auto">${titulo}</strong>
                        <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                    </div>
                    <div class="toast-body">
                        ${mensagem}
                    </div>
                </div>
            `;

            const container = document.querySelector('.toast-container');
            container.insertAdjacentHTML('beforeend', toastHtml);
            
            const toastElement = container.lastElementChild;
            const toast = new bootstrap.Toast(toastElement);
            toast.show();

            // Remove o elemento após ocultar
            toastElement.addEventListener('hidden.bs.toast', function() {
                toastElement.remove();
            });
        }

        function mostrarProgress(texto = 'Executando ação...') {
            document.getElementById('progressText').textContent = texto;
            document.getElementById('progressOverlay').style.display = 'flex';
        }

        function ocultarProgress() {
            document.getElementById('progressOverlay').style.display = 'none';
        }

        function setStatusCarregando(serviceName) {
            const serviceItem = document.getElementById('service-' + serviceName);
            const statusBadge = document.getElementById('status-' + serviceName);
            const statusIcon = document.getElementById('status-icon-' + serviceName);
            const statusText = document.getElementById('status-text-' + serviceName);
            const actions = document.getElementById('actions-' + serviceName);

            // Marca o item como carregando
            serviceItem.classList.add('loading');
            
            // Atualiza o status para carregando
            statusBadge.className = 'status-badge status-loading';
            statusIcon.className = 'loading-spinner';
            statusText.textContent = 'Processando...';

            // Desabilita todos os botões de ação
            const buttons = actions.querySelectorAll('.action-btn');
            buttons.forEach(btn => {
                btn.disabled = true;
                btn.classList.add('loading');
            });
        }

        function removerStatusCarregando(serviceName) {
            const serviceItem = document.getElementById('service-' + serviceName);
            const actions = document.getElementById('actions-' + serviceName);

            // Remove a classe de carregamento
            serviceItem.classList.remove('loading');

            // Reabilita os botões de ação
            const buttons = actions.querySelectorAll('.action-btn');
            buttons.forEach(btn => {
                btn.disabled = false;
                btn.classList.remove('loading');
            });
        }

        // ========== AÇÕES DOS SERVIÇOS ==========

        async function executarAcao(servico, acao, pid = null) {
            if (isExecutingAction) {
                mostrarToast('warning', 'Ação em Andamento', 'Aguarde a conclusão da ação atual.');
                return;
            }

            // Confirmação para ações críticas
            if (acao === 'kill') {
                if (!confirm('Tem certeza que deseja forçar o encerramento deste serviço?')) {
                    return;
                }
            }

            isExecutingAction = true;
            
            // Pausa o auto-refresh durante a execução
            const wasAutoRefreshActive = autoRefreshAtivo;
            if (autoRefreshAtivo) {
                toggleAutoRefresh();
            }

            // Feedback visual específico do serviço
            setStatusCarregando(servico);

            // Textos das ações
            const acaoTextos = {
                'start': 'Iniciando serviço...',
                'stop': 'Parando serviço...',
                'restart': 'Reiniciando serviço...',
                'kill': 'Forçando encerramento...'
            };

            mostrarProgress(acaoTextos[acao] || 'Executando ação...');

            try {
                // Simula o envio da ação
                const formData = new FormData();
                formData.append('servico', servico);
                formData.append('acao', acao);
                if (pid) {
                    formData.append('pid', pid);
                }

                const response = await fetch('/acao', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    // Ação executada com sucesso
                    const acaoNomes = {
                        'start': 'iniciado',
                        'stop': 'parado',
                        'restart': 'reiniciado',
                        'kill': 'encerrado forçadamente'
                    };

                    mostrarToast('success', 'Ação Executada', 
                        `Serviço ${servico} foi ${acaoNomes[acao]} com sucesso.`);

                    // Aguarda um momento e então atualiza o status
                    setTimeout(() => {
                        atualizarStatusServico(servico);
                    }, 2000);

                } else {
                    throw new Error('Erro na execução da ação');
                }

            } catch (error) {
                console.error('Erro:', error);
                mostrarToast('error', 'Erro na Ação', 
                    `Falha ao executar a ação no serviço ${servico}. Tente novamente.`);
                
                // Remove o status de carregamento imediatamente em caso de erro
                removerStatusCarregando(servico);
            } finally {
                ocultarProgress();
                isExecutingAction = false;

                // Reativa o auto-refresh se estava ativo
                if (wasAutoRefreshActive && !autoRefreshAtivo) {
                    setTimeout(() => {
                        toggleAutoRefresh();
                    }, 1000);
                }
            }
        }

        async function executarAcaoGlobal(acao) {
            if (isExecutingAction) {
                mostrarToast('warning', 'Ação em Andamento', 'Aguarde a conclusão da ação atual.');
                return;
            }

            // Confirmação para ações globais
            const mensagens = {
                'iniciar_todos': 'Tem certeza que deseja iniciar todos os serviços?',
                'parar_todos': 'Tem certeza que deseja parar todos os serviços?'
            };

            if (!confirm(mensagens[acao])) {
                return;
            }

            isExecutingAction = true;

            // Pausa o auto-refresh
            const wasAutoRefreshActive = autoRefreshAtivo;
            if (autoRefreshAtivo) {
                toggleAutoRefresh();
            }

            const acaoTextos = {
                'iniciar_todos': 'Iniciando todos os serviços...',
                'parar_todos': 'Parando todos os serviços...'
            };

            mostrarProgress(acaoTextos[acao]);

            // Desabilita todos os botões globais
            const globalButtons = document.querySelectorAll('.controls-section .btn-modern');
            globalButtons.forEach(btn => {
                btn.disabled = true;
            });

            try {
                const formData = new FormData();
                formData.append('acao', acao);

                const response = await fetch('/acao', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const acaoNomes = {
                        'iniciar_todos': 'iniciados',
                        'parar_todos': 'parados'
                    };

                    mostrarToast('success', 'Ação Global Executada', 
                        `Todos os serviços foram ${acaoNomes[acao]} com sucesso.`);

                    // Aguarda um momento maior para ações globais e recarrega a página
                    setTimeout(() => {
                        location.reload();
                    }, 3000);

                } else {
                    throw new Error('Erro na execução da ação global');
                }

            } catch (error) {
                console.error('Erro:', error);
                mostrarToast('error', 'Erro na Ação Global', 
                    'Falha ao executar a ação global. Tente novamente.');
                
                // Reabilita os botões em caso de erro
                globalButtons.forEach(btn => {
                    btn.disabled = false;
                });
            } finally {
                ocultarProgress();
                isExecutingAction = false;

                // Reativa o auto-refresh se estava ativo (só se não for recarregar)
                if (wasAutoRefreshActive && !autoRefreshAtivo) {
                    setTimeout(() => {
                        toggleAutoRefresh();
                    }, 1000);
                }
            }
        }

        async function atualizarStatusServico(serviceName) {
            try {
                const response = await fetch(`/status/${serviceName}`);
                if (response.ok) {
                    const data = await response.json();
                    
                    const statusBadge = document.getElementById('status-' + serviceName);
                    const statusIcon = document.getElementById('status-icon-' + serviceName);
                    const statusText = document.getElementById('status-text-' + serviceName);

                    // Atualiza o status visual
                    if (data.ativo) {
                        statusBadge.className = 'status-badge status-active';
                        statusIcon.className = 'bi bi-check-circle-fill';
                        statusText.textContent = 'Ativo';
                    } else {
                        statusBadge.className = 'status-badge status-inactive';
                        statusIcon.className = 'bi bi-x-circle-fill';
                        statusText.textContent = 'Parado';
                    }
                }
            } catch (error) {
                console.error('Erro ao atualizar status:', error);
            } finally {
                // Remove o status de carregamento
                removerStatusCarregando(serviceName);
            }
        }

        // ========== FILTRO DE SERVIÇOS ==========

        function filtrarServicos() {
            const termo = document.getElementById('searchInput').value.toLowerCase();
            const servicos = document.querySelectorAll('.service-item');
            let visiveis = 0;

            servicos.forEach(servico => {
                const nome = servico.getAttribute('data-service-name');
                if (nome.includes(termo)) {
                    servico.classList.remove('hidden');
                    visiveis++;
                } else {
                    servico.classList.add('hidden');
                }
            });

            // Atualizar contadores
            document.getElementById('visibleCount').textContent = visiveis;
            document.getElementById('servicesCount').textContent = visiveis;

            // Mostrar/ocultar botão limpar
            const btnLimpar = document.getElementById('clearSearch');
            if (termo.length > 0) {
                btnLimpar.classList.add('show');
            } else {
                btnLimpar.classList.remove('show');
            }

            // Mostrar/ocultar mensagem de nenhum resultado
            const noResults = document.getElementById('noResults');
            if (visiveis === 0 && termo.length > 0) {
                noResults.style.display = 'block';
            } else {
                noResults.style.display = 'none';
            }

            // Salvar filtro
            localStorage.setItem('filtroERP', termo);
        }

        function limparBusca() {
            document.getElementById('searchInput').value = '';
            filtrarServicos();
        }

        // ========== AUTO-REFRESH ==========

        function iniciarAutoRefresh() {
            if (!autoRefreshAtivo || isExecutingAction) return;
            
            clearTimeout(timerRefresh);
            clearInterval(timerCountdown);
            
            segundosRestantes = tempoRefresh / 1000;
            
            // Timer principal para reload
            timerRefresh = setTimeout(function() {
                if (!isExecutingAction) {
                    localStorage.setItem('filtroERP', document.getElementById('searchInput').value);
                    location.reload();
                }
            }, tempoRefresh);
            
            // Timer do countdown
            timerCountdown = setInterval(function() {
                segundosRestantes--;
                document.getElementById('countdown').textContent = segundosRestantes + 's';
                if (segundosRestantes <= 0) {
                    clearInterval(timerCountdown);
                }
            }, 1000);
            
            // Atualizar display inicial
            document.getElementById('countdown').textContent = segundosRestantes + 's';
        }

        function pararAutoRefresh() {
            clearTimeout(timerRefresh);
            clearInterval(timerCountdown);
            
            const status = document.getElementById('autoRefreshStatus');
            status.className = 'auto-refresh-status paused';
            status.innerHTML = '<i class="bi bi-pause-circle"></i><span>Pausado</span>';
        }

        function toggleAutoRefresh() {
            const botao = document.getElementById('toggleAutoRefresh');
            
            if (autoRefreshAtivo) {
                // Pausar
                autoRefreshAtivo = false;
                botao.innerHTML = '<i class="bi bi-play-circle"></i> Ativar';
                botao.className = 'btn btn-success btn-modern';
                pararAutoRefresh();
            } else {
                // Ativar
                autoRefreshAtivo = true;
                botao.innerHTML = '<i class="bi bi-pause-circle"></i> Pausar';
                botao.className = 'btn btn-warning btn-modern';
                
                const status = document.getElementById('autoRefreshStatus');
                status.className = 'auto-refresh-status';
                
                iniciarAutoRefresh();
            }
        }

        function alterarTempo() {
            tempoRefresh = parseInt(document.getElementById('tempoRefresh').value);
            if (autoRefreshAtivo && !isExecutingAction) {
                iniciarAutoRefresh();
            }
        }

        function atualizarManual() {
            if (isExecutingAction) {
                mostrarToast('warning', 'Ação em Andamento', 'Aguarde a conclusão da ação atual antes de atualizar.');
                return;
            }
            
            localStorage.setItem('filtroERP', document.getElementById('searchInput').value);
            location.reload();
        }

        // ========== PREVENÇÃO DE MÚLTIPLAS AÇÕES ==========

        // Previne múltiplos envios de formulários
        document.addEventListener('submit', function(e) {
            if (isExecutingAction) {
                e.preventDefault();
                mostrarToast('warning', 'Ação em Andamento', 'Aguarde a conclusão da ação atual.');
                return false;
            }
        });

        // Aviso ao tentar sair da página durante execução
        window.addEventListener('beforeunload', function(e) {
            if (isExecutingAction) {
                e.preventDefault();
                e.returnValue = 'Uma ação está sendo executada. Tem certeza que deseja sair?';
                return e.returnValue;
            }
        });
    </script>
</body>
</html>
'''

# ============ Funções Flask (Backend) ==============

def autenticar():
    return Response('Autenticação necessária.\n', 401,
                    {'WWW-Authenticate': 'Basic realm="Dashboard ERP Protheus"'})

def verificar_auth(usuario, senha):
    return usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha

def requer_autenticacao(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not verificar_auth(auth.username, auth.password):
            return autenticar()
        g.usuario = auth.username
        g.permissao = USUARIOS[auth.username]["permissoes"]
        return f(*args, **kwargs)
    return decorated

def status_servico(nome):
    """Obtém o status de um serviço específico"""
    try:
        status = subprocess.run(
            ["sudo", "systemctl", "is-active", f"{nome}.service"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        ).stdout.strip()

        pid = subprocess.run(
            ["sudo", "systemctl", "show", f"{nome}.service", "--property", "MainPID"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        ).stdout.strip().split('=')[-1]

        return (status == "active", pid)
    except Exception as e:
        print(f"[ERRO] {nome}: {e}")
        return (False, "0")

def calcular_estatisticas(servicos_status):
    """Calcula estatísticas dos serviços"""
    ativos = sum(1 for _, status, _ in servicos_status if status)
    total = len(servicos_status)
    parados = total - ativos
    uptime = round((ativos / total * 100)) if total > 0 else 0
    
    return {
        'ativos': ativos,
        'parados': parados,
        'total': total,
        'uptime': uptime
    }

def iniciar_todos_servicos():
    """Inicia todos os serviços"""
    for servico in SERVICOS:
        try:
            subprocess.run(
                ["sudo", "systemctl", "start", f"{servico}.service"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
            )
            time.sleep(0.5)  # Pequena pausa entre serviços
        except Exception as e:
            print(f"[ERRO] Erro ao iniciar {servico}: {e}")

def parar_todos_servicos():
    """Para todos os serviços"""
    for servico in SERVICOS:
        try:
            subprocess.run(
                ["sudo", "systemctl", "stop", f"{servico}.service"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
            )
            time.sleep(0.5)  # Pequena pausa entre serviços
        except Exception as e:
            print(f"[ERRO] Erro ao parar {servico}: {e}")

@app.route('/', methods=['GET'])
@requer_autenticacao
def home():
    """Página principal do dashboard"""
    try:
        # Obtém status de todos os serviços
        servicos_status = [(s,) + status_servico(s) for s in SERVICOS]
        
        # Calcula estatísticas
        stats = calcular_estatisticas(servicos_status)
        
        return render_template_string(HTML_TEMPLATE, servicos=servicos_status, stats=stats)
    except Exception as e:
        print(f"[ERRO] Erro ao carregar dashboard: {e}")
        return Response("Erro interno do servidor", 500)

@app.route('/status/<servico_nome>', methods=['GET'])
@requer_autenticacao
def obter_status_servico(servico_nome):
    """API endpoint para obter status de um serviço específico"""
    try:
        if servico_nome not in SERVICOS:
            return jsonify({'erro': 'Serviço não encontrado'}), 404
        
        ativo, pid = status_servico(servico_nome)
        return jsonify({
            'servico': servico_nome,
            'ativo': ativo,
            'pid': pid
        })
    except Exception as e:
        print(f"[ERRO] Erro ao obter status do serviço {servico_nome}: {e}")
        return jsonify({'erro': 'Erro interno do servidor'}), 500

@app.route('/acao', methods=['POST'])
@requer_autenticacao
def acao():
    """Executa ações nos serviços"""
    if g.permissao != 'admin':
        return Response("Acesso não autorizado para esta ação.", 403)

    try:
        servico = request.form.get('servico')
        acao_tipo = request.form.get('acao')
        pid = request.form.get('pid')

        print(f"[INFO] Executando ação: {acao_tipo} em {servico or 'todos os serviços'}")

        if acao_tipo == 'iniciar_todos':
            iniciar_todos_servicos()
            print("[INFO] Todos os serviços foram iniciados")
            
        elif acao_tipo == 'parar_todos':
            parar_todos_servicos()
            print("[INFO] Todos os serviços foram parados")
            
        elif acao_tipo in ['start', 'stop', 'restart'] and servico:
            resultado = subprocess.run(
                ["sudo", "systemctl", acao_tipo, f"{servico}.service"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
            )
            if resultado.returncode == 0:
                print(f"[INFO] Serviço {servico} - ação {acao_tipo} executada com sucesso")
            else:
                print(f"[ERRO] Serviço {servico} - falha na ação {acao_tipo}: {resultado.stderr}")
                
        elif acao_tipo == 'kill' and pid:
            if pid and pid.isdigit() and int(pid) > 0:
                resultado = subprocess.run(
                    ["sudo", "kill", "-9", pid],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
                )
                if resultado.returncode == 0:
                    print(f"[INFO] Processo {pid} foi encerrado forçadamente")
                else:
                    print(f"[ERRO] Falha ao encerrar processo {pid}: {resultado.stderr}")

        # Pequena pausa para dar tempo do sistema processar
        time.sleep(1)

    except Exception as e:
        print(f"[ERRO] Erro ao executar ação: {e}")
        return Response("Erro interno do servidor", 500)

    return Response("OK", 200)

@app.errorhandler(404)
def not_found(error):
    """Handler para páginas não encontradas"""
    return Response("Página não encontrada", 404)

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos"""
    return Response("Erro interno do servidor", 500)

if __name__ == '__main__':
    print("="*50)
    print("🚀 Iniciando Dashboard ERP Protheus")
    print("="*50)
    print("📊 Dashboard disponível em: http://localhost:8050")
    print("👤 Usuários disponíveis:")
    for usuario, dados in USUARIOS.items():
        print(f"   - {usuario} ({dados['permissoes']})")
    print(f"🔧 Total de serviços monitorados: {len(SERVICOS)}")
    print("="*50)
    
    try:
        app.run(debug=True, host="0.0.0.0", port=8050)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard finalizado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar dashboard: {e}")
