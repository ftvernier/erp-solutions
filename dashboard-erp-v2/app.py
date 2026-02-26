#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard ERP Protheus 2.0 - Aplicação Principal
Autor: Fernando Vernier - https://www.linkedin.com/in/fernando-v-10758522/
Versão: 2.0.0
"""

from flask import Flask, render_template, request, jsonify, g, send_file, Response
from datetime import datetime, timedelta
import json
import io
import csv

from config import Config, ServicesConfig
from auth import requer_autenticacao, requer_permissao, Auth
from services import ServiceManager, StatisticsCalculator
from models import HistoricoAcoes, MetricasServicos, Alertas, Database

# Inicializa aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Inicializa banco de dados
db = Database()

# Inicializa gerenciadores
service_manager = ServiceManager()
historico = HistoricoAcoes()
metricas = MetricasServicos()
alertas_manager = Alertas()
stats_calculator = StatisticsCalculator()


# ==================== FUNÇÕES AUXILIARES ====================

def obter_permissoes_usuario(username):
    """Obtém permissões do usuário baseado no username"""
    from auth import UsersConfig
    
    if not username:
        return None
    
    usuarios = UsersConfig.USUARIOS
    for usuario_config in usuarios.values():
        if usuario_config['username'] == username:
            return usuario_config['permissoes']
    
    return None


# ==================== ROTAS PRINCIPAIS ====================

@app.route('/')
@requer_autenticacao
def index():
    """Página principal do dashboard"""
    try:
        # Obtém status por grupo
        grupos = service_manager.obter_status_por_grupo()
        
        # Calcula estatísticas gerais
        todos_servicos = []
        for grupo_data in grupos.values():
            todos_servicos.extend(grupo_data['servicos'])
        
        stats_gerais = stats_calculator.calcular_estatisticas_gerais(todos_servicos)
        
        # Obtém alertas ativos
        alertas_ativos = alertas_manager.obter_ativos()
        alertas_por_severidade = alertas_manager.contar_por_severidade()
        
        # Obtém histórico recente
        historico_recente = historico.obter_recentes(limite=10)
        
        return render_template(
            'dashboard.html',
            grupos=grupos,
            stats=stats_gerais,
            alertas=alertas_ativos,
            alertas_count=alertas_por_severidade,
            historico=historico_recente,
            usuario=g.usuario,
            nome_completo=g.nome_completo,
            permissoes=g.permissoes,
            config=Config
        )
        
    except Exception as e:
        app.logger.error(f"Erro ao carregar dashboard: {e}")
        return render_template('error.html', erro=str(e), permissoes=g.permissoes), 500


@app.route('/api/status')
@requer_autenticacao
def api_status_todos():
    """API: Retorna status de todos os serviços"""
    try:
        grupos = service_manager.obter_status_por_grupo()
        
        # Calcula stats
        todos_servicos = []
        for grupo_data in grupos.values():
            todos_servicos.extend(grupo_data['servicos'])
        
        stats = stats_calculator.calcular_estatisticas_gerais(todos_servicos)
        
        return jsonify({
            'success': True,
            'grupos': grupos,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Erro na API status: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


@app.route('/api/status/<servico>')
@requer_autenticacao
def api_status_servico(servico):
    """API: Retorna status de um serviço específico"""
    try:
        if servico not in ServicesConfig.get_all_services():
            return jsonify({'success': False, 'erro': 'Serviço não encontrado'}), 404
        
        status = service_manager.obter_status(servico)
        
        return jsonify({
            'success': True,
            'servico': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao obter status de {servico}: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


@app.route('/api/acao', methods=['POST'])
@requer_autenticacao
@requer_permissao('can_manage_all')
def api_executar_acao():
    """API: Executa ação em serviço(s)"""
    try:
        data = request.get_json() or request.form.to_dict()
        
        servico = data.get('servico')
        acao = data.get('acao')
        pid = data.get('pid')
        
        if not acao:
            return jsonify({'success': False, 'erro': 'Ação não especificada'}), 400
        
        # Ações globais
        if acao == 'iniciar_todos':
            resultados = service_manager.iniciar_todos()
            
            # Registra no histórico
            historico.registrar(
                usuario=g.usuario,
                nome_completo=g.nome_completo,
                servico=None,
                acao='iniciar_todos',
                status='sucesso',
                mensagem=f"{len(resultados['sucessos'])} serviços iniciados",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify({
                'success': True,
                'mensagem': 'Ação global executada',
                'resultados': resultados
            })
        
        elif acao == 'parar_todos':
            resultados = service_manager.parar_todos()
            
            historico.registrar(
                usuario=g.usuario,
                nome_completo=g.nome_completo,
                servico=None,
                acao='parar_todos',
                status='sucesso',
                mensagem=f"{len(resultados['sucessos'])} serviços parados",
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify({
                'success': True,
                'mensagem': 'Ação global executada',
                'resultados': resultados
            })
        
        # Ações individuais
        if not servico:
            return jsonify({'success': False, 'erro': 'Serviço não especificado'}), 400
        
        if servico not in ServicesConfig.get_all_services():
            return jsonify({'success': False, 'erro': 'Serviço inválido'}), 400
        
        # Executa ação
        sucesso, mensagem = service_manager.executar_acao(servico, acao, pid)
        
        # Registra no histórico
        historico.registrar(
            usuario=g.usuario,
            nome_completo=g.nome_completo,
            servico=servico,
            acao=acao,
            status='sucesso' if sucesso else 'falha',
            mensagem=mensagem,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'success': sucesso,
            'mensagem': mensagem,
            'servico': servico,
            'acao': acao
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao executar ação: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


@app.route('/api/logs/<servico>')
@requer_autenticacao
def api_logs_servico(servico):
    """API: Retorna logs de um serviço"""
    try:
        if servico not in ServicesConfig.get_all_services():
            return jsonify({'success': False, 'erro': 'Serviço não encontrado'}), 404
        
        linhas = request.args.get('linhas', Config.MAX_LOG_LINES, type=int)
        
        logs = service_manager.obter_logs(servico, linhas)
        
        return jsonify({
            'success': True,
            'servico': servico,
            'logs': logs,
            'total_linhas': len(logs)
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao obter logs de {servico}: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


@app.route('/api/metricas/<servico>')
@requer_autenticacao
def api_metricas_servico(servico):
    """API: Retorna métricas históricas de um serviço"""
    try:
        if servico not in ServicesConfig.get_all_services():
            return jsonify({'success': False, 'erro': 'Serviço não encontrado'}), 404
        
        limite = request.args.get('limite', 100, type=int)
        
        metricas_hist = metricas.obter_ultimas(servico, limite)
        media_24h = metricas.obter_media_periodo(servico, 24)
        
        return jsonify({
            'success': True,
            'servico': servico,
            'metricas': metricas_hist,
            'media_24h': media_24h
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao obter métricas de {servico}: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


@app.route('/api/historico')


@app.route('/api/logs/<servico>/stream')
@requer_autenticacao
def api_logs_stream(servico):
    """API: Stream de logs em tempo real usando Server-Sent Events"""
    import subprocess
    import time
    
    try:
        if servico not in ServicesConfig.get_all_services():
            return jsonify({'success': False, 'erro': 'Serviço não encontrado'}), 404
        
        def generate():
            """Gerador para Server-Sent Events"""
            # Comando journalctl em modo follow
            cmd = [
                'sudo', 'journalctl',
                '-u', f'{servico}.service',
                '-f',  # Follow mode (tail -f)
                '-n', '100',  # Começa com últimas 100 linhas
                '--no-pager'
            ]
            
            process = None
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Envia linhas conforme chegam
                for line in process.stdout:
                    # Remove quebras de linha extras
                    line = line.rstrip('\n')
                    if line:
                        # Formato SSE: data: conteúdo\n\n
                        yield f"data: {line}\n\n"
                        
            except Exception as e:
                yield f"data: ERRO: {str(e)}\n\n"
            finally:
                if process:
                    process.kill()
                    process.wait()
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        app.logger.error(f"Erro no stream de logs de {servico}: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


@app.route('/api/logs/<servico>/download')
@requer_autenticacao
def api_logs_download(servico):
    """API: Download do log completo do serviço"""
    import subprocess
    
    try:
        if servico not in ServicesConfig.get_all_services():
            return jsonify({'success': False, 'erro': 'Serviço não encontrado'}), 404
        
        # Pega TODAS as linhas do log (sem limite)
        cmd = [
            'sudo', 'journalctl',
            '-u', f'{servico}.service',
            '--no-pager'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return jsonify({'success': False, 'erro': 'Erro ao obter logs'}), 500
        
        log_content = result.stdout
        
        # Nome do arquivo com timestamp
        filename = f'log_{servico}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        return Response(
            log_content,
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/plain; charset=utf-8'
            }
        )
        
    except subprocess.TimeoutExpired:
        app.logger.error(f"Timeout ao obter logs de {servico}")
        return jsonify({'success': False, 'erro': 'Timeout ao obter logs'}), 500
    except Exception as e:
        app.logger.error(f"Erro ao fazer download de logs de {servico}: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500
@requer_autenticacao
def api_historico():
    """API: Retorna histórico de ações"""
    try:
        limite = request.args.get('limite', 100, type=int)
        servico = request.args.get('servico')
        usuario = request.args.get('usuario')
        
        hist = historico.obter_recentes(limite, servico, usuario)
        
        return jsonify({
            'success': True,
            'historico': hist,
            'total': len(hist)
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao obter histórico: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


@app.route('/api/historico/estatisticas')
@requer_autenticacao
def api_historico_estatisticas():
    """API: Retorna estatísticas do histórico"""
    try:
        periodo = request.args.get('periodo', 7, type=int)
        
        stats = historico.estatisticas(periodo)
        
        return jsonify({
            'success': True,
            'estatisticas': stats
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


@app.route('/api/alertas')
@requer_autenticacao
def api_alertas():
    """API: Retorna alertas"""
    try:
        ativos_apenas = request.args.get('ativos', 'true').lower() == 'true'
        servico = request.args.get('servico')
        
        if ativos_apenas:
            alerts = alertas_manager.obter_ativos(servico)
        else:
            alerts = alertas_manager.obter_recentes(50)
        
        return jsonify({
            'success': True,
            'alertas': alerts,
            'count': len(alerts)
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao obter alertas: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


@app.route('/api/alertas/<int:alerta_id>/resolver', methods=['POST'])
@requer_autenticacao
@requer_permissao('can_manage_all')
def api_resolver_alerta(alerta_id):
    """API: Marca alerta como resolvido"""
    try:
        alertas_manager.resolver(alerta_id, g.usuario)
        
        return jsonify({
            'success': True,
            'mensagem': 'Alerta resolvido'
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao resolver alerta: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


# ==================== EXPORTAÇÃO ====================

@app.route('/export/historico')
@requer_autenticacao
@requer_permissao('can_export')
def export_historico_csv():
    """Exporta histórico em CSV"""
    try:
        periodo = request.args.get('dias', 30, type=int)
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=periodo)
        
        hist = historico.obter_por_periodo(data_inicio, data_fim)
        
        # Cria CSV em memória
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'timestamp', 'usuario', 'nome_completo', 'servico', 
            'acao', 'status', 'mensagem', 'ip_address'
        ])
        
        writer.writeheader()
        for item in hist:
            writer.writerow({
                'timestamp': item['timestamp'],
                'usuario': item['usuario'],
                'nome_completo': item.get('nome_completo', ''),
                'servico': item.get('servico', ''),
                'acao': item['acao'],
                'status': item['status'],
                'mensagem': item.get('mensagem', ''),
                'ip_address': item.get('ip_address', '')
            })
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=historico_erp_{data_inicio.strftime("%Y%m%d")}_{data_fim.strftime("%Y%m%d")}.csv'
            }
        )
        
    except Exception as e:
        app.logger.error(f"Erro ao exportar histórico: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


@app.route('/export/metricas/<servico>')
@requer_autenticacao
@requer_permissao('can_export')
def export_metricas_csv(servico):
    """Exporta métricas de um serviço em CSV"""
    try:
        if servico not in ServicesConfig.get_all_services():
            return jsonify({'success': False, 'erro': 'Serviço não encontrado'}), 404
        
        metricas_data = metricas.obter_ultimas(servico, 1000)
        
        # Cria CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'timestamp', 'servico', 'cpu_percent', 'memory_mb', 
            'memory_percent', 'threads', 'status'
        ])
        
        writer.writeheader()
        for item in metricas_data:
            writer.writerow({
                'timestamp': item['timestamp'],
                'servico': item['servico'],
                'cpu_percent': item.get('cpu_percent', 0),
                'memory_mb': item.get('memory_mb', 0),
                'memory_percent': item.get('memory_percent', 0),
                'threads': item.get('threads', 0),
                'status': item.get('status', '')
            })
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=metricas_{servico}_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
        
    except Exception as e:
        app.logger.error(f"Erro ao exportar métricas: {e}")
        return jsonify({'success': False, 'erro': str(e)}), 500


# ==================== PÁGINAS ADICIONAIS ====================

@app.route('/historico')
@requer_autenticacao
def pagina_historico():
    """Página de histórico completo"""
    try:
        hist = historico.obter_recentes(500)
        stats = historico.estatisticas(30)
        
        return render_template(
            'history.html',
            historico=hist,
            estatisticas=stats,
            usuario=g.usuario,
            permissoes=g.permissoes
        )
        
    except Exception as e:
        app.logger.error(f"Erro ao carregar página de histórico: {e}")
        return render_template('error.html', erro=str(e), permissoes=g.permissoes), 500


@app.route('/logs')
@requer_autenticacao
def pagina_logs():
    """Página de visualização de logs"""
    try:
        servicos = ServicesConfig.get_all_services()
        
        return render_template(
            'logs.html',
            servicos=servicos,
            usuario=g.usuario,
            permissoes=g.permissoes
        )
        
    except Exception as e:
        app.logger.error(f"Erro ao carregar página de logs: {e}")
        return render_template('error.html', erro=str(e), permissoes=g.permissoes), 500


# ==================== HANDLERS DE ERRO ====================

@app.errorhandler(404)
def not_found(error):
    """Handler para página não encontrada"""
    # Obtém permissões do usuário se autenticado
    auth = request.authorization
    permissoes = obter_permissoes_usuario(auth.username) if auth else None
    
    return render_template('error.html', 
                         erro='Página não encontrada',
                         permissoes=permissoes), 404


@app.errorhandler(500)
def internal_error(error):
    """Handler para erro interno"""
    app.logger.error(f"Erro interno: {error}")
    
    # Obtém permissões do usuário se autenticado
    auth = request.authorization
    permissoes = obter_permissoes_usuario(auth.username) if auth else None
    
    return render_template('error.html', 
                         erro='Erro interno do servidor',
                         permissoes=permissoes), 500


@app.errorhandler(403)
def forbidden(error):
    """Handler para acesso negado"""
    # Obtém permissões do usuário se autenticado
    auth = request.authorization
    permissoes = obter_permissoes_usuario(auth.username) if auth else None
    
    return render_template('error.html', 
                         erro='Acesso negado',
                         permissoes=permissoes), 403


# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_globals():
    """Injeta variáveis globais em todos os templates"""
    return {
        'app_name': 'Dashboard ERP Protheus 2.0',
        'app_version': '2.0.0',
        'ano_atual': datetime.now().year,
        'empresa': 'Solfácil'
    }


# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 DASHBOARD ERP PROTHEUS 2.0")
    print("=" * 70)
    print(f"📊 URL: http://{Config.HOST}:{Config.PORT}")
    print(f"🔧 Total de serviços: {len(ServicesConfig.get_all_services())}")
    print(f"👥 Grupos de serviços: {len(ServicesConfig.GRUPOS)}")
    print(f"💾 Banco de dados: {Config.DATABASE_PATH}")
    print(f"🔒 Modo debug: {'Ativo' if Config.DEBUG else 'Desativado'}")
    print("=" * 70)
    print("\n✅ Dashboard inicializado com sucesso!\n")
    
    try:
        app.run(
            debug=Config.DEBUG,
            host=Config.HOST,
            port=Config.PORT,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard finalizado pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro ao iniciar dashboard: {e}")
