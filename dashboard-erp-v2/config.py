#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard ERP Protheus 2.0 - Configurações
Autor: Fernando Vernier - https://www.linkedin.com/in/fernando-v-10758522/
"""

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv(dotenv_path='dashboard.env')

class Config:
    """Configurações da aplicação"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'seu-secret-key-super-seguro-aqui')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8050))
    
    # Banco de dados SQLite para histórico e logs
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'dashboard.db')
    
    # Limites e timeouts
    MAX_LOG_LINES = int(os.getenv('MAX_LOG_LINES', 100))
    ACTION_TIMEOUT = int(os.getenv('ACTION_TIMEOUT', 30))
    HISTORY_RETENTION_DAYS = int(os.getenv('HISTORY_RETENTION_DAYS', 90))
    
    # Auto-refresh
    DEFAULT_REFRESH_INTERVAL = int(os.getenv('DEFAULT_REFRESH_INTERVAL', 10000))
    MIN_REFRESH_INTERVAL = int(os.getenv('MIN_REFRESH_INTERVAL', 5000))
    
    # Alertas
    ENABLE_SOUND_ALERTS = os.getenv('ENABLE_SOUND_ALERTS', 'True').lower() == 'true'
    ENABLE_EMAIL_ALERTS = os.getenv('ENABLE_EMAIL_ALERTS', 'False').lower() == 'true'
    ALERT_EMAIL = os.getenv('ALERT_EMAIL', '')
    
    # Métricas avançadas
    ENABLE_PERFORMANCE_METRICS = os.getenv('ENABLE_PERFORMANCE_METRICS', 'True').lower() == 'true'
    METRICS_COLLECTION_INTERVAL = int(os.getenv('METRICS_COLLECTION_INTERVAL', 30))


class ServicesConfig:
    """Configuração dos serviços Protheus"""
    
    # Grupos de serviços organizados por função
    GRUPOS = {
        "WebApp & REST": {
            "icon": "bi-globe",
            "color": "#4f46e5",
            "servicos": [
                "appserver_broker_rest",
                "appserver_broker_webapp",
                "appserver_broker_webapp_roberto",
                "appserver_broker_webapp_bernardo",
                "appserver_broker_webapp_fernando"
            ]
        },
        "Portal & Compilação": {
            "icon": "bi-code-square",
            "color": "#06b6d4",
            "servicos": [
                "appserver_portal_01",
                "appserver_compilar",
                "appserver_exclusivo"
            ]
        },
        "Slaves (Processamento)": {
            "icon": "bi-cpu",
            "color": "#10b981",
            "servicos": [
                "appserver_slave_01",
                "appserver_slave_02",
                "appserver_slave_03",
                "appserver_slave_04",
                "appserver_slave_05",
                "appserver_slave_06",
                "appserver_slave_07",
                "appserver_slave_08",
                "appserver_slave_09",
                "appserver_slave_10"
            ]
        },
        "Workflows": {
            "icon": "bi-diagram-3",
            "color": "#f59e0b",
            "servicos": [
                "appserver_wf_01_faturamento",
                "appserver_wf_02_compras",
                "appserver_wf_03_financeiro",
                "appserver_wf_05_inncash",
                "appserver_wf_06_logfat",
                "appserver_wf_07_transmite"
            ]
        },
        "Web Services REST": {
            "icon": "bi-plugin",
            "color": "#8b5cf6",
            "servicos": [
                "appserver_wsrest_01",
                "appserver_wsrest_02",
                "appserver_wsrest_03",
                "appserver_wsrest_04"
            ]
        },
        "TSS & Integração": {
            "icon": "bi-shield-check",
            "color": "#ec4899",
            "servicos": [
                "appserver_tss"
            ]
        },
        "Monitoramento & Middleware": {
            "icon": "bi-eye",
            "color": "#14b8a6",
            "servicos": [
                "smart-view-agent",
                "monitorar_webapp",
                "kafka-middleware"
            ]
        }
    }
    
    @classmethod
    def get_all_services(cls):
        """Retorna lista com todos os serviços"""
        servicos = []
        for grupo in cls.GRUPOS.values():
            servicos.extend(grupo['servicos'])
        return servicos
    
    @classmethod
    def get_service_group(cls, service_name):
        """Retorna o grupo de um serviço específico"""
        for grupo_nome, grupo_data in cls.GRUPOS.items():
            if service_name in grupo_data['servicos']:
                return grupo_nome
        return "Outros"
    
    @classmethod
    def get_group_color(cls, service_name):
        """Retorna a cor do grupo de um serviço"""
        for grupo_data in cls.GRUPOS.values():
            if service_name in grupo_data['servicos']:
                return grupo_data['color']
        return "#6b7280"


class UsersConfig:
    """Configuração de usuários e permissões"""
    
    @staticmethod
    def get_users():
        """Retorna dicionário de usuários"""
        return {
            "squad-erp": {
                "senha": os.getenv("USER_SQUAD_ERP_PASS", "changeme"),
                "permissoes": "admin",
                "nome_completo": "Squad ERP",
                "email": os.getenv("ADMIN_EMAIL", "squad-erp@solfacil.com.br")
            },
            "viewer-erp": {
                "senha": os.getenv("USER_VIEWER_ERP_PASS", "viewerpass"),
                "permissoes": "visualizacao",
                "nome_completo": "Visualizador ERP",
                "email": os.getenv("VIEWER_EMAIL", "viewer@solfacil.com.br")
            }
        }
    
    @staticmethod
    def get_permissions():
        """Retorna definição de permissões"""
        return {
            "admin": {
                "can_start": True,
                "can_stop": True,
                "can_restart": True,
                "can_kill": True,
                "can_view_logs": True,
                "can_view_history": True,
                "can_export": True,
                "can_manage_all": True
            },
            "visualizacao": {
                "can_start": False,
                "can_stop": False,
                "can_restart": False,
                "can_kill": False,
                "can_view_logs": True,
                "can_view_history": True,
                "can_export": True,
                "can_manage_all": False
            }
        }


class ThemeConfig:
    """Configuração de temas"""
    
    THEMES = {
        "light": {
            "name": "Claro",
            "primary": "#4f46e5",
            "background": "#f8fafc",
            "card": "#ffffff",
            "text": "#1e293b",
            "border": "#e2e8f0"
        },
        "dark": {
            "name": "Escuro",
            "primary": "#6366f1",
            "background": "#0f172a",
            "card": "#1e293b",
            "text": "#f1f5f9",
            "border": "#334155"
        }
    }
