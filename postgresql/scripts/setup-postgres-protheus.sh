#!/bin/bash
# =============================================================================
#  setup-postgres-protheus.sh
#  Instalação e configuração do PostgreSQL 16 para ERP TOTVS Protheus
#  Compatível com: OpenSUSE Leap 15.4 | RHEL 8.5/9.4 | SUSE Linux Enterprise 15 SP4
#
#  Autor: Fernando Vernier — github.com/ftvernier/erp-solutions
#  Referência: Documentação oficial TOTVS — Banco de Dados Homologados
# =============================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# CORES E FORMATAÇÃO
# ------------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ------------------------------------------------------------------------------
# CONSTANTES
# ------------------------------------------------------------------------------
PG_VERSION="16"
PG_DATA_ROOT="/pgdata"
PG_SERVICE="postgresql-${PG_VERSION}"
REPORT_FILE="/tmp/protheus-pg-setup-report.txt"

# Ambientes disponíveis
declare -A ENV_NAMES=( [prd]="Produção" [hml]="Homologação" [dev]="Desenvolvimento" )
declare -A ENV_USERS=( [prd]="tpprd" [hml]="tphml" [dev]="tpdev" )
SELECTED_ENVS=()

# ------------------------------------------------------------------------------
# FUNÇÕES DE LOG
# ------------------------------------------------------------------------------
log_info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[AVISO]${NC} $*"; }
log_error()   { echo -e "${RED}[ERRO]${NC}  $*" >&2; }
log_section() { echo -e "\n${BOLD}${BLUE}━━━  $*  ━━━${NC}\n"; }
log_report()  { echo "$*" | tee -a "$REPORT_FILE"; }

# ------------------------------------------------------------------------------
# VERIFICAÇÕES INICIAIS
# ------------------------------------------------------------------------------
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script deve ser executado como root (ou via sudo)."
        exit 1
    fi
}

detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO_ID="${ID,,}"
        DISTRO_VERSION="${VERSION_ID:-}"
        DISTRO_NAME="${NAME:-}"
    else
        log_error "Não foi possível detectar a distribuição Linux."
        exit 1
    fi

    case "$DISTRO_ID" in
        opensuse-leap|opensuse*)
            DISTRO_FAMILY="suse"
            ;;
        rhel|centos|almalinux|rocky|ol)
            DISTRO_FAMILY="rhel"
            ;;
        sles|suse)
            DISTRO_FAMILY="suse"
            ;;
        *)
            log_warn "Distribuição '${DISTRO_NAME}' não está na lista de homologação TOTVS."
            log_warn "SOs homologados: OpenSUSE Leap 15.4 | RHEL 8.5/9.4 | SUSE Linux Enterprise 15 SP4"
            read -rp "Deseja continuar mesmo assim? [s/N]: " CONTINUE
            [[ "${CONTINUE,,}" == "s" ]] || exit 0
            DISTRO_FAMILY="rhel"  # fallback para RHEL-like
            ;;
    esac

    log_ok "Distribuição detectada: ${DISTRO_NAME} ${DISTRO_VERSION} (família: ${DISTRO_FAMILY})"
}

# ------------------------------------------------------------------------------
# BANNER
# ------------------------------------------------------------------------------
print_banner() {
    clear
    echo -e "${BOLD}${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║       PostgreSQL ${PG_VERSION} — Setup para ERP TOTVS Protheus          ║"
    echo "║       github.com/ftvernier/erp-solutions                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e " ${YELLOW}Referência:${NC} Documentação oficial TOTVS — Banco de Dados Homologados"
    echo -e " ${YELLOW}Encoding:${NC}  WIN1252  |  ${YELLOW}Collation:${NC} C  |  ${YELLOW}Character type:${NC} C"
    echo ""
}

# ------------------------------------------------------------------------------
# LEITURA DO HARDWARE
# ------------------------------------------------------------------------------
detect_hardware() {
    log_section "Detecção de Hardware"

    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_GB=$(( TOTAL_RAM_KB / 1024 / 1024 ))
    CPU_COUNT=$(nproc)
    STORAGE_TYPE="ssd"  # default assumido; pode ser ajustado

    # Tenta detectar se o disco principal é SSD
    ROOT_DEVICE=$(df / | tail -1 | awk '{print $1}' | sed 's|/dev/||;s|[0-9]*$||;s|p[0-9]*$||')
    if [[ -f "/sys/block/${ROOT_DEVICE}/queue/rotational" ]]; then
        ROT=$(cat "/sys/block/${ROOT_DEVICE}/queue/rotational")
        [[ "$ROT" == "0" ]] && STORAGE_TYPE="ssd" || STORAGE_TYPE="hdd"
    fi

    log_info "RAM total detectada : ${TOTAL_RAM_GB} GB"
    log_info "CPUs detectadas     : ${CPU_COUNT} vCPUs"
    log_info "Tipo de storage     : ${STORAGE_TYPE^^}"

    if [[ $TOTAL_RAM_GB -lt 4 ]]; then
        log_warn "A TOTVS recomenda no mínimo 16 GB de RAM para ambientes de produção."
        log_warn "O servidor possui apenas ${TOTAL_RAM_GB} GB — os parâmetros serão ajustados proporcionalmente."
    fi
}

# ------------------------------------------------------------------------------
# CÁLCULO DINÂMICO DOS PARÂMETROS (baseado no perfil OLTP / PGConfig)
# Application Profile: ERP or Long Transaction Applications
# ------------------------------------------------------------------------------
calculate_pg_params() {
    log_section "Calculando Parâmetros de Performance (perfil OLTP/ERP)"

    local ram_mb=$(( TOTAL_RAM_KB / 1024 ))

    # shared_buffers: 25% da RAM (mínimo 128MB)
    PARAM_SHARED_BUFFERS=$(( ram_mb / 4 ))
    [[ $PARAM_SHARED_BUFFERS -lt 128 ]] && PARAM_SHARED_BUFFERS=128

    # effective_cache_size: 75% da RAM
    PARAM_EFFECTIVE_CACHE=$(( ram_mb * 3 / 4 ))

    # work_mem: RAM / (max_connections * 4) — conservador para ERP
    PARAM_MAX_CONNECTIONS=100
    PARAM_WORK_MEM=$(( ram_mb / (PARAM_MAX_CONNECTIONS * 4) ))
    [[ $PARAM_WORK_MEM -lt 4 ]] && PARAM_WORK_MEM=4

    # maintenance_work_mem: 5% da RAM (máx 2048MB)
    PARAM_MAINTENANCE_WORK_MEM=$(( ram_mb / 20 ))
    [[ $PARAM_MAINTENANCE_WORK_MEM -gt 2048 ]] && PARAM_MAINTENANCE_WORK_MEM=2048
    [[ $PARAM_MAINTENANCE_WORK_MEM -lt 64 ]] && PARAM_MAINTENANCE_WORK_MEM=64

    # WAL
    PARAM_MIN_WAL_SIZE="1GB"
    PARAM_MAX_WAL_SIZE="3GB"
    PARAM_WAL_BUFFERS="16MB"
    PARAM_CHECKPOINT_TARGET="0.9"

    # Network
    PARAM_LISTEN_ADDRESSES="*"

    # Storage — SSD: random_page_cost=1.1, effective_io_concurrency=200
    if [[ "$STORAGE_TYPE" == "ssd" ]]; then
        PARAM_RANDOM_PAGE_COST="1.1"
        PARAM_IO_CONCURRENCY="200"
    else
        PARAM_RANDOM_PAGE_COST="4.0"
        PARAM_IO_CONCURRENCY="2"
    fi

    # Autovacuum: obrigatoriamente ON (exigência TOTVS)
    PARAM_AUTOVACUUM="on"

    log_info "shared_buffers              = ${PARAM_SHARED_BUFFERS}MB"
    log_info "effective_cache_size        = ${PARAM_EFFECTIVE_CACHE}MB"
    log_info "work_mem                    = ${PARAM_WORK_MEM}MB"
    log_info "maintenance_work_mem        = ${PARAM_MAINTENANCE_WORK_MEM}MB"
    log_info "max_connections             = ${PARAM_MAX_CONNECTIONS}"
    log_info "min_wal_size                = ${PARAM_MIN_WAL_SIZE}"
    log_info "max_wal_size                = ${PARAM_MAX_WAL_SIZE}"
    log_info "wal_buffers                 = ${PARAM_WAL_BUFFERS}"
    log_info "checkpoint_completion_target= ${PARAM_CHECKPOINT_TARGET}"
    log_info "listen_addresses            = '${PARAM_LISTEN_ADDRESSES}'"
    log_info "random_page_cost            = ${PARAM_RANDOM_PAGE_COST}"
    log_info "effective_io_concurrency    = ${PARAM_IO_CONCURRENCY}"
    log_info "autovacuum                  = ${PARAM_AUTOVACUUM} (obrigatório TOTVS)"
}

# ------------------------------------------------------------------------------
# SELEÇÃO INTERATIVA DE AMBIENTES
# ------------------------------------------------------------------------------
select_environments() {
    log_section "Seleção de Ambientes"

    echo -e "Quais ambientes deseja criar? (pressione ${BOLD}ENTER${NC} para confirmar cada opção)\n"

    for env in prd hml dev; do
        read -rp "  Criar ambiente de ${ENV_NAMES[$env]} (${env^^}) [s/N]? " RESP
        if [[ "${RESP,,}" == "s" ]]; then
            SELECTED_ENVS+=("$env")
            log_ok "Ambiente ${ENV_NAMES[$env]} selecionado."
        fi
    done

    if [[ ${#SELECTED_ENVS[@]} -eq 0 ]]; then
        log_error "Nenhum ambiente selecionado. Encerrando."
        exit 1
    fi

    echo ""
    log_info "Ambientes que serão criados: ${SELECTED_ENVS[*]}"
}

# ------------------------------------------------------------------------------
# INSTALAÇÃO DO POSTGRESQL 16
# ------------------------------------------------------------------------------
install_postgresql() {
    log_section "Instalação do PostgreSQL ${PG_VERSION}"

    case "$DISTRO_FAMILY" in
        suse)
            log_info "Adicionando repositório PGDG para SUSE/OpenSUSE..."
            REPO_URL="https://download.postgresql.org/pub/repos/zypp/repo/pgdg-sles-${PG_VERSION}-x86_64.repo"

            if ! zypper lr | grep -q "pgdg"; then
                zypper addrepo "$REPO_URL" || {
                    log_warn "Falha ao adicionar repo PGDG. Tentando via zypper install direto..."
                }
            fi

            zypper --non-interactive refresh
            zypper --non-interactive install -y \
                "postgresql${PG_VERSION}" \
                "postgresql${PG_VERSION}-server" \
                "postgresql${PG_VERSION}-contrib"
            ;;
        rhel)
            log_info "Adicionando repositório PGDG para RHEL/Oracle Linux..."
            MAJOR_VER="${DISTRO_VERSION%%.*}"

            if ! rpm -q "pgdg-redhat-repo" &>/dev/null; then
                dnf install -y \
                    "https://download.postgresql.org/pub/repos/yum/reporpms/EL-${MAJOR_VER}-x86_64/pgdg-redhat-repo-latest.noarch.rpm"
            fi

            # Desabilita o módulo postgresql do AppStream (RHEL 8+)
            if [[ "$MAJOR_VER" -ge 8 ]]; then
                dnf -qy module disable postgresql 2>/dev/null || true
            fi

            dnf install -y \
                "postgresql${PG_VERSION}" \
                "postgresql${PG_VERSION}-server" \
                "postgresql${PG_VERSION}-contrib"
            ;;
    esac

    PG_BIN="/usr/pgsql-${PG_VERSION}/bin"
    log_ok "PostgreSQL ${PG_VERSION} instalado com sucesso."
}

# ------------------------------------------------------------------------------
# INICIALIZAÇÃO DO CLUSTER
# ------------------------------------------------------------------------------
init_cluster() {
    log_section "Inicialização do Cluster"

    log_info "Executando initdb (padrão TOTVS)..."
    "${PG_BIN}/postgresql-${PG_VERSION}-setup" initdb

    log_info "Habilitando serviço no systemd..."
    systemctl enable "${PG_SERVICE}"

    log_info "Iniciando o serviço PostgreSQL..."
    systemctl start "${PG_SERVICE}"

    systemctl is-active --quiet "${PG_SERVICE}" && \
        log_ok "Serviço ${PG_SERVICE} está ativo e rodando." || \
        { log_error "Falha ao iniciar o serviço ${PG_SERVICE}."; exit 1; }
}

# ------------------------------------------------------------------------------
# APLICAÇÃO DOS PARÂMETROS DE PERFORMANCE
# ------------------------------------------------------------------------------
apply_performance_params() {
    log_section "Aplicando Parâmetros de Performance"

    run_sql() {
        su - postgres -c "psql -c \"$1\""
    }

    run_sql "ALTER SYSTEM SET shared_buffers = '${PARAM_SHARED_BUFFERS}MB';"
    run_sql "ALTER SYSTEM SET effective_cache_size = '${PARAM_EFFECTIVE_CACHE}MB';"
    run_sql "ALTER SYSTEM SET work_mem = '${PARAM_WORK_MEM}MB';"
    run_sql "ALTER SYSTEM SET maintenance_work_mem = '${PARAM_MAINTENANCE_WORK_MEM}MB';"
    run_sql "ALTER SYSTEM SET min_wal_size = '${PARAM_MIN_WAL_SIZE}';"
    run_sql "ALTER SYSTEM SET max_wal_size = '${PARAM_MAX_WAL_SIZE}';"
    run_sql "ALTER SYSTEM SET wal_buffers = '${PARAM_WAL_BUFFERS}';"
    run_sql "ALTER SYSTEM SET checkpoint_completion_target = ${PARAM_CHECKPOINT_TARGET};"
    run_sql "ALTER SYSTEM SET listen_addresses = '${PARAM_LISTEN_ADDRESSES}';"
    run_sql "ALTER SYSTEM SET max_connections = ${PARAM_MAX_CONNECTIONS};"
    run_sql "ALTER SYSTEM SET random_page_cost = ${PARAM_RANDOM_PAGE_COST};"
    run_sql "ALTER SYSTEM SET effective_io_concurrency = ${PARAM_IO_CONCURRENCY};"
    run_sql "ALTER SYSTEM SET autovacuum = '${PARAM_AUTOVACUUM}';"

    log_info "Reiniciando o serviço para aplicar todos os parâmetros..."
    systemctl restart "${PG_SERVICE}"

    log_ok "Parâmetros de performance aplicados com sucesso."
}

# ------------------------------------------------------------------------------
# CRIAÇÃO DE ESTRUTURA DE DIRETÓRIOS, USUÁRIOS, TABLESPACES E BANCOS
# ------------------------------------------------------------------------------
create_environments() {
    log_section "Criação dos Ambientes Protheus"

    run_psql() { su - postgres -c "psql $*"; }
    run_psql_c() { su - postgres -c "psql -c \"$1\""; }

    mkdir -p "$PG_DATA_ROOT"
    chown postgres:postgres "$PG_DATA_ROOT"

    for env in "${SELECTED_ENVS[@]}"; do
        local user="${ENV_USERS[$env]}"
        local env_name="${ENV_NAMES[$env]}"
        local data_dir="${PG_DATA_ROOT}/${user}/data"
        local idx_dir="${PG_DATA_ROOT}/${user}/index"
        local ts_data="${user}_data"
        local ts_idx="${user}_index"
        local db_name="${user}"

        log_info "── Configurando ambiente: ${env_name^^} (${user}) ──"

        # Diretórios
        log_info "  Criando diretórios de datafiles..."
        su - postgres -c "mkdir -p '${data_dir}' '${idx_dir}'"
        log_ok "  Diretórios criados: ${data_dir} | ${idx_dir}"

        # Role/usuário
        log_info "  Criando role '${user}'..."
        run_psql_c "DO \$\$ BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${user}') THEN
                CREATE ROLE ${user} WITH LOGIN PASSWORD '${user}@Protheus2024' NOSUPERUSER NOCREATEDB NOCREATEROLE;
            END IF;
        END \$\$;"
        log_ok "  Role '${user}' criada."

        # Tablespaces
        log_info "  Criando tablespaces..."
        run_psql_c "DO \$\$ BEGIN
            IF NOT EXISTS (SELECT FROM pg_tablespace WHERE spcname = '${ts_data}') THEN
                CREATE TABLESPACE ${ts_data} OWNER ${user} LOCATION '${data_dir}';
            END IF;
        END \$\$;"
        run_psql_c "DO \$\$ BEGIN
            IF NOT EXISTS (SELECT FROM pg_tablespace WHERE spcname = '${ts_idx}') THEN
                CREATE TABLESPACE ${ts_idx} OWNER ${user} LOCATION '${idx_dir}';
            END IF;
        END \$\$;"
        log_ok "  Tablespaces criados: ${ts_data} | ${ts_idx}"

        # Banco de dados
        log_info "  Criando banco de dados '${db_name}'..."
        if ! su - postgres -c "psql -lqt" | cut -d'|' -f1 | grep -qw "${db_name}"; then
            run_psql_c "CREATE DATABASE ${db_name}
                OWNER ${user}
                TEMPLATE template0
                ENCODING 'WIN1252'
                LC_COLLATE 'C'
                LC_CTYPE 'C'
                TABLESPACE ${ts_data}
                CONNECTION LIMIT -1;"
            log_ok "  Banco '${db_name}' criado com encoding WIN1252, Collation C, Character type C."
        else
            log_warn "  Banco '${db_name}' já existe. Pulando criação."
        fi

        # Permissões
        run_psql_c "GRANT ALL PRIVILEGES ON DATABASE ${db_name} TO ${user};"
        run_psql_c "ALTER DATABASE ${db_name} SET default_tablespace = '${ts_data}';"

        log_ok "  Ambiente ${env_name} configurado com sucesso!\n"
    done
}

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DO pg_hba.conf
# ------------------------------------------------------------------------------
configure_hba() {
    log_section "Configuração do pg_hba.conf"

    PG_DATA_DIR=$(su - postgres -c "psql -t -c 'SHOW data_directory;'" | xargs)
    HBA_FILE="${PG_DATA_DIR}/pg_hba.conf"

    log_info "Arquivo pg_hba.conf localizado em: ${HBA_FILE}"

    # Backup
    cp "${HBA_FILE}" "${HBA_FILE}.bak.$(date +%Y%m%d%H%M%S)"
    log_ok "Backup do pg_hba.conf criado."

    # Adiciona regras para cada ambiente criado
    for env in "${SELECTED_ENVS[@]}"; do
        local user="${ENV_USERS[$env]}"
        if ! grep -q "^host.*${user}.*${user}" "${HBA_FILE}"; then
            echo "# Protheus - Ambiente ${ENV_NAMES[$env]}" >> "${HBA_FILE}"
            echo "host    ${user}    ${user}    0.0.0.0/0    scram-sha-256" >> "${HBA_FILE}"
        fi
    done

    systemctl reload "${PG_SERVICE}" 2>/dev/null || systemctl restart "${PG_SERVICE}"
    log_ok "pg_hba.conf atualizado e serviço recarregado."
}

# ------------------------------------------------------------------------------
# RELATÓRIO FINAL
# ------------------------------------------------------------------------------
generate_report() {
    log_section "Relatório Final da Instalação"

    : > "$REPORT_FILE"

    {
        echo "════════════════════════════════════════════════════════════"
        echo " PostgreSQL ${PG_VERSION} — Setup Protheus — Relatório"
        echo " $(date '+%d/%m/%Y %H:%M:%S')"
        echo "════════════════════════════════════════════════════════════"
        echo ""
        echo "SISTEMA"
        echo "  Distribuição : ${DISTRO_NAME} ${DISTRO_VERSION}"
        echo "  RAM Total    : ${TOTAL_RAM_GB} GB"
        echo "  CPUs         : ${CPU_COUNT}"
        echo "  Storage      : ${STORAGE_TYPE^^}"
        echo ""
        echo "POSTGRESQL"
        echo "  Versão       : ${PG_VERSION}"
        echo "  Serviço      : ${PG_SERVICE} (systemd, autostart habilitado)"
        echo ""
        echo "PARÂMETROS DE PERFORMANCE (perfil OLTP/ERP)"
        echo "  shared_buffers              = ${PARAM_SHARED_BUFFERS}MB"
        echo "  effective_cache_size        = ${PARAM_EFFECTIVE_CACHE}MB"
        echo "  work_mem                    = ${PARAM_WORK_MEM}MB"
        echo "  maintenance_work_mem        = ${PARAM_MAINTENANCE_WORK_MEM}MB"
        echo "  max_connections             = ${PARAM_MAX_CONNECTIONS}"
        echo "  min_wal_size                = ${PARAM_MIN_WAL_SIZE}"
        echo "  max_wal_size                = ${PARAM_MAX_WAL_SIZE}"
        echo "  wal_buffers                 = ${PARAM_WAL_BUFFERS}"
        echo "  checkpoint_completion_target= ${PARAM_CHECKPOINT_TARGET}"
        echo "  listen_addresses            = '${PARAM_LISTEN_ADDRESSES}'"
        echo "  random_page_cost            = ${PARAM_RANDOM_PAGE_COST}"
        echo "  effective_io_concurrency    = ${PARAM_IO_CONCURRENCY}"
        echo "  autovacuum                  = ${PARAM_AUTOVACUUM}"
        echo ""
        echo "AMBIENTES CRIADOS"
        for env in "${SELECTED_ENVS[@]}"; do
            local user="${ENV_USERS[$env]}"
            echo "  [${ENV_NAMES[$env]^^}]"
            echo "    Role         : ${user}"
            echo "    Banco        : ${user}"
            echo "    Tablespace   : ${user}_data | ${user}_index"
            echo "    Diretórios   : ${PG_DATA_ROOT}/${user}/data | ${PG_DATA_ROOT}/${user}/index"
            echo "    Encoding     : WIN1252 | Collation: C | Character type: C"
            echo "    Senha inicial: ${user}@Protheus2024  ← ALTERE IMEDIATAMENTE"
            echo ""
        done
        echo "IMPORTANTE"
        echo "  - Altere as senhas dos usuários em produção imediatamente"
        echo "  - Ajuste max_connections conforme necessário (mínimo 2x usuários do ERP)"
        echo "  - Verifique /var/lib/pgsql/${PG_VERSION}/data/postgresql.auto.conf"
        echo "  - Referência: docs.totvs.com — Banco de Dados Homologados"
        echo ""
        echo "  github.com/ftvernier/erp-solutions"
        echo "════════════════════════════════════════════════════════════"
    } | tee "$REPORT_FILE"

    echo ""
    log_ok "Relatório salvo em: ${REPORT_FILE}"
}

# ------------------------------------------------------------------------------
# CONFIRMAÇÃO ANTES DE EXECUTAR
# ------------------------------------------------------------------------------
confirm_execution() {
    echo -e "\n${YELLOW}${BOLD}ATENÇÃO:${NC} Este script irá:"
    echo "  • Instalar o PostgreSQL ${PG_VERSION} via repositório PGDG oficial"
    echo "  • Inicializar o cluster e configurar o systemd"
    echo "  • Aplicar parâmetros de performance calculados para este servidor"
    echo "  • Criar estruturas de banco para os ambientes selecionados"
    echo ""
    read -rp "Confirma a execução? [s/N]: " CONFIRM
    [[ "${CONFIRM,,}" == "s" ]] || { log_info "Execução cancelada pelo usuário."; exit 0; }
}

# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------
main() {
    print_banner
    check_root
    detect_distro
    detect_hardware
    calculate_pg_params
    select_environments
    confirm_execution

    install_postgresql
    init_cluster
    apply_performance_params
    create_environments
    configure_hba
    generate_report

    echo ""
    echo -e "${GREEN}${BOLD}✔  Instalação concluída com sucesso!${NC}"
    echo -e "   Consulte o relatório em: ${REPORT_FILE}"
    echo ""
}

main "$@"
