# Nome do Projeto: DashBoard para monitorar serviços do ERP Protheus em Linux
# Autor: Fernando Vernier
# Data: Abril/2025
# Tecnologias: Python, BootStrap, HTML.

from flask import Flask, render_template_string, request, redirect, url_for, Response, g
from functools import wraps
import subprocess

app = Flask(__name__)

# Usuários e permissões
USUARIOS = {
    "squad-erp": {
        "senha": "suasenha",
        "permissoes": "admin"
    },
    "viewer-erp": {
        "senha": "suasenha",
        "permissoes": "visualizacao"
    }
}

SERVICOS = [
    "appserver_broker", "appserver_broker_portal", "appserver_broker_rest", "appserver_broker_webapp",
    "appserver_portal_01", "appserver_compilar",
    "appserver_slave_01", "appserver_slave_02", "appserver_slave_03", "appserver_slave_04",
    "appserver_slave_05", "appserver_slave_06", "appserver_slave_07", "appserver_slave_08",
    "appserver_slave_09", "appserver_slave_10", "appserver_tss",
    "appserver_wsrest_01", "appserver_wsrest_02", "appserver_wsrest_03",
    "smart-view-agent"
]

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard ERP</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
</head>
<body class="p-4 bg-light">
    <div class="container">
        <h2 class="mb-4">Status dos Serviços do ERP Protheus</h2>

        {% if g.permissao == 'visualizacao' %}
        <div class="alert alert-info">Você está em modo somente visualização.</div>
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

    <!-- Modal de Confirmação -->
    <div class="modal fade" id="modalConfirmacao" tabindex="-1" aria-labelledby="modalConfirmacaoLabel" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="modalConfirmacaoLabel">Confirmação</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
          </div>
          <div class="modal-body">
            Tem certeza que deseja executar esta ação?
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            <button type="button" class="btn btn-primary" id="confirmarBotao">Confirmar</button>
          </div>
        </div>
      </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        let tempoAtualizacao = 10000; // padrão 10s
        let timer = setTimeout(() => location.reload(), tempoAtualizacao);

        function alterarTempo() {
            const select = document.getElementById('tempoRefresh');
            tempoAtualizacao = parseInt(select.value);
            clearTimeout(timer);
            timer = setTimeout(() => location.reload(), tempoAtualizacao);
        }

        const forms = document.querySelectorAll('.form-acao');
        forms.forEach(form => {
            form.addEventListener('submit', () => {
                const loading = document.createElement('div');
                loading.innerHTML = '<div class="mt-2 text-primary"><i class="bi bi-hourglass-split"></i> Processando ação...</div>';
                form.parentNode.appendChild(loading);
            });
        });

        let acaoEscolhida = '';

        function confirmarAcao(acao) {
            acaoEscolhida = acao;
            var modal = new bootstrap.Modal(document.getElementById('modalConfirmacao'));
            modal.show();
        }

        document.getElementById('confirmarBotao').addEventListener('click', function () {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/acao';

            const inputAcao = document.createElement('input');
            inputAcao.type = 'hidden';
            inputAcao.name = 'acao';
            inputAcao.value = acaoEscolhida;

            form.appendChild(inputAcao);
            document.body.appendChild(form);
            form.submit();
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

def iniciar_todos_servicos():
    for servico in SERVICOS:
        subprocess.run(["sudo", "systemctl", "start", f"{servico}.service"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

def parar_todos_servicos():
    for servico in SERVICOS:
        subprocess.run(["sudo", "systemctl", "stop", f"{servico}.service"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

@app.route('/', methods=['GET'])
@requer_autenticacao
def home():
    status = [(s,) + status_servico(s) for s in SERVICOS]
    return render_template_string(HTML, servicos=status)

@app.route('/acao', methods=['POST'])
@requer_autenticacao
def acao():
    if g.permissao != 'admin':
        return Response("Acesso não autorizado para esta ação.", 403)

    servico = request.form.get('servico')
    acao = request.form.get('acao')

    if acao == 'iniciar_todos':
        iniciar_todos_servicos()
    elif acao == 'parar_todos':
        parar_todos_servicos()
    elif acao in ['start', 'stop', 'restart'] and servico:
        subprocess.run(
            ["sudo", "systemctl", acao, f"{servico}.service"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
    elif acao == 'kill':
        pid = request.form.get('pid')
        if pid and pid.isdigit() and int(pid) > 0:
            subprocess.run(
                ["sudo", "kill", "-9", pid],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
            )
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8050)

