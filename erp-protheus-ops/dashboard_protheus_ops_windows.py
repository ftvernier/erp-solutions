#!/usr/bin/env python3
from flask import Flask, render_template_string, request, redirect, url_for, Response, g, flash
from functools import wraps
import subprocess
import os
import psutil
import win32service
import win32serviceutil
import win32con
from dotenv import load_dotenv

# Carrega as variáveis do arquivo dashboard.env
load_dotenv(dotenv_path='dashboard.env')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


# ========== Autenticação ==========
USUARIOS = {
    "squad-erp": {
        "senha": os.getenv("ADMIN_PASSWORD"),
        "permissoes": "admin"
    },
    "viewer-erp": {
        "senha": os.getenv("VIEWER_PASSWORD"),
        "permissoes": "visualizacao"
    }
}

def autenticar():
    return Response('Autenticação necessária.\n', 401, {'WWW-Authenticate': 'Basic realm="Dashboard ERP Protheus"'})

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

# ========== Caminhos Windows ==========
CAMINHO_INIS = r'C:\TOTVS\P12PRD\bin'
CAMINHO_LIMPEZA = r'C:\TOTVS\scripts\limpa_upddistr.bat'

# ========== Funções Windows Services ==========
def obter_status_servico_windows(nome_servico):
    """Obtém o status de um serviço Windows"""
    try:
        # Conecta ao gerenciador de serviços
        hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
        try:
            # Abre o serviço
            hs = win32service.OpenService(hscm, nome_servico, win32service.SERVICE_ALL_ACCESS)
            try:
                # Obtém o status do serviço
                status = win32service.QueryServiceStatus(hs)
                state = status[1]
                
                # Obtém o PID do processo
                pid = "0"
                if state == win32service.SERVICE_RUNNING:
                    try:
                        # Procura o processo pelo nome do serviço
                        for proc in psutil.process_iter(['pid', 'name']):
                            if nome_servico.lower() in proc.info['name'].lower():
                                pid = str(proc.info['pid'])
                                break
                    except:
                        pass
                
                return (state == win32service.SERVICE_RUNNING, pid)
            finally:
                win32service.CloseServiceHandle(hs)
        finally:
            win32service.CloseServiceHandle(hscm)
    except Exception as e:
        print(f"Erro ao obter status do serviço {nome_servico}: {e}")
        return (False, "0")

def controlar_servico_windows(nome_servico, acao):
    """Controla um serviço Windows (start, stop, restart)"""
    try:
        if acao == "start":
            win32serviceutil.StartService(nome_servico)
        elif acao == "stop":
            win32serviceutil.StopService(nome_servico)
        elif acao == "restart":
            win32serviceutil.RestartService(nome_servico)
        return True
    except Exception as e:
        print(f"Erro ao {acao} o serviço {nome_servico}: {e}")
        return False

def finalizar_processo_windows(pid):
    """Finaliza um processo pelo PID"""
    try:
        processo = psutil.Process(int(pid))
        processo.terminate()
        return True
    except Exception as e:
        print(f"Erro ao finalizar processo {pid}: {e}")
        return False

# ========== Rota: Executar limpeza ==========
@app.route('/limpeza', methods=['GET', 'POST'])
@requer_autenticacao
def executar_limpeza():
    if g.permissao != 'admin':
        return Response("Acesso restrito ao admin.", 403)

    mensagem = ""
    conteudo_script = ""

    if os.path.exists(CAMINHO_LIMPEZA):
        with open(CAMINHO_LIMPEZA, 'r', encoding='utf-8') as f:
            conteudo_script = f.read()

    if request.method == 'POST' and request.form.get('acao') == 'salvar':
        novo_conteudo = request.form.get('conteudo')
        with open(CAMINHO_LIMPEZA, 'w', encoding='utf-8') as f:
            f.write(novo_conteudo)
        mensagem = "Script atualizado com sucesso!"
        conteudo_script = novo_conteudo

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Executar Limpeza</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </head>
    <body class="p-4">
    <div class="container">
        <h2 class="mb-4">Executar Script de Limpeza</h2>

        {% if mensagem %}
            <div class="alert alert-info">{{ mensagem }}</div>
        {% endif %}

        <form method="post">
            <button type="button" onclick="executarScript()" class="btn btn-danger me-2">Executar limpeza</button>
            <button type="submit" name="acao" value="salvar" class="btn btn-primary">Salvar alterações</button>
            <br><br>
            <textarea name="conteudo" rows="25" cols="100" style="font-family:monospace; width:100%;">{{ conteudo_script }}</textarea>
        </form>
        <br><a href="/" class="btn btn-secondary">Voltar</a>
    </div>

    <!-- Modal -->
    <div class="modal fade" id="modalExecucao" tabindex="-1" aria-labelledby="modalExecucaoLabel" aria-hidden="true">
      <div class="modal-dialog modal-xl modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="modalExecucaoLabel">Saída da Execução</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
          </div>
          <div class="modal-body">
            <pre id="saida-script" style="font-family:monospace; white-space: pre-wrap;"></pre>
          </div>
        </div>
      </div>
    </div>

    <script>
        function executarScript() {
            fetch("/limpeza/exec")
                .then(response => response.text())
                .then(data => {
                    document.getElementById("saida-script").textContent = data;
                    new bootstrap.Modal(document.getElementById("modalExecucao")).show();
                })
                .catch(error => {
                    document.getElementById("saida-script").textContent = "Erro: " + error;
                    new bootstrap.Modal(document.getElementById("modalExecucao")).show();
                });
        }
    </script>
    </body>
    </html>
    ''', conteudo_script=conteudo_script, mensagem=mensagem)

# ========== Rota AJAX ==========
@app.route('/limpeza/exec')
@requer_autenticacao
def limpeza_exec():
    if g.permissao != 'admin':
        return Response("Acesso não autorizado", 403)

    try:
        # Executa script .bat no Windows
        resultado = subprocess.run([CAMINHO_LIMPEZA],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   text=True,
                                   shell=True,
                                   encoding='utf-8')
        return f"Execução Finalizada:\n\n{resultado.stdout}"
    except Exception as e:
        return f"Erro ao executar script:\n{str(e)}"

# ========== Configurações ==========
SERVICOS = [
    "TOTVS_AppServer_Broker", "TOTVS_AppServer_Broker_Portal", "TOTVS_AppServer_Broker_Rest", "TOTVS_AppServer_Broker_WebApp",
    "TOTVS_AppServer_Portal_01", "TOTVS_AppServer_Compilar",
    "TOTVS_AppServer_Slave_01", "TOTVS_AppServer_Slave_02", "TOTVS_AppServer_Slave_03", "TOTVS_AppServer_Slave_04",
    "TOTVS_AppServer_Slave_05", "TOTVS_AppServer_Slave_06", "TOTVS_AppServer_Slave_07", "TOTVS_AppServer_Slave_08",
    "TOTVS_AppServer_Slave_09", "TOTVS_AppServer_Slave_10", "TOTVS_AppServer_TSS",
    "TOTVS_AppServer_WF_01_Faturamento", "TOTVS_AppServer_WF_02_Compras", "TOTVS_AppServer_WF_03_Financeiro",
    "TOTVS_AppServer_WF_05_InnCash", "TOTVS_AppServer_WF_06_LogFat", "TOTVS_AppServer_WF_07_Transmite",
    "TOTVS_AppServer_WSRest_01", "TOTVS_AppServer_WSRest_02", "TOTVS_AppServer_WSRest_03",
    "TOTVS_SmartView_Agent"
]

# ========== HTML PRINCIPAL ==========
HTML_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>Status dos Serviços do ERP Protheus - Windows</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body class="p-4 bg-light">
    <div class="container">
        <h2 class="mb-4">Status dos Serviços do ERP Protheus - Windows Server</h2>

        {% if g.permissao == 'admin' %}
        <div class="mb-3">
            <a href="/inis" class="btn btn-outline-primary me-2">Editar arquivos .INI</a>
            <a href="/logs" class="btn btn-outline-secondary me-2">Visualizar arquivos .LOG</a>
            <a href="/limpeza" class="btn btn-outline-danger">Executar limpeza</a>
        </div>
        {% endif %}

        {% if g.permissao == 'admin' %}
        <div class="mb-3">
            <button class="btn btn-success" onclick="confirmarAcao('iniciar_todos')">
                <i class="bi bi-play-circle-fill"></i> Iniciar Todos
            </button>
            <button class="btn btn-danger" onclick="confirmarAcao('parar_todos')">
                <i class="bi bi-stop-circle-fill"></i> Parar Todos
            </button>
        </div>
        {% endif %}

        <div class="mb-3">
            <label class="form-label">Tempo de atualização:</label>
            <select id="tempoRefresh" class="form-select d-inline w-auto" onchange="alterarTempo()">
                <option value="10000">10 segundos</option>
                <option value="20000">20 segundos</option>
                <option value="30000">30 segundos</option>
            </select>
            <button class="btn btn-primary ms-2" onclick="location.reload()">
                <i class="bi bi-arrow-clockwise"></i> Atualizar Agora
            </button>
        </div>

        <table class="table table-bordered table-hover bg-white shadow">
            <thead class="table-dark">
                <tr>
                    <th>Serviço</th>
                    <th>Status</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                {% for nome, status, pid in servicos %}
                <tr>
                    <td>{{ nome }}</td>
                    <td><span class="badge bg-{{ 'success' if status else 'danger' }}">
                        <i class="bi bi-{{ 'check-circle-fill' if status else 'x-circle-fill' }}"></i>
                        {{ 'Ativo' if status else 'Parado' }}
                    </span></td>
                    <td>
                        {% if g.permissao == 'admin' %}
                        <form method="post" action="/acao" class="d-inline form-acao">
                            <input type="hidden" name="servico" value="{{ nome }}">
                            <button class="btn btn-sm btn-success" name="acao" value="start">
                                <i class="bi bi-play-fill"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" name="acao" value="stop">
                                <i class="bi bi-stop-fill"></i>
                            </button>
                            <button class="btn btn-sm btn-warning text-white" name="acao" value="restart">
                                <i class="bi bi-arrow-clockwise"></i>
                            </button>
                            {% if status and pid != "0" %}
                            <button class="btn btn-sm btn-outline-danger" name="acao" value="kill" onclick="return confirm('Tem certeza que deseja forçar o encerramento deste serviço?')">
                                <i class="bi bi-exclamation-triangle-fill"></i> Kill
                            </button>
                            <input type="hidden" name="pid" value="{{ pid }}">
                            {% endif %}
                        </form>
                        {% else %}
                        <span class="text-muted">Somente visualização</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <p class="text-muted">Atualiza automaticamente conforme tempo selecionado</p>
    </div>

    <!-- Modal da saída da limpeza -->
    <div class="modal fade" id="modalSaidaLimpeza" tabindex="-1" aria-labelledby="saidaLimpezaLabel" aria-hidden="true">
      <div class="modal-dialog modal-xl modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="saidaLimpezaLabel">Saída da Limpeza</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
          </div>
          <div class="modal-body">
            <pre id="saida-script" style="font-family: monospace; white-space: pre-wrap;"></pre>
          </div>
        </div>
      </div>
    </div>

<script>
    let tempoAtualizacao = 10000;
    let timer = setTimeout(() => location.reload(), tempoAtualizacao);

    function alterarTempo() {
        const select = document.getElementById('tempoRefresh');
        tempoAtualizacao = parseInt(select.value);
        clearTimeout(timer);
        timer = setTimeout(() => location.reload(), tempoAtualizacao);
    }

    function confirmarAcao(acao) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/acao';

        const inputAcao = document.createElement('input');
        inputAcao.type = 'hidden';
        inputAcao.name = 'acao';
        inputAcao.value = acao;

        form.appendChild(inputAcao);
        document.body.appendChild(form);
        form.submit();
    }

    function executarLimpeza() {
        fetch("/limpeza/exec")
            .then(response => response.text())
            .then(data => {
                document.getElementById("saida-script").textContent = data;
                new bootstrap.Modal(document.getElementById("modalSaidaLimpeza")).show();
            })
            .catch(error => {
                document.getElementById("saida-script").textContent = "Erro: " + error;
                new bootstrap.Modal(document.getElementById("modalSaidaLimpeza")).show();
            });
    }
</script>
</body>
</html>
'''

# ========== Função para status ==========
def status_servico(nome):
    return obter_status_servico_windows(nome)

# ========== Rotas ==========
@app.route('/')
@requer_autenticacao
def home():
    status = [(s,) + status_servico(s) for s in SERVICOS]
    return render_template_string(HTML_DASHBOARD, servicos=status)

@app.route('/acao', methods=['POST'])
@requer_autenticacao
def acao():
    if g.permissao != 'admin':
        return Response("Acesso não autorizado para esta ação.", 403)

    servico = request.form.get('servico')
    acao = request.form.get('acao')

    if acao == 'iniciar_todos':
        for s in SERVICOS:
            controlar_servico_windows(s, 'start')
    elif acao == 'parar_todos':
        for s in SERVICOS:
            controlar_servico_windows(s, 'stop')
    elif acao in ['start', 'stop', 'restart'] and servico:
        controlar_servico_windows(servico, acao)
    elif acao == 'kill':
        pid = request.form.get('pid')
        if pid and pid.isdigit() and int(pid) > 0:
            finalizar_processo_windows(pid)

    return redirect(url_for('home'))

# ========== Editor de INIs ==========
@app.route('/inis')
@requer_autenticacao
def listar_inis():
    arquivos = []
    if os.path.exists(CAMINHO_INIS):
        for pasta in os.listdir(CAMINHO_INIS):
            caminho = os.path.join(CAMINHO_INIS, pasta)
            if os.path.isdir(caminho):
                for nome in os.listdir(caminho):
                    if nome.lower().endswith('.ini'):
                        arquivos.append((pasta, nome))
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Arquivos .INI</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>
    <body class="p-4">
    <div class="container">
        <h2>Arquivos .INI</h2>
        <ul class="list-group">
        {% for pasta, nome in arquivos %}
            <li class="list-group-item">
                <a href="{{ url_for('editar_ini', pasta=pasta, nome=nome) }}" class="text-decoration-none">
                    {{ nome }} ({{ pasta }})
                </a>
            </li>
        {% endfor %}
        </ul>
        <br><a href="/" class="btn btn-secondary">Voltar</a>
    </div>
    </body>
    </html>
    ''', arquivos=arquivos)

@app.route('/inis/<pasta>/<nome>', methods=['GET', 'POST'])
@requer_autenticacao
def editar_ini(pasta, nome):
    if g.permissao != 'admin':
        return Response("Acesso restrito ao admin.", 403)
        
    caminho = os.path.join(CAMINHO_INIS, pasta, nome)

    if request.method == 'POST':
        novo_conteudo = request.form.get('conteudo')
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(novo_conteudo)
        return redirect(url_for('listar_inis'))

    conteudo = ""
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Editando {{ nome }}</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>
    <body class="p-4">
    <div class="container">
        <h2>Editando {{ nome }} ({{ pasta }})</h2>
        <form method="post">
            <textarea name="conteudo" rows="25" class="form-control" style="font-family:monospace;">{{ conteudo }}</textarea>
            <br>
            <button type="submit" class="btn btn-primary">Salvar</button>
            <a href="/inis" class="btn btn-secondary">Voltar</a>
        </form>
    </div>
    </body>
    </html>
    ''', pasta=pasta, nome=nome, conteudo=conteudo)

# ========== Visualização de LOGs ==========
@app.route('/logs')
@requer_autenticacao
def listar_logs():
    arquivos = []
    if os.path.exists(CAMINHO_INIS):
        for pasta in os.listdir(CAMINHO_INIS):
            caminho = os.path.join(CAMINHO_INIS, pasta)
            if os.path.isdir(caminho):
                for nome in os.listdir(caminho):
                    if nome.lower().endswith('.log'):
                        arquivos.append((pasta, nome))
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Arquivos .LOG</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>
    <body class="p-4">
    <div class="container">
        <h2>Arquivos .LOG</h2>
        <ul class="list-group">
        {% for pasta, nome in arquivos %}
            <li class="list-group-item">
                <a href="{{ url_for('visualizar_log', pasta=pasta, nome=nome) }}" class="text-decoration-none">
                    {{ nome }} ({{ pasta }})
                </a>
            </li>
        {% endfor %}
        </ul>
        <br><a href="/" class="btn btn-secondary">Voltar</a>
    </div>
    </body>
    </html>
    ''', arquivos=arquivos)

@app.route('/logs/<pasta>/<nome>')
@requer_autenticacao
def visualizar_log(pasta, nome):
    if g.permissao != 'admin':
        return Response("Acesso restrito ao admin.", 403)
        
    caminho = os.path.join(CAMINHO_INIS, pasta, nome)
    conteudo = 'Arquivo não encontrado'
    
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
        except UnicodeDecodeError:
            # Tenta com encoding latin-1 se UTF-8 falhar
            with open(caminho, 'r', encoding='latin-1') as f:
                conteudo = f.read()
                
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Visualizando {{ nome }}</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>
    <body class="p-4">
    <div class="container">
        <h2>Visualizando {{ nome }} ({{ pasta }})</h2>
        <textarea rows="30" class="form-control" readonly style="font-family:monospace">{{ conteudo }}</textarea>
        <br><br><a href="/logs" class="btn btn-secondary">Voltar</a>
    </div>
    </body>
    </html>
    ''', pasta=pasta, nome=nome, conteudo=conteudo)

# ========== Execução ==========
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
