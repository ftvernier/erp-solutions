#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard ERP Protheus 2.0 - Modelos de Dados
Autor: Fernando Vernier - https://www.linkedin.com/in/fernando-v-10758522/
"""

import sqlite3
from datetime import datetime, timedelta
from config import Config
import json


class Database:
    """Classe para gerenciamento do banco de dados SQLite"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_database()
    
    def get_connection(self):
        """Cria conexão com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Inicializa o banco de dados e cria tabelas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de histórico de ações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_acoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                usuario TEXT NOT NULL,
                nome_completo TEXT,
                servico TEXT,
                acao TEXT NOT NULL,
                status TEXT DEFAULT 'sucesso',
                mensagem TEXT,
                ip_address TEXT,
                user_agent TEXT
            )
        ''')
        
        # Tabela de métricas de performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metricas_servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                servico TEXT NOT NULL,
                cpu_percent REAL,
                memory_mb REAL,
                memory_percent REAL,
                threads INTEGER,
                status TEXT,
                uptime_seconds INTEGER
            )
        ''')
        
        # Tabela de alertas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                servico TEXT NOT NULL,
                tipo_alerta TEXT NOT NULL,
                severidade TEXT DEFAULT 'warning',
                mensagem TEXT,
                resolvido BOOLEAN DEFAULT 0,
                resolvido_em DATETIME,
                resolvido_por TEXT
            )
        ''')
        
        # Índices para melhor performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_historico_timestamp 
            ON historico_acoes(timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_historico_servico 
            ON historico_acoes(servico, timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metricas_timestamp 
            ON metricas_servicos(timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_alertas_resolvido 
            ON alertas(resolvido, timestamp DESC)
        ''')
        
        conn.commit()
        conn.close()


class HistoricoAcoes:
    """Modelo para histórico de ações"""
    
    def __init__(self):
        self.db = Database()
    
    def registrar(self, usuario, servico, acao, status='sucesso', mensagem=None, 
                  nome_completo=None, ip_address=None, user_agent=None):
        """Registra uma ação no histórico"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO historico_acoes 
            (usuario, nome_completo, servico, acao, status, mensagem, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (usuario, nome_completo, servico, acao, status, mensagem, ip_address, user_agent))
        
        conn.commit()
        conn.close()
    
    def obter_recentes(self, limite=100, servico=None, usuario=None):
        """Obtém ações recentes"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM historico_acoes WHERE 1=1'
        params = []
        
        if servico:
            query += ' AND servico = ?'
            params.append(servico)
        
        if usuario:
            query += ' AND usuario = ?'
            params.append(usuario)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limite)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def obter_por_periodo(self, data_inicio, data_fim, servico=None):
        """Obtém ações em um período específico"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM historico_acoes 
            WHERE timestamp BETWEEN ? AND ?
        '''
        params = [data_inicio, data_fim]
        
        if servico:
            query += ' AND servico = ?'
            params.append(servico)
        
        query += ' ORDER BY timestamp DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def limpar_antigos(self, dias=None):
        """Remove registros antigos"""
        dias = dias or Config.HISTORY_RETENTION_DAYS
        data_limite = datetime.now() - timedelta(days=dias)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM historico_acoes 
            WHERE timestamp < ?
        ''', (data_limite,))
        
        removidos = cursor.rowcount
        conn.commit()
        conn.close()
        
        return removidos
    
    def estatisticas(self, periodo_dias=7):
        """Retorna estatísticas do histórico"""
        data_inicio = datetime.now() - timedelta(days=periodo_dias)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Total de ações
        cursor.execute('''
            SELECT COUNT(*) as total 
            FROM historico_acoes 
            WHERE timestamp >= ?
        ''', (data_inicio,))
        total_acoes = cursor.fetchone()['total']
        
        # Ações por tipo
        cursor.execute('''
            SELECT acao, COUNT(*) as count 
            FROM historico_acoes 
            WHERE timestamp >= ?
            GROUP BY acao
            ORDER BY count DESC
        ''', (data_inicio,))
        acoes_por_tipo = [dict(row) for row in cursor.fetchall()]
        
        # Usuários mais ativos
        cursor.execute('''
            SELECT usuario, nome_completo, COUNT(*) as count 
            FROM historico_acoes 
            WHERE timestamp >= ?
            GROUP BY usuario
            ORDER BY count DESC
            LIMIT 5
        ''', (data_inicio,))
        usuarios_ativos = [dict(row) for row in cursor.fetchall()]
        
        # Serviços mais manipulados
        cursor.execute('''
            SELECT servico, COUNT(*) as count 
            FROM historico_acoes 
            WHERE timestamp >= ? AND servico IS NOT NULL
            GROUP BY servico
            ORDER BY count DESC
            LIMIT 10
        ''', (data_inicio,))
        servicos_manipulados = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_acoes': total_acoes,
            'acoes_por_tipo': acoes_por_tipo,
            'usuarios_ativos': usuarios_ativos,
            'servicos_manipulados': servicos_manipulados,
            'periodo_dias': periodo_dias
        }


class MetricasServicos:
    """Modelo para métricas de performance dos serviços"""
    
    def __init__(self):
        self.db = Database()
    
    def registrar(self, servico, cpu_percent=None, memory_mb=None, 
                  memory_percent=None, threads=None, status=None, uptime_seconds=None):
        """Registra métricas de um serviço"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO metricas_servicos 
            (servico, cpu_percent, memory_mb, memory_percent, threads, status, uptime_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (servico, cpu_percent, memory_mb, memory_percent, threads, status, uptime_seconds))
        
        conn.commit()
        conn.close()
    
    def obter_ultimas(self, servico, limite=100):
        """Obtém últimas métricas de um serviço"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM metricas_servicos 
            WHERE servico = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (servico, limite))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def obter_media_periodo(self, servico, horas=24):
        """Obtém média das métricas em um período"""
        data_inicio = datetime.now() - timedelta(hours=horas)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                AVG(cpu_percent) as cpu_avg,
                AVG(memory_mb) as memory_avg,
                AVG(memory_percent) as memory_percent_avg,
                MAX(cpu_percent) as cpu_max,
                MAX(memory_mb) as memory_max,
                MIN(cpu_percent) as cpu_min,
                MIN(memory_mb) as memory_min
            FROM metricas_servicos
            WHERE servico = ? AND timestamp >= ?
        ''', (servico, data_inicio))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def limpar_antigas(self, dias=30):
        """Remove métricas antigas"""
        data_limite = datetime.now() - timedelta(days=dias)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM metricas_servicos 
            WHERE timestamp < ?
        ''', (data_limite,))
        
        removidos = cursor.rowcount
        conn.commit()
        conn.close()
        
        return removidos


class Alertas:
    """Modelo para alertas do sistema"""
    
    def __init__(self):
        self.db = Database()
    
    def criar(self, servico, tipo_alerta, mensagem, severidade='warning'):
        """Cria um novo alerta"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alertas 
            (servico, tipo_alerta, severidade, mensagem)
            VALUES (?, ?, ?, ?)
        ''', (servico, tipo_alerta, severidade, mensagem))
        
        alerta_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return alerta_id
    
    def resolver(self, alerta_id, resolvido_por):
        """Marca um alerta como resolvido"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE alertas 
            SET resolvido = 1, resolvido_em = CURRENT_TIMESTAMP, resolvido_por = ?
            WHERE id = ?
        ''', (resolvido_por, alerta_id))
        
        conn.commit()
        conn.close()
    
    def obter_ativos(self, servico=None):
        """Obtém alertas não resolvidos"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM alertas WHERE resolvido = 0'
        params = []
        
        if servico:
            query += ' AND servico = ?'
            params.append(servico)
        
        query += ' ORDER BY timestamp DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def obter_recentes(self, limite=50):
        """Obtém alertas recentes"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM alertas 
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limite,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def contar_por_severidade(self):
        """Conta alertas ativos por severidade"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT severidade, COUNT(*) as count 
            FROM alertas 
            WHERE resolvido = 0
            GROUP BY severidade
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return {row['severidade']: row['count'] for row in rows}
