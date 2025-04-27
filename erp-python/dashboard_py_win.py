from flask import Flask, render_template_string, request, redirect, url_for, Response, g
from functools import wraps
import subprocess
import platform

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

# Serviços (nomes dos serviços configurados no Windows)
SERVICOS = [
    "ProtheusBroker", "ProtheusPortal", "ProtheusRest", "ProtheusWebApp",
    "ProtheusPortal01", "ProtheusCompilar",
    "ProtheusSlave01", "ProtheusSlave02", "ProtheusSlave03", "ProtheusSlave04",
    "ProtheusSlave05", "ProtheusSlave06", "ProtheusSlave07", "ProtheusSlave08",
    "ProtheusSlave09", "ProtheusSlave10", "ProtheusTSS",
    "ProtheusWF01", "ProtheusWF02", "ProtheusWF03",
    "ProtheusWF05", "ProtheusWF06", "ProtheusWF07",
    "ProtheusWsRest01", "ProtheusWsRest02", "ProtheusWsRest03",
    "SmartViewAgent"
]

# ------------------------------------------
# Funções Flask (Backend) adaptadas para Windows
# ------------------------------------------

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
        output = subprocess.run(
            ["sc", "query", nome],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        ).stdout

        status = "STOPPED"
        pid = "0"

        for line in output.splitlines():
            if "STATE" in line:
                if "RUNNING" in line:
                    status = "RUNNING"
            if "PID" in line:
                pid = line.strip().split(":")[-1].strip()

        return (status == "RUNNING", pid)
    except Exception as e:
        print(f"[ERRO] {nome}: {e}")
        return (False, "0")

def iniciar_todos_servicos():
    for servico in SERVICOS:
        subprocess.run(["sc", "start", servico],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

def parar_todos_servicos():
    for servico in SERVICOS:
        subprocess.run(["sc", "stop", servico],
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
    elif acao in ['start', 'stop'] and servico:
        subprocess.run(["sc", acao, servico],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    elif acao == 'restart' and servico:
        subprocess.run(["sc", "stop", servico],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        subprocess.run(["sc", "start", servico],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    elif acao == 'kill':
        pid = request.form.get('pid')
        if pid and pid.isdigit() and int(pid) > 0:
            subprocess.run(["taskkill", "/PID", pid, "/F"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8050)
