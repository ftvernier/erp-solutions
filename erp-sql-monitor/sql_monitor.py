from flask import Flask, render_template_string, request, redirect, url_for
import pyodbc

app = Flask(__name__)

# Conexão ao banco de dados
def conectar_sql():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=seuservidor;'
        'DATABASE=suadatabase;'
        'UID=usuario;'
        'PWD=senha;'
    )
    return conn

# HTML base
HTML = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>ERP SQL Monitor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body class="bg-light">

<div class="container mt-4">
    <h2 class="mb-4">ERP SQL Monitor - TOTVS2310</h2>

    <!-- Menu Tabs -->
    <ul class="nav nav-tabs mb-4" id="tabMenu">
        <li class="nav-item"><a class="nav-link {% if aba == 'bloqueios' %}active{% endif %}" href="/bloqueios">Bloqueios</a></li>
        <li class="nav-item"><a class="nav-link {% if aba == 'crescimento' %}active{% endif %}" href="/crescimento">Crescimento Tabelas</a></li>
        <li class="nav-item"><a class="nav-link {% if aba == 'sessoes' %}active{% endif %}" href="/sessoes">Sessões Ativas</a></li>
        <li class="nav-item"><a class="nav-link {% if aba == 'fragmentacao' %}active{% endif %}" href="/fragmentacao">Fragmentação Índices</a></li>
        <li class="nav-item"><a class="nav-link {% if aba == 'backup' %}active{% endif %}" href="/backup">Backup Status</a></li>
        <li class="nav-item"><a class="nav-link {% if aba == 'espaco' %}active{% endif %}" href="/espaco">Espaço Disco</a></li>
    </ul>

    <!-- Controle de Atualização -->
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
    return redirect(url_for('bloqueios'))

@app.route('/bloqueios')
def bloqueios():
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                blocking_session_id AS SessaoBloqueadora,
                session_id AS SessaoBloqueada,
                wait_type,
                wait_time / 1000 AS TempoEsperaSegundos,
                text AS ComandoSQL
            FROM sys.dm_exec_requests r
            CROSS APPLY sys.dm_exec_sql_text(r.sql_handle)
            WHERE blocking_session_id <> 0
            ORDER BY TempoEsperaSegundos DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            conteudo = '<div class="alert alert-success">Nenhum bloqueio encontrado. Banco saudável! ✅</div>'
        else:
            conteudo = '''
            <table class="table table-bordered table-hover">
                <thead class="table-dark">
                    <tr>
                        <th>Quem Bloqueia</th>
                        <th>Quem Está Bloqueado</th>
                        <th>Tipo de Espera</th>
                        <th>Tempo de Espera (s)</th>
                        <th>Comando SQL</th>
                    </tr>
                </thead>
                <tbody>
            '''
            for row in rows:
                conteudo += f'''
                    <tr>
                        <td>{row.SessaoBloqueadora}</td>
                        <td>{row.SessaoBloqueada}</td>
                        <td>{row.wait_type}</td>
                        <td>{row.TempoEsperaSegundos}</td>
                        <td><pre>{row.ComandoSQL}</pre></td>
                    </tr>
                '''
            conteudo += '</tbody></table>'
    except Exception as e:
        conteudo = f'<div class="alert alert-danger">Erro ao buscar bloqueios: {str(e)}</div>'

    return render_template_string(HTML, conteudo=conteudo, aba='bloqueios')
@app.route('/crescimento')
def crescimento():
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.NAME AS NomeTabela,
                SUM(p.rows) AS TotalLinhas,
                SUM(a.total_pages) * 8 / 1024 AS TamanhoMB
            FROM 
                sys.tables t
            INNER JOIN      
                sys.indexes i ON t.OBJECT_ID = i.object_id
            INNER JOIN 
                sys.partitions p ON i.object_id = p.OBJECT_ID AND i.index_id = p.index_id
            INNER JOIN 
                sys.allocation_units a ON p.partition_id = a.container_id
            WHERE 
                t.is_ms_shipped = 0
            GROUP BY 
                t.Name
            ORDER BY 
                TotalLinhas DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        conteudo = '''
        <table class="table table-bordered table-hover">
            <thead class="table-dark">
                <tr>
                    <th>Tabela</th>
                    <th>Total de Linhas</th>
                    <th>Tamanho (MB)</th>
                    <th>Tamanho (GB)</th>
                </tr>
            </thead>
            <tbody>
        '''
        for row in rows:
            tamanho_gb = float(row.TamanhoMB) / 1024
            conteudo += f'''
                <tr>
                    <td>{row.NomeTabela}</td>
                    <td>{row.TotalLinhas}</td>
                    <td>{row.TamanhoMB:.2f}</td>
                    <td>{tamanho_gb:.2f}</td>
                </tr>
            '''
        conteudo += '</tbody></table>'

    except Exception as e:
        conteudo = f'<div class="alert alert-danger">Erro ao buscar crescimento: {str(e)}</div>'

    return render_template_string(HTML, conteudo=conteudo, aba='crescimento')
@app.route('/sessoes')
def sessoes():
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                session_id,
                login_name,
                host_name,
                status,
                cpu_time,
                memory_usage
            FROM sys.dm_exec_sessions
            WHERE is_user_process = 1
        """)
        rows = cursor.fetchall()
        conn.close()

        conteudo = '''
        <table class="table table-bordered table-hover">
            <thead class="table-dark">
                <tr>
                    <th>ID Sessão</th>
                    <th>Login</th>
                    <th>Host</th>
                    <th>Status</th>
                    <th>CPU Time</th>
                    <th>Memória (KB)</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
        '''
        for row in rows:
            conteudo += f'''
                <tr>
                    <td>{row.session_id}</td>
                    <td>{row.login_name}</td>
                    <td>{row.host_name}</td>
                    <td>{row.status}</td>
                    <td>{row.cpu_time}</td>
                    <td>{row.memory_usage * 8}</td>
                    <td>
                        <form method="post" action="/kill/{row.session_id}" onsubmit="return confirm('Deseja realmente encerrar esta sessão?')">
                            <button type="submit" class="btn btn-sm btn-danger">Kill</button>
                        </form>
                    </td>
                </tr>
            '''
        conteudo += '</tbody></table>'

    except Exception as e:
        conteudo = f'<div class="alert alert-danger">Erro ao buscar sessões: {str(e)}</div>'

    return render_template_string(HTML, conteudo=conteudo, aba='sessoes')

# Rota para encerrar sessão (KILL)
@app.route('/kill/<int:session_id>', methods=['POST'])
def kill(session_id):
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute(f"KILL {session_id}")
        conn.commit()
        conn.close()
        return redirect(url_for('sessoes'))
    except Exception as e:
        return f"<h3>Erro ao encerrar sessão: {str(e)}</h3>"
@app.route('/fragmentacao')
def fragmentacao():
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                dbschemas.name AS Esquema,
                dbtables.name AS Tabela,
                dbindexes.name AS Indice,
                indexstats.avg_fragmentation_in_percent AS Fragmentacao
            FROM sys.dm_db_index_physical_stats (DB_ID(), NULL, NULL, NULL, 'LIMITED') indexstats
            INNER JOIN sys.tables dbtables ON dbtables.[object_id] = indexstats.[object_id]
            INNER JOIN sys.schemas dbschemas ON dbtables.[schema_id] = dbschemas.[schema_id]
            INNER JOIN sys.indexes AS dbindexes ON dbindexes.[object_id] = indexstats.[object_id]
                                                AND indexstats.index_id = dbindexes.index_id
            WHERE indexstats.database_id = DB_ID()
            ORDER BY Fragmentacao DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        conteudo = '''
        <table class="table table-bordered table-hover">
            <thead class="table-dark">
                <tr>
                    <th>Esquema</th>
                    <th>Tabela</th>
                    <th>Índice</th>
                    <th>Fragmentação (%)</th>
                </tr>
            </thead>
            <tbody>
        '''
        for row in rows:
            conteudo += f'''
                <tr>
                    <td>{row.Esquema}</td>
                    <td>{row.Tabela}</td>
                    <td>{row.Indice}</td>
                    <td>{row.Fragmentacao:.2f}</td>
                </tr>
            '''
        conteudo += '</tbody></table>'

    except Exception as e:
        conteudo = f'<div class="alert alert-danger">Erro ao buscar fragmentação: {str(e)}</div>'

    return render_template_string(HTML, conteudo=conteudo, aba='fragmentacao')
@app.route('/backup')
def backup():
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                database_name,
                MAX(backup_finish_date) AS UltimoBackup,
                CASE 
                    WHEN type = 'D' THEN 'Full'
                    WHEN type = 'I' THEN 'Diferencial'
                    WHEN type = 'L' THEN 'Log'
                    ELSE 'Outro'
                END AS TipoBackup
            FROM msdb.dbo.backupset
            GROUP BY database_name, type
            ORDER BY UltimoBackup DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        conteudo = '''
        <table class="table table-bordered table-hover">
            <thead class="table-dark">
                <tr>
                    <th>Base</th>
                    <th>Último Backup</th>
                    <th>Tipo</th>
                </tr>
            </thead>
            <tbody>
        '''
        for row in rows:
            conteudo += f'''
                <tr>
                    <td>{row.database_name}</td>
                    <td>{row.UltimoBackup}</td>
                    <td>{row.TipoBackup}</td>
                </tr>
            '''
        conteudo += '</tbody></table>'

    except Exception as e:
        conteudo = f'<div class="alert alert-danger">Erro ao buscar backups: {str(e)}</div>'

    return render_template_string(HTML, conteudo=conteudo, aba='backup')
@app.route('/espaco')
def espaco():
    try:
        conn = conectar_sql()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                DB_NAME(database_id) AS Base,
                SUM(size) * 8 / 1024 AS TamanhoMB
            FROM sys.master_files
            GROUP BY database_id
        """)
        rows = cursor.fetchall()
        conn.close()

        conteudo = '''
        <table class="table table-bordered table-hover">
            <thead class="table-dark">
                <tr>
                    <th>Base</th>
                    <th>Tamanho (MB)</th>
                    <th>Tamanho (GB)</th>
                    <th>Tamanho (TB)</th>
                </tr>
            </thead>
            <tbody>
        '''
        for row in rows:
            tamanho_gb = float(row.TamanhoMB) / 1024
            tamanho_tb = tamanho_gb / 1024
            conteudo += f'''
                <tr>
                    <td>{row.Base}</td>
                    <td>{row.TamanhoMB:.2f}</td>
                    <td>{tamanho_gb:.2f}</td>
                    <td>{tamanho_tb:.4f}</td>
                </tr>
            '''
        conteudo += '</tbody></table>'

    except Exception as e:
        conteudo = f'<div class="alert alert-danger">Erro ao buscar espaço: {str(e)}</div>'

    return render_template_string(HTML, conteudo=conteudo, aba='espaco')
    
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8060)
