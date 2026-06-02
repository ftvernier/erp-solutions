# execauto-generator

> Skill para Claude Code que gera rotinas automáticas (ExecAuto) em ADVPL/TLPP para o ERP Protheus com zero margem para erro de padrão.

---

## O problema que essa skill resolve

Quem desenvolve para Protheus sabe: ExecAuto parece simples, mas tem armadilhas que só aparecem em produção.

- Usar `BEGIN TRANSACTION` em volta do `MSExecAuto` — e concorrer com o controle interno da rotina
- Esquecer de resetar `lMsErroAuto := .F.` antes de cada chamada
- Confundir `GetErrorMessage()` como string quando é um **array de 9 posições**
- Não saber quando usar `FWLoadModel + GetModel` versus `FWMVCRotAuto`
- Usar `PREPARE ENVIRONMENT` dentro de Web Service — quando o ambiente já está definido no `AppServer.ini`

Essa skill instrui o Claude Code a conhecer essas diferenças e gerar código correto desde a primeira vez.

---

## O que está coberto

| Padrão | Descrição |
|---|---|
| Clássico simples | `MSExecAuto` com cabeçalho — rotinas sem itens (FINA040, MATA020...) |
| Clássico com itens | `MSExecAuto` com cabeçalho + array de arrays de itens (MATA410, MATA241...) |
| MVC — FWLoadModel | Acesso a submodelos via `GetModel` + `SetValue` com controle completo |
| MVC — FWMVCRotAuto | Abordagem enxuta para rotinas próprias ou operações simples |

Cada padrão inclui inclusão, alteração e exclusão com tratamento de erro correto.

---

## Estrutura

```
execauto-generator/
  SKILL.md                              # Instruções para o Claude Code
  examples/
    execauto-classico-simples.prw       # MSExecAuto sem itens — FINA040/SE1
    execauto-classico-com-itens.prw     # MSExecAuto com itens — MATA410/SC5+SC6
    execauto-mvc-fwloadmodel.prw        # FWLoadModel + GetModel — MATA010/SB1
    execauto-mvc-fwmvcrotauto.prw       # FWMVCRotAuto — modelo simples e com itens
```

---

## Como instalar

1. Copie a pasta `execauto-generator/` inteira para dentro do `.claude/skills/` do seu projeto:

```
seu-projeto/
  .claude/
    skills/
      execauto-generator/
        SKILL.md
        examples/
          ...
```

2. Abra o projeto no Claude Code — a skill é detectada automaticamente.

3. Peça naturalmente:
   - *"Cria um ExecAuto para incluir um título na SE1 via FINA040"*
   - *"Gera uma rotina automática MVC para alterar o cadastro de fornecedor"*
   - *"Como excluir um pedido de venda via código?"*

---

## Requisitos

- [Claude Code](https://claude.ai/code)
- Protheus 12.1.x ou superior
- ADVPL / TLPP

---

## Referências oficiais

- [MSExecAuto — TDN TOTVS](https://tdn.totvs.com)
- [FWMVCRotAuto — TDN TOTVS](https://tdn.totvs.com)
- [GetAutoGRLog — TDN TOTVS](https://tdn.totvs.com)

---

## Autor

**Fernando Vernier** — Staff Software Engineer, DBA e Tech Lead  
[GitHub](https://github.com/ftvernier/erp-solutions) · [LinkedIn]([https://www.linkedin.com/in/fernandovernier](https://www.linkedin.com/in/fernando-v-10758522/))

---

## Licença

MIT
