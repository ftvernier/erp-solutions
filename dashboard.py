from flask import Flask, render_template_string, request, redirect, url_for, Response, g
from functools import wraps
import subprocess
 
app = Flask(__name__)
 
# Usuários e permissões
USUARIOS = {
    "erpadmin": {
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
    "smart-view-agent"
]
 
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard ERP</title>
    <meta http-equiv="refresh" content="10">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
</head>
<body class="p-4 bg-light">
    <div class="container">
        <h2 class="mb-4">Status dos Serviços do ERP Protheus</h2>
 
        {% if g.permissao == 'visualizacao' %}
        <div class="alert alert-info">Você está em modo somente visualização.</div>
        {% endif %}
 
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
        <p class="text-muted">Atualiza a cada 10 segundos</p>
    </div>
 
    <script>
        const forms = document.querySelectorAll('.form-acao');
        forms.forEach(form => {
            form.addEventListener('submit', () => {
                const loading = document.createElement('div');
                loading.innerHTML = '<div class="mt-2 text-primary"><i class="bi bi-hourglass-split"></i> ? Processando ação...</div>';
                form.parentNode.appendChild(loading);
            });
        });
    </script>
</body>
</html>
'''
 
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
 
    servico = request.form['servico']
    acao = request.form['acao']
    if acao in ['start', 'stop', 'restart']:
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
