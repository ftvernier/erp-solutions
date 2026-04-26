# 🦙 Usando PO-UI Protheus Angular com Ollama no VS Code

> Guia para configurar o `CLAUDE.md` / `AGENTS.md` com modelos locais via **Ollama** no VS Code,
> sem depender de nenhuma API externa paga.

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
ollama pull codellama:13b         # boa alternativa
ollama pull llama3.1:8b           # bom para raciocínio geral + código
ollama pull deepseek-coder-v2     # excelente para TypeScript
```

> **Recomendação:** Para projetos Angular com PO-UI, `qwen2.5-coder:7b` ou `deepseek-coder-v2`
> apresentam os melhores resultados com TypeScript e código estruturado.

---

## Passo 2 — Instalar a extensão Continue.dev no VS Code

O **Continue.dev** é a extensão que conecta o Ollama ao VS Code e lê arquivos de contexto
do repositório automaticamente.

1. Abra o VS Code
2. Vá em Extensions (`Ctrl+Shift+X`)
3. Busque por **Continue**
4. Instale a extensão oficial **Continue - Codestral, Claude, and more**

Ou instale via terminal:
```bash
code --install-extension Continue.continue
```

---

## Passo 3 — Configurar o Continue.dev com Ollama

Abra o arquivo de configuração do Continue (`~/.continue/config.json`) e adicione:

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
    {
      "name": "edit",
      "description": "Editar código selecionado"
    },
    {
      "name": "comment",
      "description": "Comentar código selecionado"
    }
  ]
}
```

---

## Passo 4 — Baixar a documentação PO-UI localmente

Como modelos Ollama rodam offline, é necessário baixar a documentação do PO-UI
para dentro do projeto. O PO-UI disponibiliza um arquivo único com toda a documentação:

```bash
# Na raiz do seu projeto Angular
curl -o po-ui-docs.txt https://po-ui.io/llms-full.txt
```

Adicione ao `.gitignore` para não versionar (o arquivo pode ter vários MB):

```bash
echo "po-ui-docs.txt" >> .gitignore
```

> **Atualize periodicamente** quando o PO-UI lançar novas versões:
> ```bash
> curl -o po-ui-docs.txt https://po-ui.io/llms-full.txt
> ```

---

## Passo 5 — Copiar o CLAUDE.md adaptado para Ollama

Copie o arquivo `CLAUDE.md` deste repositório para a raiz do seu projeto e **substitua
a seção de documentação** pela versão offline:

```markdown
## Documentação PO-UI

A documentação completa do PO-UI está disponível no arquivo `po-ui-docs.txt`
na raiz deste projeto.

Antes de implementar qualquer componente PO-UI, consulte este arquivo para
verificar os inputs, outputs, eventos e interfaces corretos do componente.

Exemplos de consulta:
- Para po-table: busque "PoTableComponent" ou "po-table" no arquivo
- Para po-dynamic-form: busque "PoDynamicFormComponent"
- Para po-modal: busque "PoModalComponent"
- Para interfaces: busque "PoTableColumn", "PoDynamicFormField", etc.
```

O restante do `CLAUDE.md` (regras de arquitetura, NgModules, SubSink, ProtheusLibCore, etc.)
permanece **idêntico** — essas regras funcionam com qualquer agente.

---

## Passo 6 — Usar no dia a dia com Continue.dev

Com tudo configurado, abra o painel do Continue (`Ctrl+L`) e use normalmente:

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

> O `@` no Continue.dev permite referenciar arquivos específicos como contexto
> para o modelo. Combine `@CLAUDE.md` + `@po-ui-docs.txt` para melhores resultados.

---

## Estrutura final do projeto

```
seu-projeto-angular/
├── CLAUDE.md          ← padrões de arquitetura (Claude Code)
├── AGENTS.md          ← padrões de arquitetura (Codex)
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

## Modelos testados para Angular/TypeScript

| Modelo | Tamanho | TypeScript | Contexto | Velocidade |
|---|---|---|---|---|
| `qwen2.5-coder:7b` | ~4GB | ⭐⭐⭐⭐⭐ | 32k | ⭐⭐⭐⭐ |
| `deepseek-coder-v2` | ~9GB | ⭐⭐⭐⭐⭐ | 128k | ⭐⭐⭐ |
| `codellama:13b` | ~7GB | ⭐⭐⭐⭐ | 16k | ⭐⭐⭐ |
| `llama3.1:8b` | ~5GB | ⭐⭐⭐ | 128k | ⭐⭐⭐⭐ |
| `mistral:7b` | ~4GB | ⭐⭐⭐ | 32k | ⭐⭐⭐⭐ |

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

**Divida tarefas grandes:**
Em vez de pedir o CRUD completo de uma vez, peça por arquivo:
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

Feito por [Fernando Vernier](https://www.linkedin.com/in/ftvernier/](https://www.linkedin.com/in/fernando-v-10758522/) • [@ftvernier/erp-solutions](https://github.com/ftvernier/erp-solutions)
