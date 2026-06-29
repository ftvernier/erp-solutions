# 🦙 Usando PO-UI Protheus Angular com Ollama no VS Code

> Guia para configurar o `CLAUDE.md` / `AGENTS.md` com modelos locais via **Ollama** no VS Code,
> sem depender de nenhuma API externa paga.

---

## Por que um guia separado para Ollama?

O `CLAUDE.md` principal deste repositório prioriza o **MCP oficial do PO-UI** (`@po-ui/mcp`) como fonte de documentação, com `web_fetch` como fallback. Nenhum dos dois funciona com modelos locais via Ollama — eles não têm acesso à rede por padrão.

Este guia troca essa camada por uma alternativa **100% offline**: a documentação do PO-UI baixada localmente e referenciada por arquivo. O restante do `CLAUDE.md` (arquitetura, NgModules, SubSink, ProtheusLibCore, contrato de API, etc.) permanece **idêntico** — essas regras não dependem de acesso à internet.

---

## Pré-requisitos

- [Ollama](https://ollama.com) instalado e rodando localmente
- VS Code instalado
- Projeto Angular com PO-UI na raiz

---

## Passo 1 — Instalar o Ollama e baixar um modelo

```bash
# Instale o Ollama (Linux/macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Modelos recomendados para geração de código Angular/TypeScript
ollama pull qwen2.5-coder:7b     # melhor custo/benefício para código
ollama pull deepseek-coder-v2     # excelente para TypeScript, contexto maior
ollama pull codellama:13b         # boa alternativa
ollama pull llama3.1:8b           # bom para raciocínio geral + código
```

| Modelo | Tamanho | TypeScript | Contexto | Velocidade |
|---|---|---|---|---|
| `qwen2.5-coder:7b` | ~4GB | ⭐⭐⭐⭐⭐ | 32k | ⭐⭐⭐⭐ |
| `deepseek-coder-v2` | ~9GB | ⭐⭐⭐⭐⭐ | 128k | ⭐⭐⭐ |
| `codellama:13b` | ~7GB | ⭐⭐⭐⭐ | 16k | ⭐⭐⭐ |
| `llama3.1:8b` | ~5GB | ⭐⭐⭐ | 128k | ⭐⭐⭐⭐ |
| `mistral:7b` | ~4GB | ⭐⭐⭐ | 32k | ⭐⭐⭐⭐ |

> **Recomendação:** para projetos Angular com PO-UI, `qwen2.5-coder:7b` ou `deepseek-coder-v2` apresentam os melhores resultados com TypeScript e código estruturado.

---

## Passo 2 — Instalar a extensão Continue.dev no VS Code

O **Continue.dev** é a extensão que conecta o Ollama ao VS Code e lê arquivos de contexto do repositório (incluindo `CLAUDE.md`) através de referências manuais com `@`.

```bash
code --install-extension Continue.continue
```

Ou pela interface: Extensions (`Ctrl+Shift+X`) → busque **Continue** → instale **Continue - Codestral, Claude, and more**.

---

## Passo 3 — Configurar o Continue.dev com Ollama

Edite `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "Qwen2.5 Coder (PO-UI Protheus)",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b",
      "contextLength": 32768
    },
    {
      "title": "DeepSeek Coder V2",
      "provider": "ollama",
      "model": "deepseek-coder-v2",
      "contextLength": 32768
    }
  ],
  "contextProviders": [
    { "name": "file" },
    { "name": "directory" },
    { "name": "currentFile" },
    { "name": "open" }
  ],
  "slashCommands": [
    { "name": "edit", "description": "Editar código selecionado" },
    { "name": "comment", "description": "Comentar código selecionado" }
  ]
}
```

---

## Passo 4 — Baixar a documentação PO-UI localmente

O PO-UI disponibiliza um arquivo único com toda a documentação:

```bash
# Na raiz do seu projeto Angular
curl -o po-ui-docs.txt https://po-ui.io/llms-full.txt
```

Adicione ao `.gitignore` (o arquivo pode ter vários MB e fica desatualizado rápido):

```bash
echo "po-ui-docs.txt" >> .gitignore
```

> **Atualize periodicamente**, sempre que o PO-UI lançar uma nova versão:
> ```bash
> curl -o po-ui-docs.txt https://po-ui.io/llms-full.txt
> ```

---

## Passo 5 — Adaptar a seção de documentação no CLAUDE.md

Copie o `CLAUDE.md` deste repositório para a raiz do seu projeto e **substitua o Passo 1** (que referencia o MCP/`web_fetch`) por esta versão offline:

```markdown
## Passo 1 — Documentação PO-UI (modo offline / Ollama)

A documentação completa do PO-UI está disponível no arquivo `po-ui-docs.txt`
na raiz deste projeto (baixado de https://po-ui.io/llms-full.txt).

Antes de implementar qualquer componente PO-UI, consulte este arquivo para
verificar inputs, outputs, eventos e interfaces corretos do componente.

Exemplos de consulta:
- Para po-table: busque "PoTableComponent" ou "po-table" no arquivo
- Para po-dynamic-form: busque "PoDynamicFormComponent"
- Para po-modal: busque "PoModalComponent"
- Para interfaces: busque "PoTableColumn", "PoDynamicFormField", etc.
```

O restante do arquivo (Passo 2 em diante — arquitetura, contrato de API, grid system, `po-chart`) permanece **idêntico**.

---

## Passo 6 — Usar no dia a dia com Continue.dev

Com tudo configurado, abra o painel do Continue (`Ctrl+L`) e referencie os arquivos com `@`:

```
@po-ui-docs.txt Crie uma tela de listagem de pedidos com po-page-list e po-table,
seguindo os padrões do CLAUDE.md
```

```
@CLAUDE.md @po-ui-docs.txt Implemente o formulário de cadastro de fornecedores
com po-dynamic-form e campos: código, nome, CNPJ e tipo
```

```
@currentFile Revise este componente e corrija qualquer violação dos padrões
definidos no CLAUDE.md
```

> Combine `@CLAUDE.md` + `@po-ui-docs.txt` para melhores resultados — o primeiro define como escrever, o segundo define o que existe na biblioteca.

---

## Estrutura final do projeto

```
seu-projeto-angular/
├── CLAUDE.md          ← padrões de arquitetura (Claude Code) — Passo 1 adaptado para offline
├── AGENTS.md          ← padrões de arquitetura (Codex) — mesma adaptação
├── po-ui-docs.txt     ← documentação PO-UI offline (não versionar)
├── .gitignore         ← incluir po-ui-docs.txt
├── package.json
└── src/
```

---

## Comparativo de extensões VS Code com Ollama

| Extensão | Lê CLAUDE.md | Contexto de arquivos | Ollama | Gratuito |
|---|---|---|---|---|
| **Continue.dev** | ✅ via `@file` | ✅ | ✅ nativo | ✅ |
| **Twinny** | ⚠️ manual | ✅ | ✅ nativo | ✅ |
| **Codeium** | ❌ | ⚠️ parcial | ❌ | ✅ plano free |
| **Copilot** | ⚠️ `.github/copilot-instructions.md` | ✅ | ❌ | ❌ pago |

> **Recomendação:** Continue.dev é a opção com melhor integração Ollama + contexto de arquivos.

---

## Dicas para melhores resultados com modelos locais

**Seja específico na tarefa:**
```
# ✅ Bom
Crie o arquivo natureza.service.ts seguindo o padrão do CLAUDE.md,
com os métodos listar(), buscar(id), criar() e excluir()

# ❌ Vago
Crie um service
```

**Referencie sempre o contexto:**
```
@CLAUDE.md @po-ui-docs.txt @currentFile
```

**Divida tarefas grandes** — em vez de pedir o CRUD completo de uma vez, peça por arquivo:
1. Primeiro o model (`natureza.model.ts`)
2. Depois o service (`natureza.service.ts`)
3. Depois o module (`natureza.module.ts`)
4. Depois list e form separados

**Valide com tsc após gerar:**
```bash
npx tsc --noEmit
```

---

## Referências

- [Ollama](https://ollama.com)
- [Continue.dev](https://continue.dev)
- [PO-UI llms-full.txt](https://po-ui.io/llms-full.txt)
- [Repositório erp-solutions](https://github.com/ftvernier/erp-solutions)

---

Feito por [Fernando Vernier](https://www.linkedin.com/in/ftvernier/) • [@ftvernier/erp-solutions](https://github.com/ftvernier/erp-solutions)
