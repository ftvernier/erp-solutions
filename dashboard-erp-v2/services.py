#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard ERP Protheus 2.0 - Gerenciamento de Serviços
Autor: Fernando Vernier - https://www.linkedin.com/in/fernando-v-10758522/
"""

import subprocess
import time
import re
from typing import Dict, List, Tuple, Optional
from config import ServicesConfig, Config
from models import MetricasServicos, Alertas


class ServiceManager:
    """Gerenciador de serviços systemd com métricas avançadas"""
    
    def __init__(self):
        self.metricas = MetricasServicos() if Config.ENABLE_PERFORMANCE_METRICS else None
        self.alertas = Alertas()
    
    def obter_status(self, servico: str) -> Dict:
        """
        Obtém status completo de um serviço
        
        Returns:
            dict com: ativo, pid, uptime, memoria, cpu, threads, estado
        """
        try:
            # Status básico
            status_cmd = subprocess.run(
                ["sudo", "systemctl", "is-active", f"{servico}.service"],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                universal_newlines=True,
                timeout=5
            )
            ativo = status_cmd.stdout.strip() == "active"
            
            # Propriedades do serviço
            props = self._obter_propriedades(servico)
            
            resultado = {
                'servico': servico,
                'ativo': ativo,
                'pid': props.get('MainPID', '0'),
                'estado': props.get('ActiveState', 'unknown'),
                'sub_estado': props.get('SubState', 'unknown'),
                'uptime': self._calcular_uptime(props.get('ActiveEnterTimestamp')),
                'memoria_mb': 0,
                'memoria_percent': 0,
                'cpu_percent': 0,
                'threads': 0,
                'grupo': ServicesConfig.get_service_group(servico),
                'cor': ServicesConfig.get_group_color(servico)
            }
            
            # Se o serviço está ativo, coleta métricas de performance
            if ativo and resultado['pid'] != '0' and Config.ENABLE_PERFORMANCE_METRICS:
                metricas_perf = self._obter_metricas_processo(resultado['pid'])
                resultado.update(metricas_perf)
                
                # Registra métricas no banco
                if self.metricas:
                    self.metricas.registrar(
                        servico=servico,
                        cpu_percent=resultado['cpu_percent'],
                        memory_mb=resultado['memoria_mb'],
                        memory_percent=resultado['memoria_percent'],
                        threads=resultado['threads'],
                        status='active' if ativo else 'inactive',
                        uptime_seconds=resultado.get('uptime_seconds', 0)
                    )
            
            return resultado
            
        except subprocess.TimeoutExpired:
            return self._resultado_erro(servico, "Timeout ao verificar status")
        except Exception as e:
            return self._resultado_erro(servico, str(e))
    
    def _obter_propriedades(self, servico: str) -> Dict:
        """Obtém propriedades do systemd para um serviço"""
        props = {}
        try:
            cmd = subprocess.run(
                ["sudo", "systemctl", "show", f"{servico}.service"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=5
            )
            
            for linha in cmd.stdout.split('\n'):
                if '=' in linha:
                    chave, valor = linha.split('=', 1)
                    props[chave] = valor
                    
        except Exception as e:
            print(f"[ERRO] Falha ao obter propriedades de {servico}: {e}")
        
        return props
    
    def _calcular_uptime(self, timestamp_str: Optional[str]) -> str:
        """Calcula uptime a partir do timestamp de ativação"""
        if not timestamp_str or timestamp_str == '0':
            return "0s"
        
        try:
            # Parse do timestamp do systemd
            # Exemplo: "Fri 2024-02-07 10:30:45 -03"
            import datetime
            
            # Remove o timezone para simplificar
            ts = timestamp_str.rsplit(' ', 1)[0] if ' ' in timestamp_str else timestamp_str
            
            # Tenta diferentes formatos
            formatos = [
                "%a %Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%a %b %d %H:%M:%S %Y"
            ]
            
            dt_ativacao = None
            for fmt in formatos:
                try:
                    dt_ativacao = datetime.datetime.strptime(ts, fmt)
                    break
                except ValueError:
                    continue
            
            if not dt_ativacao:
                return "N/A"
            
            agora = datetime.datetime.now()
            diff = agora - dt_ativacao
            
            dias = diff.days
            horas, resto = divmod(diff.seconds, 3600)
            minutos, segundos = divmod(resto, 60)
            
            partes = []
            if dias > 0:
                partes.append(f"{dias}d")
            if horas > 0:
                partes.append(f"{horas}h")
            if minutos > 0 or (dias == 0 and horas == 0):
                partes.append(f"{minutos}m")
            
            return " ".join(partes) if partes else "0m"
            
        except Exception as e:
            print(f"[ERRO] Falha ao calcular uptime: {e}")
            return "N/A"
    
    def _obter_metricas_processo(self, pid: str) -> Dict:
        """Obtém métricas de CPU, memória e threads de um processo"""
        metricas = {
            'memoria_mb': 0,
            'memoria_percent': 0,
            'cpu_percent': 0,
            'threads': 0
        }
        
        try:
            # Usa ps para obter métricas do processo
            cmd = subprocess.run(
                ["ps", "-p", pid, "-o", "%cpu,%mem,rss,nlwp", "--no-headers"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=3
            )
            
            if cmd.returncode == 0 and cmd.stdout.strip():
                partes = cmd.stdout.strip().split()
                if len(partes) >= 4:
                    metricas['cpu_percent'] = float(partes[0])
                    metricas['memoria_percent'] = float(partes[1])
                    metricas['memoria_mb'] = float(partes[2]) / 1024  # Converte KB para MB
                    metricas['threads'] = int(partes[3])
                    
        except Exception as e:
            print(f"[ERRO] Falha ao obter métricas do processo {pid}: {e}")
        
        return metricas
    
    def _resultado_erro(self, servico: str, erro: str) -> Dict:
        """Retorna dicionário de resultado em caso de erro"""
        return {
            'servico': servico,
            'ativo': False,
            'pid': '0',
            'estado': 'error',
            'sub_estado': 'error',
            'uptime': '0s',
            'memoria_mb': 0,
            'memoria_percent': 0,
            'cpu_percent': 0,
            'threads': 0,
            'erro': erro,
            'grupo': ServicesConfig.get_service_group(servico),
            'cor': ServicesConfig.get_group_color(servico)
        }
    
    def obter_status_todos(self) -> List[Dict]:
        """Obtém status de todos os serviços configurados"""
        servicos = ServicesConfig.get_all_services()
        return [self.obter_status(servico) for servico in servicos]
    
    def obter_status_por_grupo(self) -> Dict:
        """Organiza status dos serviços por grupo"""
        grupos = {}
        
        for grupo_nome, grupo_data in ServicesConfig.GRUPOS.items():
            servicos_status = []
            for servico in grupo_data['servicos']:
                status = self.obter_status(servico)
                servicos_status.append(status)
            
            # Calcula estatísticas do grupo
            total = len(servicos_status)
            ativos = sum(1 for s in servicos_status if s['ativo'])
            
            grupos[grupo_nome] = {
                'icon': grupo_data['icon'],
                'color': grupo_data['color'],
                'servicos': servicos_status,
                'total': total,
                'ativos': ativos,
                'parados': total - ativos,
                'percentual_ativo': round((ativos / total * 100) if total > 0 else 0, 1)
            }
        
        return grupos
    
    def executar_acao(self, servico: str, acao: str, pid: Optional[str] = None) -> Tuple[bool, str]:
        """
        Executa uma ação em um serviço
        
        Args:
            servico: Nome do serviço
            acao: start, stop, restart, kill
            pid: PID para ação kill
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            if acao == 'kill' and pid:
                return self._kill_processo(pid)
            
            if acao not in ['start', 'stop', 'restart']:
                return False, f"Ação inválida: {acao}"
            
            # Executa comando systemctl
            cmd = subprocess.run(
                ["sudo", "systemctl", acao, f"{servico}.service"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=Config.ACTION_TIMEOUT
            )
            
            if cmd.returncode == 0:
                # Aguarda um momento para o serviço estabilizar
                time.sleep(2)
                
                # Verifica se a ação foi bem sucedida
                status = self.obter_status(servico)
                
                if acao == 'start' and status['ativo']:
                    return True, f"Serviço {servico} iniciado com sucesso"
                elif acao == 'stop' and not status['ativo']:
                    return True, f"Serviço {servico} parado com sucesso"
                elif acao == 'restart':
                    if status['ativo']:
                        return True, f"Serviço {servico} reiniciado com sucesso"
                    else:
                        return False, f"Serviço {servico} falhou ao reiniciar"
                
                return True, f"Ação {acao} executada em {servico}"
            else:
                erro = cmd.stderr.strip() or "Erro desconhecido"
                return False, f"Falha ao executar {acao} em {servico}: {erro}"
                
        except subprocess.TimeoutExpired:
            return False, f"Timeout ao executar {acao} em {servico}"
        except Exception as e:
            return False, f"Erro ao executar {acao} em {servico}: {str(e)}"
    
    def _kill_processo(self, pid: str) -> Tuple[bool, str]:
        """Força o encerramento de um processo"""
        try:
            if not pid or not pid.isdigit() or int(pid) <= 0:
                return False, "PID inválido"
            
            cmd = subprocess.run(
                ["sudo", "kill", "-9", pid],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=5
            )
            
            if cmd.returncode == 0:
                return True, f"Processo {pid} encerrado forçadamente"
            else:
                erro = cmd.stderr.strip() or "Processo não encontrado"
                return False, f"Falha ao encerrar processo {pid}: {erro}"
                
        except Exception as e:
            return False, f"Erro ao encerrar processo {pid}: {str(e)}"
    
    def iniciar_todos(self) -> Dict:
        """Inicia todos os serviços"""
        resultados = {'sucessos': [], 'falhas': []}
        
        for servico in ServicesConfig.get_all_services():
            sucesso, mensagem = self.executar_acao(servico, 'start')
            
            if sucesso:
                resultados['sucessos'].append({'servico': servico, 'mensagem': mensagem})
            else:
                resultados['falhas'].append({'servico': servico, 'mensagem': mensagem})
            
            time.sleep(0.5)  # Pausa entre serviços
        
        return resultados
    
    def parar_todos(self) -> Dict:
        """Para todos os serviços"""
        resultados = {'sucessos': [], 'falhas': []}
        
        for servico in ServicesConfig.get_all_services():
            sucesso, mensagem = self.executar_acao(servico, 'stop')
            
            if sucesso:
                resultados['sucessos'].append({'servico': servico, 'mensagem': mensagem})
            else:
                resultados['falhas'].append({'servico': servico, 'mensagem': mensagem})
            
            time.sleep(0.5)
        
        return resultados
    
    def obter_logs(self, servico: str, linhas: int = None) -> List[str]:
        """Obtém logs de um serviço"""
        linhas = linhas or Config.MAX_LOG_LINES
        
        try:
            cmd = subprocess.run(
                ["sudo", "journalctl", "-u", f"{servico}.service", "-n", str(linhas), "--no-pager"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=10
            )
            
            if cmd.returncode == 0:
                return cmd.stdout.split('\n')
            else:
                return [f"Erro ao obter logs: {cmd.stderr}"]
                
        except subprocess.TimeoutExpired:
            return ["Timeout ao obter logs"]
        except Exception as e:
            return [f"Erro ao obter logs: {str(e)}"]
    
    def verificar_saude_servico(self, servico: str) -> Dict:
        """Verifica a saúde de um serviço e cria alertas se necessário"""
        status = self.obter_status(servico)
        alertas_criados = []
        
        if not status['ativo']:
            alerta_id = self.alertas.criar(
                servico=servico,
                tipo_alerta='servico_parado',
                mensagem=f"Serviço {servico} está parado",
                severidade='critical'
            )
            alertas_criados.append(alerta_id)
        
        # Verifica uso de memória
        if status['memoria_percent'] > 80:
            alerta_id = self.alertas.criar(
                servico=servico,
                tipo_alerta='memoria_alta',
                mensagem=f"Serviço {servico} usando {status['memoria_percent']:.1f}% de memória",
                severidade='warning'
            )
            alertas_criados.append(alerta_id)
        
        # Verifica uso de CPU
        if status['cpu_percent'] > 90:
            alerta_id = self.alertas.criar(
                servico=servico,
                tipo_alerta='cpu_alta',
                mensagem=f"Serviço {servico} usando {status['cpu_percent']:.1f}% de CPU",
                severidade='warning'
            )
            alertas_criados.append(alerta_id)
        
        return {
            'servico': servico,
            'saudavel': status['ativo'] and status['memoria_percent'] < 80 and status['cpu_percent'] < 90,
            'alertas_criados': alertas_criados,
            'status': status
        }


class StatisticsCalculator:
    """Calculador de estatísticas do dashboard"""
    
    @staticmethod
    def calcular_estatisticas_gerais(servicos_status: List[Dict]) -> Dict:
        """Calcula estatísticas gerais dos serviços"""
        total = len(servicos_status)
        ativos = sum(1 for s in servicos_status if s['ativo'])
        parados = total - ativos
        
        memoria_total = sum(s.get('memoria_mb', 0) for s in servicos_status)
        cpu_media = sum(s.get('cpu_percent', 0) for s in servicos_status) / total if total > 0 else 0
        
        return {
            'total': total,
            'ativos': ativos,
            'parados': parados,
            'uptime_percentual': round((ativos / total * 100) if total > 0 else 0, 1),
            'memoria_total_mb': round(memoria_total, 2),
            'cpu_media': round(cpu_media, 2)
        }
    
    @staticmethod
    def calcular_estatisticas_por_grupo(grupos: Dict) -> Dict:
        """Calcula estatísticas agregadas por grupo"""
        stats = {}
        
        for grupo_nome, grupo_data in grupos.items():
            servicos = grupo_data['servicos']
            
            stats[grupo_nome] = {
                'total': len(servicos),
                'ativos': sum(1 for s in servicos if s['ativo']),
                'memoria_total': sum(s.get('memoria_mb', 0) for s in servicos),
                'cpu_media': sum(s.get('cpu_percent', 0) for s in servicos) / len(servicos) if servicos else 0
            }
        
        return stats
