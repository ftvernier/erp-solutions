# 🤖 PO-UI Protheus — CLAUDE.md

> Um `CLAUDE.md` pronto para uso, construído a partir de experiência real em produção, para times que desenvolvem telas Angular + PO-UI integradas ao ERP Protheus (TOTVS) usando Claude Code (ou qualquer outro assistente de IA compatível com arquivos de contexto de projeto).

🚀 Visão Geral • 🎯 O Problema • ⚙️ O que está dentro • 🚀 Quick Start • 📖 Estrutura • 🤝 Contribuindo

---

## 🎯 O Problema

Se você já tentou usar IA generativa para desenvolver telas Angular com PO-UI integradas ao Protheus, provavelmente já passou por isso:

- A IA sugere `standalone: true`, mas seu projeto usa NgModules.
- O código gerado não trata subscriptions, causando memory leak.
- O service chama a API sem considerar `filial`, `ProtheusLibCoreService` ou o formato de resposta que o TLPP REST realmente devolve.
- Cada conversa começa do zero, repetindo as mesmas correções de sempre.

O problema não é falta de capacidade do modelo — é **falta de contexto persistente** sobre como o seu time realmente trabalha.

## ⚙️ O que está dentro

Este módulo entrega um `CLAUDE.md` (e seu equivalente `AGENTS.md`, compatível com OpenAI Codex) cobrindo:

- ✅ **Stack e versões** — Angular 21, PO-UI 21, RxJS, TypeScript, com nota sobre o novo build system (`@angular/build`)
- ✅ **Scaffolding via schematics oficiais** (`ng generate`) antes de criar telas manualmente
- ✅ **Documentação PO-UI sob demanda** — prioriza o MCP oficial `@po-ui/mcp`, com fallback em `web_fetch`
- ✅ **Regras de arquitetura sem exceção** — NgModules, SubSink, ProtheusLibCoreService, Reactive Forms, tipagem estrita
- ✅ **Contrato de API formal** — o formato exato de erro/sucesso/coleção/paginação que o TLPP REST precisa devolver para os componentes PO-UI funcionarem sem gambiarra
- ✅ **Grid system, espaçamento e boas práticas de `po-chart`** — para quem monta dashboards fiscais/financeiros
- ✅ **Checklist de entrega** — para revisão antes de abrir um PR

> 💡 Este arquivo nasceu de fricção real: cada seção resolve um problema que já aconteceu em produção, não uma boa prática teórica de blog.

## 🚀 Quick Start

1. Copie o `CLAUDE.md` (e o `AGENTS.md`, se usar Codex) para a **raiz** do seu projeto Angular:

   ```
   seu-projeto/
   ├── .claude/
   ├── CLAUDE.md      ← Claude Code lê automaticamente
   ├── AGENTS.md       ← OpenAI Codex lê automaticamente
   └── package.json
   ```

2. Ajuste a tabela de versões no topo do arquivo para bater com o seu `package.json`.

3. (Opcional, mas recomendado) Configure o MCP oficial do PO-UI para consulta de documentação em tempo real:

   ```json
   {
     "mcpServers": {
       "po-ui": {
         "command": "npx",
         "args": ["-y", "@po-ui/mcp"]
       }
     }
   }
   ```

4. Comece a desenvolver normalmente. O Claude Code (ou Codex) vai carregar essas regras automaticamente em toda sessão.

## 📖 Estrutura

```
po-ui-protheus/
├── CLAUDE.md          ← regras de contexto para Claude Code
├── AGENTS.md          ← mesmo conteúdo, formato lido pelo Codex
├── README.md           ← este arquivo
└── README-ollama.md    ← guia para uso 100% offline com Ollama + Continue.dev
```

> 💡 Usa modelos locais via **Ollama** (sem custo de API)? O MCP do PO-UI e o `web_fetch` não funcionam offline — veja o [README-ollama.md](README-ollama.md) para a versão adaptada da seção de documentação.

## 🧩 Por que compartilhar isso?

Documentação de IA tende a ficar travada no notebook de quem escreveu. A ideia aqui é o oposto: um ponto de partida testado em ambiente real de produção Protheus, que qualquer squad pode adaptar — trocando convenções, versões e regras de negócio pelas próprias.

Se você desenvolve com PO-UI e Protheus, sinta-se livre para usar, adaptar e abrir uma issue/PR com melhorias.

## 🤝 Contribuindo

Encontrou uma regra que não bate com a sua realidade, ou quer sugerir uma seção nova (ex.: outro framework de IA, outro padrão de squad)? Abra uma issue ou um PR no repositório.

## 👨‍💻 Autor

**Fernando Vernier**
- 💼 [LinkedIn](https://www.linkedin.com/in/fernando-v-10758522/)
- 🌐 [GitHub](https://github.com/ftvernier)

---

## 📜 Licença

Este projeto é open source e está disponível sob a [MIT License](LICENSE).

---

**⚠️ Aviso**: este `CLAUDE.md` reflete convenções de um time e projeto específicos. Revise e adapte antes de usar em produção — especialmente as seções de autenticação, contrato de API e estrutura de pastas.

---

**💡 "Documentar para a IA é documentar para o time."**

Feito com dedicação por [Fernando Vernier](https://github.com/ftvernier) — ERP Solutions
