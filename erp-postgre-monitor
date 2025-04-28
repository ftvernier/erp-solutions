from flask import Flask, render_template_string, request, redirect, url_for
import psycopg2

app = Flask(__name__)

# Conexão ao banco PostgreSQL
def conectar_sql():
    conn = psycopg2.connect(
        host="SEU_HOST",
        database="SUA_DATABASE",
        user="SEU_USUARIO",
        password="SUA_SENHA",
        port="5432"
    )
    return conn

# HTML base com Auto Refresh e Atualizar Agora
HTML = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>ERP SQL Monitor - PostgreSQL</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container mt-4">
    <h2 class="mb-4">ERP SQL Monitor - PostgreSQL</h2>
    <ul class="nav nav-tabs mb-4" id="tabMenu">
        <li class="nav-item"><a class="nav-link {% if aba == 'sessoes' %}active{% endif %}" href="/sessoes">Sessões</a></li>
        <li class="nav-item"><a class="nav-link {% if aba == 'bloqueios' %}active{% endif %}" href="/bloqueios">Bloqueios</a></li>
        <li class="nav-item"><a class="nav-link {% if aba == 'crescimento' %}active{% endif %}" href="/crescimento">Crescimento Tabelas</a></li>
        <li class="nav-item"><a class="nav-link {% if aba == 'espaco' %}active{% endif %}" href="/espaco">Espaço Disco</a></li>
    </ul>

    <div class="d-flex mb-4">
        <div>
            <label for="tempoAtualizacao" class="form-label">Atualizar a cada:</label>
            <select id="tempoAtualizacao" class="form-select d-inline w-auto" onchange="alterarTempo()">
                <option value="10000">10 segundos</option>
                <option value="20000">20 segundos</option>
                <option value="30000">30 segundos</option>
            </select>
        </div>
        <div class="ms-3 align-self-end">
            <button class="btn btn-primary" onclick="atualizarAgora()">Atualizar Agora</button>
        </div>
    </div>

    <div class="card shadow p-4">
        {{ conteudo|safe }}
    </div>
</div>

<script>
    let tempoAtualizacao = localStorage.getItem('tempoAtualizacao') || 10000;

    function alterarTempo() {
        const select = document.getElementById('tempoAtualizacao');
        tempoAtualizacao = parseInt(select.value);
        localStorage.setItem('tempoAtualizacao', tempoAtualizacao);
        clearTimeout(window.autoReload);
        iniciarAutoReload();
    }

    function atualizarAgora() {
        location.reload();
    }

    function iniciarAutoReload() {
        window.autoReload = setTimeout(() => {
            location.reload();
        }, tempoAtualizacao);
    }

    document.addEventListener('DOMContentLoaded', () => {
        const select = document.getElementById('tempoAtualizacao');
        select.value = tempoAtualizacao;
        iniciarAutoReload();
    });
</script>

</body>
</html>
'''

@app.route('/')
def home():
    return redirect(url_for('sessoes'))

# Sessoes Ativas
@app.route('/sessoes')
def sessoes():
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                pid, usename, client_addr, state, backend_start, now() - backend_start AS tempo_conexao
            FROM pg_stat_activity
            WHERE pid <> pg_backend_pid()
            ORDER BY backend_start DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        conteudo = '<table class="table table-bordered table-hover"><thead class="table-dark"><tr><th>PID</th><th>Usuário</th><th>Cliente</th><th>Status</th><th>Iniciado</th><th>Tempo Conexão</th><th>Ações</th></tr></thead><tbody>'
        for row in rows:
            conteudo += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{str(row[5]).split(".")[0]}</td>'
            conteudo += f'<td><form method="post" action="/kill/{row[0]}" onsubmit="return confirm(\'Deseja encerrar esta conexão?\')"><button type="submit" class="btn btn-sm btn-danger">Kill</button></form></td></tr>'
        conteudo += '</tbody></table>'

    except Exception as e:
        conteudo = f'<div class="alert alert-danger">Erro ao buscar sessões: {str(e)}</div>'

    return render_template_string(HTML, conteudo=conteudo, aba='sessoes')

# Kill Sessao
@app.route('/kill/<int:pid>', methods=['POST'])
def kill(pid):
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute(f"SELECT pg_terminate_backend({pid});")
        conn.commit()
        conn.close()
        return redirect(url_for('sessoes'))
    except Exception as e:
        return f"<h3>Erro ao encerrar sessão: {str(e)}</h3>"

# Bloqueios
@app.route('/bloqueios')
def bloqueios():
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                l.pid, a.usename, l.mode, l.locktype, a.query
            FROM pg_locks l
            JOIN pg_stat_activity a ON l.pid = a.pid
            WHERE NOT l.granted
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            conteudo = '<div class="alert alert-success">Nenhum bloqueio pendente encontrado. ✅</div>'
        else:
            conteudo = '<table class="table table-bordered table-hover"><thead class="table-dark"><tr><th>PID</th><th>Usuário</th><th>Tipo de Lock</th><th>Modo</th><th>Query</th></tr></thead><tbody>'
            for row in rows:
                conteudo += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[3]}</td><td>{row[2]}</td><td><pre>{row[4]}</pre></td></tr>'
            conteudo += '</tbody></table>'

    except Exception as e:
        conteudo = f'<div class="alert alert-danger">Erro ao buscar bloqueios: {str(e)}</div>'

    return render_template_string(HTML, conteudo=conteudo, aba='bloqueios')

# Crescimento de Tabelas
@app.route('/crescimento')
def crescimento():
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT relname AS tabela, reltuples::BIGINT AS linhas_estimadas, pg_total_relation_size(relid) / 1024 / 1024 AS tamanho_mb
            FROM pg_catalog.pg_statio_user_tables
            ORDER BY linhas_estimadas DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        conteudo = '<table class="table table-bordered table-hover"><thead class="table-dark"><tr><th>Tabela</th><th>Linhas Estimadas</th><th>Tamanho (MB)</th></tr></thead><tbody>'
        for row in rows:
            conteudo += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]:.2f}</td></tr>'
        conteudo += '</tbody></table>'

    except Exception as e:
        conteudo = f'<div class="alert alert-danger">Erro ao buscar crescimento: {str(e)}</div>'

    return render_template_string(HTML, conteudo=conteudo, aba='crescimento')

# Espaço em Disco
@app.route('/espaco')
def espaco():
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT datname, pg_database_size(datname) / 1024 / 1024 AS tamanho_mb
            FROM pg_database
            ORDER BY tamanho_mb DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        conteudo = '<table class="table table-bordered table-hover"><thead class="table-dark"><tr><th>Base de Dados</th><th>Tamanho (MB)</th></tr></thead><tbody>'
        for row in rows:
            conteudo += f'<tr><td>{row[0]}</td><td>{row[1]:.2f}</td></tr>'
        conteudo += '</tbody></table>'

    except Exception as e:
        conteudo = f'<div class="alert alert-danger">Erro ao buscar espaço: {str(e)}</div>'

    return render_template_string(HTML, conteudo=conteudo, aba='espaco')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8060)
