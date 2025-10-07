#!/usr/bin/python3.12
# -*- coding: utf-8 -*-
"""
Script de Deploy Protheus - timeouts + fallback + validações
Autor: Fernando Tadeu Vernier
Rev: 16/09/2025
"""

import os
import sys
import shutil
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ==================== CONFIG ====================
REPO_PATH = "/opt/git_protheus/protheus/"
BASE_PATH = "/totvs/p12prd/apo"
BIN_PATH = "/totvs/p12prd/bin"
BACKUP_BASE = "/totvs/p12prd/apo/backup_rpo"
SERVICOS_SCRIPT = "/totvs/scripts/gerenciar_servicos.sh"

# Includes: VSCode usava exatamente esse caminho
INCLUDES_PATH = "/opt/git_protheus/protheus/Includes"
INCLUDES_JOINED = f"{INCLUDES_PATH}"

# Diretórios que contêm RPOs
DIRS_RPO = ["producao", "solar", "faturamento"]

# Binário de compilação
APPSERVER_BIN = "/totvs/p12prd/bin/appserver_compilar/appsrvlinux"
APPSERVER_BIN_DIR = str(Path(APPSERVER_BIN).parent)

# Permissões elevadas (definido via env no Actions)
SUDO = os.getenv("SUDO", "").strip()  # ex.: "sudo -n"
def sudo_cmd(c: str) -> str:
    return f"{SUDO} {c}".strip() if SUDO else c

# Timeouts (override via env se quiser)
TIMEOUT_PARAR = int(os.getenv("TIMEOUT_PARAR", "900"))
TIMEOUT_INICIAR = int(os.getenv("TIMEOUT_INICIAR", "180"))
TIMEOUT_EXCLUSIVO = int(os.getenv("TIMEOUT_EXCLUSIVO", "120"))

# Log
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
LOG_FILE = f"/tmp/deploy_protheus_{timestamp}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ==================== EXCEPTIONS ====================
class DeployError(Exception): ...
class CompilationError(DeployError): ...
class ValidationError(DeployError): ...

# ==================== UTILS ====================
def run_git_command(args: List[str]) -> str:
    try:
        res = subprocess.run(["git"] + args, cwd=REPO_PATH, capture_output=True, text=True, timeout=60)
        return res.stdout.strip() if res.returncode == 0 else ""
    except Exception as e:
        logger.error(f"Erro no git {' '.join(args)}: {e}")
        return ""

def run_command(cmd: str, cwd: Optional[str] = None, timeout: int = 300) -> bool:
    try:
        res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        if res.stdout:
            for line in res.stdout.strip().splitlines():
                logger.info(line)
        if res.returncode != 0:
            logger.error(f"Comando falhou (rc={res.returncode}): {cmd}")
            if res.stderr:
                logger.error(f"STDERR: {res.stderr.strip()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Comando expirou (timeout {timeout}s): {cmd}")
        return False
    except Exception as e:
        logger.error(f"Erro ao executar {cmd}: {e}")
        return False

def check_no_process(pattern: str) -> bool:
    res = subprocess.run(f"pgrep -f {pattern}", shell=True, capture_output=True)
    return res.returncode != 0  # True se NÃO encontrou

def wait_until_no_process(pattern: str, timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if check_no_process(pattern):
            return True
        time.sleep(1)
    return False

# ==================== PRECHECK DE SERVIÇOS ====================
_CRITICOS = [
    "appserver_broker_rest",
    "appserver_broker_webapp",
    "appserver_portal_01",
    "appserver_compilar",
    "appserver_slave_01",
    "appserver_slave_02",
    "appserver_slave_03",
    "appserver_slave_04",
    "appserver_slave_05",
    "appserver_slave_06",
    "appserver_slave_07",
    "appserver_slave_08",
    "appserver_slave_09",
    "appserver_slave_10",
    "appserver_tss",
    "appserver_wf_01_faturamento",
    "appserver_wf_02_compras",
    "appserver_wf_03_financeiro",
]

def _status_systemd(servico: str) -> str:
    r = subprocess.run(
        f"systemctl is-active {servico}.service",
        shell=True, capture_output=True, text=True
    )
    return (r.stdout or "").strip() or (r.stderr or "").strip() or "unknown"

def validar_servicos_ativos_antes_do_deploy() -> None:
    """
    Aborta o deploy caso o ERP já esteja parado:
    - Se NÃO existir nenhum processo 'appserver' rodando (pgrep).
    - Loga o status dos serviços críticos para diagnóstico.
    """
    if check_no_process("appserver"):
        logger.error("Detectado ERP parado: nenhum processo 'appserver' em execução.")
        for s in _CRITICOS:
            logger.info(f"Status {s}: {_status_systemd(s)}")
        raise DeployError("Serviços do ERP estão parados; abortando deploy.")

# ==================== LIMPEZA SEGURA DO WORKSPACE ====================
def _is_git_tracked(path: Path) -> bool:
    """Retorna True se o path é rastreado pelo Git (versionado)."""
    try:
        rel = path.relative_to(REPO_PATH)
    except ValueError:
        return False
    r = subprocess.run(
        ["git", "-C", REPO_PATH, "ls-files", "--error-unmatch", str(rel)],
        capture_output=True, text=True
    )
    return r.returncode == 0

def _limpar_lixo_workspace() -> None:
    """
    Remove somente arquivos de lixo que podem confundir o appre/compilação,
    sem tocar em configs úteis do VS Code e SEM apagar arquivos versionados.
    """
    root = Path(REPO_PATH)

    # 1) apaga a pasta de cache do VS Code dentro do repo (seguro)
    cache_dir = root / ".vscode" / ".cache"
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir, ignore_errors=True)
            logger.info(f"Removing {cache_dir.relative_to(root)}")
        except Exception:
            pass

    # 2) candidatos: artefatos temporários do preprocessor e logs de erro locais
    candidates: List[Path] = []
    candidates += list(root.rglob("*.erx"))
    candidates += list(root.rglob("*.erx_*"))
    candidates += [root / "console_error.log"]

    for p in candidates:
        try:
            if not p.exists():
                continue
            # nunca apagar algo versionado no Git
            if _is_git_tracked(p):
                logger.info(f"Preservando arquivo versionado: {p.relative_to(root)}")
                continue

            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
                logger.info(f"Removing {p.relative_to(root)}")
            else:
                p.unlink(missing_ok=True)
                logger.info(f"Removing {p.relative_to(root)}")
        except Exception:
            # limpeza é best-effort; não falha o deploy
            pass

# ==================== STEPS ====================
def verificar_prerequisitos() -> None:
    logger.info("Verificando pré-requisitos...")
    for path in [REPO_PATH, BASE_PATH, BIN_PATH, BACKUP_BASE, SERVICOS_SCRIPT, APPSERVER_BIN, INCLUDES_PATH]:
        if not Path(path).exists():
            raise DeployError(f"Caminho não encontrado: {path}")
    if not os.access(APPSERVER_BIN, os.X_OK):
        raise DeployError(f"Sem permissão de execução para: {APPSERVER_BIN}")
    logger.info("Pré-requisitos OK")

def obter_ultima_versao_rpo() -> Dict[str, str]:
    """Retorna o diretório da última versão de RPO por ambiente (producao/solar/faturamento)."""
    rpo_dirs: Dict[str, str] = {}
    for dir_name in DIRS_RPO:
        rpo_path = Path(BASE_PATH) / dir_name
        if not rpo_path.exists():
            logger.warning(f"Ambiente '{dir_name}' não encontrado em {rpo_path}")
            continue
        # pega subpastas com padrão de timestamp (tem "_")
        subdirs = [d for d in rpo_path.iterdir() if d.is_dir() and "_" in d.name]
        if not subdirs:
            logger.warning(f"Nenhuma versão encontrada em {rpo_path}")
            continue
        subdirs.sort(key=lambda p: p.name)  # AAAAMMDD_HHMM → ordenação lex funciona
        latest = subdirs[-1]
        rpo_dirs[dir_name] = str(latest)
        logger.info(f"Última versão {dir_name}: {latest.name}")
    return rpo_dirs

def obter_rpo_compilado() -> str:
    compilar_path = Path(BASE_PATH) / "compilar"
    if not compilar_path.exists():
        raise DeployError("Diretório de compilação não encontrado")
    subdirs = [d.name for d in compilar_path.iterdir() if d.is_dir() and "_" in d.name]
    if not subdirs:
        raise DeployError("Nenhum diretório de compilação encontrado")
    subdirs.sort()
    return str(compilar_path / subdirs[-1])

def atualizar_repositorio() -> None:
    logger.info("Atualizando repositório...")
    # Limpeza antes do pull para evitar appre confuso com artefatos locais
    _limpar_lixo_workspace()
    for cmd in ["git fetch origin", "git checkout main", "git pull origin main"]:
        if not run_command(cmd, REPO_PATH, timeout=120):
            raise DeployError(f"Falha ao executar: {cmd}")
    logger.info("Repositório atualizado")

def identificar_arquivos_alterados() -> List[str]:
    """
    1) Se o Actions passar CHANGED_FILES no ambiente, usa essa lista.
    2) Caso contrário, diff entre HEAD@{1} (HEAD anterior ao pull) e HEAD.
    3) Fallback final: HEAD~1..HEAD.
    """
    logger.info("Identificando arquivos alterados...")

    env_list = os.getenv("CHANGED_FILES", "").strip()
    arquivos: List[str] = []

    if env_list:
        logger.info(f"CHANGED_FILES recebido (len={len(env_list)}).")
        logger.info("Arquivos recebidos do Actions:")
        for linha in env_list.splitlines():
            f = linha.strip()
            if not f:
                continue
            logger.info(f"  - {f}")
            if f.lower().endswith(".prw") or f.lower().endswith(".tlpp"):
                arquivos.append(f)
        if arquivos:
            logger.info("Arquivos .prw/.tlpp a compilar (via Actions):")
            for f in arquivos:
                logger.info(f"  - {f}")
            return arquivos

    logger.info("CHANGED_FILES vazio e arquivo não encontrado; usando fallback local.")
    base = run_git_command(["rev-parse", "HEAD@{1}"]) or run_git_command(["rev-parse", "HEAD~1"])
    if not base:
        logger.warning("Não foi possível determinar o commit base; seguindo sem alterações.")
        return []

    all_files = run_git_command(["diff", "--name-only", base, "HEAD"])
    logger.info("Todos os arquivos alterados (fallback):")
    for linha in all_files.split("\n"):
        f = (linha or "").strip()
        if not f:
            continue
        logger.info(f"  - {f}")
        if f.lower().endswith(".prw") or f.lower().endswith(".tlpp"):
            arquivos.append(f)

    if not arquivos:
        logger.info("Nenhum arquivo .prw/.tlpp encontrado")
        return []

    return arquivos

def gerenciar_servicos(acao: str) -> None:
    """
    - parar: até TIMEOUT_PARAR; se falhar, aplica TERM→KILL (sudo) em 'appserver'
    - iniciar: até TIMEOUT_INICIAR
    - exclusivo: até TIMEOUT_EXCLUSIVO (warning se falhar)
    """
    logger.info(f"Serviços: {acao}...")
    to = {"parar": TIMEOUT_PARAR, "iniciar": TIMEOUT_INICIAR, "exclusivo": TIMEOUT_EXCLUSIVO}.get(acao, 300)
    ok = run_command(f"bash {SERVICOS_SCRIPT} {acao}", timeout=to)

    if not ok:
        if acao == "parar":
            logger.warning("Parada falhou/expirou. Aplicando fallback TERM→KILL (sudo).")
            run_command(sudo_cmd("pkill -f appserver || true"), timeout=15)
            if wait_until_no_process("appserver", timeout=30):
                logger.info("Fallback: processos encerrados após SIGTERM.")
            else:
                run_command(sudo_cmd("pkill -9 -f appserver || true"), timeout=10)
                if wait_until_no_process("appserver", timeout=15):
                    logger.info("Fallback: processos encerrados após SIGKILL.")
                else:
                    raise DeployError("Falha ao parar serviços: processos persistem após SIGKILL")
        elif acao == "iniciar":
            raise DeployError("Falha ao iniciar serviços")
        elif acao == "exclusivo":
            logger.warning("Falha ao entrar em exclusivo; prosseguindo.")
        else:
            raise DeployError(f"Falha ao {acao} serviços")

    logger.info(f"Serviços: {acao} OK")

def backup_rpos_e_inis() -> str:
    """
    Faz backup dos RPOs (.rpo) da última versão de cada ambiente e dos INIs.
    Copiamos arquivo a arquivo para evitar pastas vazias/links/peculiaridades.
    """
    logger.info("Fazendo backup...")
    backup_dir = Path(BACKUP_BASE) / f"{timestamp}_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # --- RPOs (copia somente *.rpo da última versão de cada ambiente)
    ultimos = obter_ultima_versao_rpo()
    for env, src_dir in ultimos.items():
        src = Path(src_dir)
        dst = backup_dir / f"rpo_{env}"
        dst.mkdir(parents=True, exist_ok=True)

        rpos = sorted(src.glob("*.rpo"))
        if not rpos:
            logger.warning(f"Nenhum .rpo encontrado em {src} (env={env})")
        else:
            for rpo in rpos:
                shutil.copy2(rpo, dst / rpo.name)
                logger.info(f"Backup RPO {env}: {rpo.name}")

    # --- INIs
    ini_dir = backup_dir / "inis"
    ini_dir.mkdir(exist_ok=True)
    for app_dir in Path(BIN_PATH).iterdir():
        if app_dir.is_dir() and app_dir.name.startswith("appserver_"):
            dst = ini_dir / app_dir.name
            dst.mkdir(exist_ok=True)
            for ini_name in ["appserver.ini", "appsrvlinux.ini"]:
                ini_path = app_dir / ini_name
                if ini_path.is_file():
                    shutil.copy2(ini_path, dst)
                    logger.info(f"Backup INI: {app_dir.name}/{ini_name}")

    logger.info(f"Backup completo: {backup_dir}")
    return str(backup_dir)

def criar_pastas_timestamp() -> Dict[str, str]:
    logger.info("Criando pastas timestamp...")
    novos: Dict[str, str] = {}
    for dir_name in DIRS_RPO:
        p = Path(BASE_PATH) / dir_name / timestamp
        p.mkdir(parents=True, exist_ok=True)
        novos[dir_name] = str(p)
        logger.info(f"Criado: {p}")
    return novos

def _compile_one(full: Path) -> None:
    """Compila um único arquivo e mostra tail do console em caso de erro."""
    bin_dir = APPSERVER_BIN_DIR
    pid = os.getpid()
    fname = Path(full).name
    consolefile = f"/tmp/compile_{timestamp}_{pid}_{fname}.log"
    outpreproc = f"/tmp/preproc_{timestamp}_{pid}"

    cmd = (
        f'LD_LIBRARY_PATH="{bin_dir}" "{APPSERVER_BIN}" -compile '
        f'-files="{full}" '
        f'-includes="{INCLUDES_JOINED}" '
        f'-src="{REPO_PATH}" '
        f'-env=COMPILAR_PRD '
        f'-consolefile="{consolefile}" '
        f'-outpreproc="{outpreproc}"'
    )

    if not run_command(cmd, timeout=300, cwd=bin_dir):
        # tenta exibir o tail do consolefile para diagnóstico
        try:
            if Path(consolefile).is_file():
                logger.error(f"Tail do consolefile ({consolefile}):")
                with open(consolefile, "r", encoding="utf-8", errors="ignore") as fh:
                    lines = fh.readlines()[-20:]
                for ln in lines:
                    logger.error(ln.rstrip())
        except Exception:
            pass
        raise CompilationError(f"Falha ao compilar: {full.relative_to(REPO_PATH)}")

def compilar_arquivos(arquivos: List[str]) -> List[str]:
    """Compila e retorna a lista de arquivos compilados com sucesso (paths relativos ao repo)."""
    if not arquivos:
        logger.info("Nenhum arquivo para compilar")
        return []

    logger.info("Compilando arquivos...")

    if not Path(APPSERVER_BIN).is_file():
        raise CompilationError(f"Executável de compilação não encontrado: {APPSERVER_BIN}")
    if not os.access(APPSERVER_BIN, os.X_OK):
        raise CompilationError(f"Sem permissão de execução para: {APPSERVER_BIN}")

    compilados: List[str] = []

    for f in arquivos:
        full = Path(REPO_PATH) / f
        if not full.exists():
            logger.warning(f"Arquivo não encontrado: {full}")
            continue
        _compile_one(full)
        # usa o caminho "como veio" do Actions (string f), para aparecer igual no log
        compilados.append(f)

    logger.info("Compilação concluída")
    return compilados

def _swap_env_dir_once(path_value: str, ambiente: str) -> str:
    anchor = f"/apo/{ambiente}/"
    i = path_value.find(anchor)
    if i == -1:
        return path_value
    head = path_value[:i] + anchor
    tail = path_value[i + len(anchor):]
    if "/" in tail:
        tail = tail.split("/", 1)[1]  # remove eventual subpasta antiga
    else:
        tail = ""
    new_val = head + f"{timestamp}/" + tail.lstrip("/")
    while "//" in new_val:
        new_val = new_val.replace("//", "/")
    return new_val

def atualizar_inis(novos_dirs: Dict[str, str]) -> None:
    logger.info("Atualizando INIs...")
    keys = ("SourcePath=", "RPOCustom=")

    for app_dir in Path(BIN_PATH).iterdir():
        if not (app_dir.is_dir() and app_dir.name.startswith("appserver_")):
            continue

        ini_path = app_dir / "appserver.ini"
        if not ini_path.is_file():
            continue

        lines = ini_path.read_text().splitlines(keepends=False)
        changed = False

        for idx, line in enumerate(lines):
            stripped = line.lstrip()
            for key in keys:
                if stripped.startswith(key):
                    value = line.split("=", 1)[1].strip()
                    new_value = value
                    for ambiente in DIRS_RPO:
                        new_value = _swap_env_dir_once(new_value, ambiente)
                    if new_value != value:
                        prefix = line.split("=", 1)[0]
                        lines[idx] = f"{prefix}={new_value}"
                        changed = True
                    break

        if changed:
            ini_path.write_text("\n".join(lines) + "\n")
            logger.info(f"INI atualizado: {app_dir.name}")

    logger.info("INIs atualizados")

def copiar_rpos_para_pastas(novos_dirs: Dict[str, str]) -> None:
    logger.info("Copiando RPOs compilados...")
    src = Path(obter_rpo_compilado())
    for dir_name, dst_path in novos_dirs.items():
        dst_dir = Path(dst_path)
        for rpo in src.glob("*.rpo"):
            shutil.copy2(rpo, dst_dir / rpo.name)
            logger.info(f"Copiado {rpo.name} para {dir_name}")
    logger.info("RPOs copiados")

def validar_ambiente() -> None:
    logger.info("Validando ambiente...")
    time.sleep(10)
    if check_no_process("appserver"):
        raise ValidationError("AppServer não está rodando")
    logger.info("Ambiente validado")

# ==================== MAIN ====================
def main() -> bool:
    backup_dir: Optional[str] = None
    try:
        logger.info("=== INICIANDO DEPLOY DO PROTHEUS ===")
        logger.info(f"Timestamp: {timestamp}")

        verificar_prerequisitos()
        atualizar_repositorio()
        validar_servicos_ativos_antes_do_deploy()   # Aborta se ERP já estiver parado

        arquivos = identificar_arquivos_alterados()
        if not arquivos:
            logger.info("=== NENHUM ARQUIVO .PRW/.TLPP ALTERADO ===")
            logger.info("Deploy cancelado automaticamente")
            return True

        logger.info("=== PARANDO SERVIÇOS (timeout ampliado) ===")
        gerenciar_servicos("parar")

        backup_dir = backup_rpos_e_inis()
        novos = criar_pastas_timestamp()

        try:
            gerenciar_servicos("exclusivo")
        except DeployError as e:
            logger.warning(f"Modo exclusivo falhou: {e}. Seguindo o fluxo.")

        compilados = compilar_arquivos(arquivos)
        copiar_rpos_para_pastas(novos)
        atualizar_inis(novos)

        gerenciar_servicos("iniciar")
        validar_ambiente()

        logger.info("=== DEPLOY CONCLUÍDO COM SUCESSO! ===")
        return True

    except Exception as e:
        logger.error(f"=== ERRO NO DEPLOY: {e} ===")
        if backup_dir:
            backup_name = Path(backup_dir).name
            logger.error(f"Backup disponível: {backup_dir}")
            logger.error(f"Para rollback: python3.12 /totvs/scripts/rollback_protheus.py --backup {backup_name}")
        try:
            gerenciar_servicos("iniciar")
        except Exception:
            logger.error("Falha ao iniciar serviços após erro")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
