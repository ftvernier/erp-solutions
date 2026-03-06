# 🐘 PostgreSQL 16 — Setup Automatizado para ERP TOTVS Protheus

> Script shell interativo que instala, configura e otimiza o PostgreSQL 16 em Linux, seguindo rigorosamente as especificações de homologação da TOTVS.

---

## 🎯 O problema que este script resolve

Quem já trabalhou com Protheus sabe: configurar o PostgreSQL do jeito certo não é trivial. São encoding específico, tablespaces separados por ambiente, parâmetros de performance para perfil OLTP/ERP e uma série de detalhes que, se errados, comprometem performance e estabilidade.

Este script automatiza **todo esse processo**, do zero até o banco pronto para conectar no Application Server.

---

## ✅ Distribuições Homologadas (TOTVS)

| Sistema Operacional | Status |
|---|---|
| OpenSUSE Leap 15.4 | ✅ Suportado |
| RHEL 8.5 / 9.4 | ✅ Suportado |
| Oracle Linux 8.5 / 9.4 | ✅ Suportado |
| SUSE Linux Enterprise 15 SP4 | ✅ Suportado |

---

## ⚙️ O que o script faz

### 1. Detecção automática de ambiente
- Identifica a distribuição Linux e escolhe o repositório PGDG correto
- Lê hardware do servidor: RAM total, número de CPUs e tipo de storage (SSD/HDD)
- Exibe aviso caso a distro não esteja na lista de homologação TOTVS

### 2. Cálculo dinâmico de performance
Usando o perfil **OLTP / ERP or Long Transaction Applications** (referência: PGConfig), os parâmetros são calculados proporcionalmente ao hardware detectado:

| Parâmetro | Critério de cálculo |
|---|---|
| `shared_buffers` | 25% da RAM total |
| `effective_cache_size` | 75% da RAM total |
| `work_mem` | RAM / (max_connections × 4) |
| `maintenance_work_mem` | 5% da RAM (máx 2GB) |
| `random_page_cost` | 1.1 (SSD) ou 4.0 (HDD) |
| `effective_io_concurrency` | 200 (SSD) ou 2 (HDD) |
| `min_wal_size` / `max_wal_size` | 1GB / 3GB |
| `checkpoint_completion_target` | 0.9 |
| `wal_buffers` | 16MB |
| `listen_addresses` | `*` |
| `max_connections` | 100 (ajustável) |
| `autovacuum` | **on** (obrigatório TOTVS) |

### 3. Seleção interativa de ambientes
O script pergunta quais ambientes devem ser criados:

```
Criar ambiente de Produção (PRD)? [s/N]
Criar ambiente de Homologação (HML)? [s/N]
Criar ambiente de Desenvolvimento (DEV)? [s/N]
```

Para cada ambiente selecionado, são criados automaticamente:

```
/pgdata/
├── tpprd/
│   ├── data/     → tablespace tpprd_data
│   └── index/    → tablespace tpprd_index
├── tphml/
│   ├── data/     → tablespace tphml_data
│   └── index/    → tablespace tphml_index
└── tpdev/
    ├── data/     → tablespace tpdev_data
    └── index/    → tablespace tpdev_index
```

### 4. Banco de dados com configurações TOTVS
Cada banco é criado com as especificações exatas da documentação:

```sql
CREATE DATABASE tpprd
    OWNER tpprd
    TEMPLATE template0
    ENCODING 'WIN1252'
    LC_COLLATE 'C'
    LC_CTYPE 'C'
    TABLESPACE tpprd_data
    CONNECTION LIMIT -1;
```

### 5. Configuração do pg_hba.conf
Regras de acesso adicionadas automaticamente por ambiente, usando `scram-sha-256`.

### 6. Relatório final
Ao término, um relatório completo é gerado em `/tmp/protheus-pg-setup-report.txt` com todos os parâmetros aplicados, ambientes criados e senhas iniciais.

---

## 🚀 Como usar

```bash
# Clone o repositório
git clone https://github.com/ftvernier/erp-solutions.git
cd erp-solutions/postgres-setup

# Dê permissão de execução
chmod +x setup-postgres-protheus.sh

# Execute como root
sudo ./setup-postgres-protheus.sh
```

> ⚠️ **Requer execução como root ou via sudo.**

---

## 🔐 Segurança — Importante

As senhas iniciais geradas pelo script seguem o padrão `{usuario}@Protheus2024`.  
**Altere todas as senhas imediatamente após a instalação**, especialmente em ambientes de produção.

```bash
# Exemplo: alterar senha do usuário de produção
sudo -u postgres psql -c "ALTER ROLE tpprd WITH PASSWORD 'nova_senha_segura';"
```

---

## 📋 Pré-requisitos

- Acesso root ao servidor
- Conexão com a internet (para download do repositório PGDG)
- Disco com espaço suficiente em `/pgdata` para os tablespaces

---

## 📁 Estrutura do Repositório

```
postgres-setup/
├── setup-postgres-protheus.sh   # Script principal
└── README.md                    # Este arquivo
```

---

## 📚 Referências

- [TOTVS — Banco de Dados Homologados](https://tdn.totvs.com)
- [PostgreSQL PGDG — Repositórios oficiais](https://www.postgresql.org/download/linux/)
- [PGConfig — Calculadora de parâmetros PostgreSQL](https://www.pgconfig.org)

---

## 🤝 Contribuições

Encontrou algum problema ou quer adaptar para outra distribuição? Abra uma issue ou envie um PR.  
Este repositório é mantido com o objetivo de ajudar a comunidade Protheus com soluções práticas e de qualidade.

---

<p align="center">
  Feito com 💙 por <a href="https://github.com/ftvernier">Fernando Vernier</a><br>
  <a href="https://github.com/ftvernier/erp-solutions">github.com/ftvernier/erp-solutions</a>
</p>
