# 🤖 CLAUDE.md — PO-UI Protheus Angular

> Instruções permanentes para o **Claude Code** que transformam o agente em um especialista em Angular + PO-UI para o ERP Protheus, seguindo as melhores práticas de arquitetura desde o primeiro comando.

---

## O que é isso?

Este repositório contém um arquivo `CLAUDE.md` pronto para ser colado na raiz de qualquer projeto Angular que use a biblioteca [PO-UI da TOTVS](https://po-ui.io).

O `CLAUDE.md` é lido automaticamente pelo **Claude Code** (extensão VS Code / CLI) no início de cada sessão. Com ele configurado, o Claude passa a:

- Buscar a **documentação oficial do PO-UI em tempo real** antes de escrever qualquer componente
- Aplicar automaticamente os **padrões de arquitetura** do projeto (NgModules, SubSink, ProtheusLibCore, Reactive Forms)
- Gerar código pronto com tratamento de erro, tipagem estrita e notificações em PT-BR
- Nunca usar `standalone: true`, `any` implícito ou HttpClient direto no componente

---

## Instalação

### 1. Instale o Claude Code

**VS Code:**
Instale a extensão **Claude Code** na marketplace do VS Code.

**Terminal (CLI):**
```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Copie o CLAUDE.md para a raiz do seu projeto

```bash
# Na raiz do seu projeto Angular
curl -o CLAUDE.md https://raw.githubusercontent.com/<seu-usuario>/erp-solutions/main/po-ui-protheus/CLAUDE.md
```

Ou baixe manualmente e cole na raiz do projeto (mesmo nível do `package.json`).

### 3. Adapte as versões

Abra o `CLAUDE.md` e ajuste a tabela de stack para as versões do seu `package.json`:

```markdown
| Angular                  | 21.x  ← altere aqui
| @po-ui/ng-components     | 21.x  ← altere aqui
| @totvs/protheus-lib-core | 21.x  ← altere aqui
```

### 4. Adapte o mecanismo de autenticação (se necessário)

Se o seu projeto **não usa** `@totvs/protheus-lib-core` para autenticação, substitua o bloco `ProtheusLibCoreService` pelo mecanismo do seu projeto (JWT próprio, token fixo, etc.).

### 5. Pronto

Abra o projeto no VS Code com a extensão Claude Code ativa. O agente lerá o `CLAUDE.md` automaticamente.

---

## Como usar no dia a dia

Após a configuração, basta descrever o que você precisa normalmente:

```
Crie uma tela de listagem de pedidos de venda com filtro por cliente e data de emissão.
```

```
Adicione um modal de confirmação de exclusão na tela de cadastro de fornecedores.
```

```
Implemente a importação de CSV para a tabela SE1 com validação de campos obrigatórios.
```

O Claude Code vai:
1. Buscar automaticamente a doc do PO-UI (`po-page-list.md`, `po-table.md`, etc.)
2. Gerar o módulo, componente, service e model seguindo os padrões definidos
3. Incluir `ngOnDestroy`, `SubSink`, `catchError`, filial e PT-BR sem que você precise pedir

---

## O que o CLAUDE.md cobre

| Área | Detalhe |
|---|---|
| **Documentação PO-UI** | URLs `llms-generated` para todos os componentes, serviços e interfaces |
| **NgModules** | Estrutura de módulo + routing por feature, sem `standalone` |
| **ProtheusLibCoreService** | Padrão de `headers`, `baseUrl`, `filial` e `usuario` |
| **SubSink** | Gerenciamento de subscriptions sem `takeUntil` manual |
| **Reactive Forms** | Nunca template-driven para formulários ERP |
| **Tratamento de erro** | `catchError` no service + mensagem humanizada no componente |
| **Tipagem** | Interfaces TypeScript para todos os modelos, sem `any` |
| **Convenções** | PT-BR, datas Protheus (`YYYYMMDD`→`dd/MM/yyyy`), filial no payload |

---

## Estrutura de feature gerada automaticamente

```
src/app/features/<nome>/
├── <nome>.module.ts
├── <nome>-routing.module.ts
├── <nome>-list/
│   ├── <nome>-list.component.ts
│   └── <nome>-list.component.html
├── <nome>-form/
│   ├── <nome>-form.component.ts
│   └── <nome>-form.component.html
├── <nome>.service.ts
└── <nome>.model.ts
```

---

## Por que funciona melhor do que um prompt avulso?

Um prompt avulso some depois da primeira resposta. O `CLAUDE.md` é persistente — ele é lido em toda sessão, em todo arquivo, em todo comando. Isso significa que mesmo em um projeto novo ou depois de semanas sem usar, o agente mantém os padrões do projeto sem você precisar repetir as instruções.

Além disso, em vez de manter uma cópia estática da documentação PO-UI (que fica desatualizada a cada release), o `CLAUDE.md` instrui o Claude a buscar a documentação oficial em tempo real via `https://po-ui.io/llms-generated/<componente>.md` — um endpoint mantido pela própria TOTVS para consumo por ferramentas de IA.

---

## Compatibilidade

| Ferramenta | Suporte |
|---|---|
| Claude Code (VS Code) | ✅ |
| Claude Code (CLI) | ✅ |
| Claude.ai (web/mobile) | ⚠️ Parcial — use o arquivo `.skill` disponível neste repo |
| GitHub Copilot | ❌ Usa formato diferente (`copilot-instructions.md`) |
| Cursor | ⚠️ Parcial — renomeie para `.cursorrules` |

---

## Contribuindo

Pull requests são bem-vindos. Se você adaptou o `CLAUDE.md` para uma versão diferente do PO-UI ou para um mecanismo de auth específico, considere abrir um PR com a variante.

---

## Licença

MIT — use, adapte e distribua à vontade.

---

Feito por [Fernando Vernier](https://www.linkedin.com/in/fernando-v-10758522/) • [@ftvernier/erp-solutions](https://github.com/ftvernier/erp-solutions)
