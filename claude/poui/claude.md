# CLAUDE.md — PO-UI Protheus Angular

Instruções permanentes para o Claude Code neste projeto.
Leia este arquivo antes de qualquer tarefa de desenvolvimento Angular/PO-UI.

---

## Stack do projeto

| Item | Versão |
|---|---|
| Node.js | 20.11.x ou superior |
| Angular | ~21.2.4 (NgModules — **NUNCA** `standalone: true`) |
| @angular/cli | ~21.2.4 |
| @po-ui/ng-components | 21.x |
| @po-ui/ng-templates | 21.x |
| @totvs/po-theme | 21.x |
| @totvs/protheus-lib-core | 21.x |
| RxJS | ~7.8.1 |
| TypeScript | ~5.9.3 |
| zone.js | ~0.15.0 |
| SubSink | 1.x |

> **Adapte as versões acima para as do seu `package.json` antes de usar.**
> A partir da v14, o número de versão major do **PO UI acompanha o do Angular** (Angular 21 → PO UI 21.x). Consulte a [tabela de compatibilidade](https://github.com/po-ui/po-angular/wiki) se o projeto estiver em versão mais antiga.

### Observação sobre o build system (Angular 19+/21+)

Projetos recentes podem usar o novo builder `@angular/build:*` em vez do tradicional `@angular-devkit/build-angular`. Antes de investigar um erro de build/serve, **verifique no `angular.json` qual builder está configurado**:

```json
"architect": {
  "build": { "builder": "@angular/build:application" },
  "serve": { "builder": "@angular/build:dev-server" }
}
```

Se o builder for `@angular/build:*`, o pacote `@angular/build` precisa estar instalado (`npm install -D @angular/build`). Erro comum: `Could not find the @angular/build:dev-server builder's package`.

---

## Passo 0 — Setup e scaffolding (use os schematics oficiais antes de criar manualmente)

Antes de escrever uma feature do zero, prefira gerar a base via CLI/schematics e depois aplicar as convenções deste documento por cima.

```bash
# Adicionar o PO UI a um projeto existente (configura tema, módulo PO e HttpClientModule)
ng add @po-ui/ng-components

# Adicionar templates dinâmicos
ng add @po-ui/ng-templates
```

### Schematics de componentes (`@po-ui/ng-components`)

| Schematic | Descrição |
|---|---|
| `po-page-list` | Container principal para telas de listagem (lista ou tabela) |
| `po-page-default` | Container principal para telas sem template definido |
| `po-page-edit` | Container para tela de edição/inclusão de registro |
| `po-page-detail` | Container para tela de detalhamento de registro |

### Schematics de templates dinâmicos (`@po-ui/ng-templates`)

| Schematic | Descrição |
|---|---|
| `po-page-dynamic-table` | Lista de registros em tabela baseada em metadados/fields |
| `po-page-dynamic-edit` | Edição/criação de registros baseada em metadados |
| `po-page-dynamic-detail` | Exibição de detalhes baseada em metadados |
| `po-page-dynamic-search` | Tela de pesquisa com ações já definidas |
| `po-page-job-scheduler` | Tela de agendamento de processos (Job Scheduler) |
| `po-page-login` | Template de tela de login |
| `po-page-change-password` | Template de cadastro/alteração de senha |
| `po-page-blocked-user` | Template de tela de bloqueio de usuário |

Uso: `ng generate <package>:<schematic-name>`. Exemplo:

```bash
ng generate @po-ui/ng-templates:po-page-dynamic-table
```

### Atualizando o PO UI (`ng update`)

```bash
# 1. Atualize o Angular primeiro
npm install @angular-devkit/schematics --save-dev   # necessário em Angular 20+
ng update @angular/cli@21 @angular/core@21 --force

# 2. Depois atualize o PO UI
ng update @po-ui/ng-components --allow-dirty --force
```

Se o `ng update` falhar: apague `node_modules` e `package-lock.json`, rode `npm i --legacy-peer-deps`, e tente novamente. O processo pode perguntar se deseja migrar para a nova biblioteca de ícones — decida conscientemente, não aceite por padrão sem avaliar o impacto visual.

Antes de subir uma versão major, consulte:
- [Guia de Depreciações](https://po-ui.io/guides/deprecations)
- [CHANGELOG no GitHub](https://github.com/po-ui/po-angular/blob/master/CHANGELOG.md)

---

## Passo 1 — Buscar documentação PO-UI antes de escrever código

**Antes de implementar qualquer componente, busque a referência oficial.** Use o MCP do PO-UI como fonte primária; recorra ao `web_fetch` apenas se o MCP não estiver disponível no ambiente atual.

### Fonte primária — MCP `@po-ui/mcp`

O PO-UI oferece um servidor MCP oficial. Se as ferramentas abaixo estiverem disponíveis na sessão, **use-as em vez de `web_fetch`** — são mais confiáveis (sem necessidade de montar/adivinhar slug de URL) e têm busca textual nativa.

| Ferramenta | Uso |
|---|---|
| `list_components` | Lista componentes, serviços, interfaces e enums (com filtro por seção/texto). Útil para descobrir o que existe antes de implementar algo novo ou verificar se já há um componente pronto para o caso. |
| `get_component_docs` | Documentação completa em Markdown de um componente/API pelo slug. Use sempre antes de implementar ou alterar uso de um componente específico. |
| `search_docs` | Busca texto livre em toda a documentação. Ideal quando não se sabe o nome exato do componente (ex.: "componente com upload de arquivo"). |
| `get_guide` | Conteúdo de guias (ex.: `getting-started`, `schematics`, `migration-poui`). |

**Configuração** (não exige instalação — executa via `npx`):

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

- Cursor: `.cursor/mcp.json` ou configurações globais
- Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) ou `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
- Claude Code: configurar conforme o método de MCP do projeto/usuário

### Fallback — `web_fetch` nas URLs de documentação

Caso o MCP não esteja configurado no ambiente, busque via `web_fetch`:

```
# Índice geral
https://po-ui.io/llms.txt

# Componente específico
https://po-ui.io/llms-generated/<nome-do-componente>.md

# Exemplos
https://po-ui.io/llms-generated/po-table.md
https://po-ui.io/llms-generated/po-dynamic-form.md
https://po-ui.io/llms-generated/po-page-list.md
https://po-ui.io/llms-generated/po-page-edit.md
https://po-ui.io/llms-generated/po-modal.md
https://po-ui.io/llms-generated/po-upload.md
https://po-ui.io/llms-generated/po-lookup.md
https://po-ui.io/llms-generated/po-page-dynamic-table.md
https://po-ui.io/llms-generated/po-page-dynamic-edit.md
https://po-ui.io/llms-generated/po-notification-service.md
https://po-ui.io/llms-generated/po-dialog-service.md
https://po-ui.io/llms-generated/po-chart.md
https://po-ui.io/llms-generated/po-grid.md
https://po-ui.io/llms-generated/po-helper.md

# Interfaces
https://po-ui.io/llms-generated/po-table-column.md
https://po-ui.io/llms-generated/po-dynamic-form-field.md
https://po-ui.io/llms-generated/po-page-action.md
https://po-ui.io/llms-generated/po-modal-action.md
```

**Padrão:** componentes → `po-<nome>.md` | serviços → `po-<nome>-service.md`

### Componentes novos/relevantes a ter em mente

- **`po-grid`**: em desenvolvimento — pode haver *breaking changes* nas próximas versões. Avaliar com cautela antes de usar em produção.
- **`po-helper`**: ícone de ajuda/informação com popover, útil para complementar campos de formulário.
- **`po-code-editor`**: editor de código baseado no Monaco Editor.
- **`po-list-view`**, **`po-filter-chip`**, **`po-datetimepicker`**: componentes adicionais disponíveis na v21.
- **`po-gauge` está DEPRECIADO** e será removido na v22.x — não usar em código novo; preferir `po-chart` (tipo gauge semicircular) ou avaliar alternativa.

---

## Passo 2 — Regras de arquitetura (sem exceção)

### NgModules obrigatório

```typescript
// ✅ CORRETO
@NgModule({ declarations: [MeuComponent] })
export class MeuModule {}

// ❌ NUNCA FAZER
@Component({ standalone: true })
export class MeuComponent {}
```

### SubSink para subscriptions

```typescript
import { SubSink } from 'subsink';

export class MeuComponent implements OnDestroy {
  private subs = new SubSink();

  ngOnInit(): void {
    this.subs.sink = this.service.listar().subscribe(...);
  }

  ngOnDestroy(): void {
    this.subs.unsubscribe(); // sempre
  }
}
```

### ProtheusLibCoreService — única fonte de contexto Protheus

```typescript
// ✅ CORRETO — no service
import { ProtheusLibCoreService } from '@totvs/protheus-lib-core';
import { HttpHeaders } from '@angular/common/http';

constructor(
  private http: HttpClient,
  private protheusCoreLib: ProtheusLibCoreService
) {
  this.baseUrl = this.protheusCoreLib.getServerUrl();
  this.filial  = this.protheusCoreLib.getBranchCode();
  this.usuario = this.protheusCoreLib.getUserName();
}

private get headers(): HttpHeaders {
  return new HttpHeaders({
    'Authorization': this.protheusCoreLib.getAuthorizationHeaderValue(),
    'Content-Type': 'application/json'
  });
}
```

> **Adapte este bloco se seu projeto usar outro mecanismo de autenticação.**

### HttpClient — sempre no service, nunca no componente

```typescript
// ✅ CORRETO
@Injectable({ providedIn: 'root' })
export class PedidoService {
  constructor(private http: HttpClient) {}
}

// ❌ NUNCA FAZER
@Component({...})
export class PedidoComponent {
  constructor(private http: HttpClient) {} // errado
}
```

### Reactive Forms — nunca template-driven

```typescript
// ✅ CORRETO
this.form = this.fb.group({
  codigo:    ['', Validators.required],
  descricao: ['', [Validators.required, Validators.maxLength(40)]]
});

// ❌ EVITAR para formulários ERP
// <input [(ngModel)]="registro.codigo">
```

### catchError — tratamento no service, mensagem humanizada no componente

```typescript
// No service
listar(): Observable<MeuModel[]> {
  return this.http.get<MeuModel[]>(this.url, { headers: this.headers })
    .pipe(catchError(e => {
      const msg = e?.error?.message ?? e?.error?.errorMessage ?? e?.message ?? 'Erro desconhecido.';
      return throwError(() => new Error(msg));
    }));
}

// No componente
this.subs.sink = this.service.listar().subscribe({
  next: (dados) => this.items = dados,
  error: (err: Error) => this.notif.error({ message: err.message })
});
```

### Tipagem estrita — sem `any` implícito

```typescript
// ✅ CORRETO
interface PedidoVenda {
  filial:  string;
  numero:  string;
  cliente: string;
  valor:   number;
}

// ❌ EVITAR
const pedido: any = {};
```

---

## Passo 3 — Contrato de API esperado pelos componentes PO-UI

Os componentes PO-UI que consomem endpoints (`po-table`, `po-lookup`, `po-page-dynamic-table`, `po-page-dynamic-edit`, etc.) esperam um formato de requisição/resposta padronizado. **O TLPP REST do lado Protheus deve devolver exatamente esse shape**, sem necessidade de adaptação manual no Angular.

### Mensagens de erro (HTTP 4xx/5xx)

Campos obrigatórios:

```json
{
  "code": "Código identificador do erro",
  "message": "Literal no idioma da requisição descrevendo o erro para o cliente",
  "detailedMessage": "Mensagem técnica e mais detalhada do erro"
}
```

Campos opcionais: `type` (`error` | `warning` | `information`), `helpUrl`, `details[]` (lista recursiva de objetos de erro).

### Mensagens de sucesso (item único)

Retorna a entidade diretamente. Opcionalmente pode incluir `_messages[]` (mesmo formato de erro, para avisos/informações complementares):

```json
{
  "id": 10,
  "name": "John",
  "_messages": [{ "code": "INFO", "type": "information", "message": "...", "detailedMessage": "..." }]
}
```

### Mensagens de sucesso (coleção)

```json
{
  "hasNext": true,
  "items": [ {}, {} ],
  "_messages": [ ... ]
}
```

- `hasNext`: indica se existe próxima página.
- `items`: lista de itens.

### Parâmetros de requisição em coleções

| Recurso | Parâmetro | Regra |
|---|---|---|
| Ordenação | `order` | `order=name,-age,surname` → crescente sem sinal, decrescente com `-` |
| Filtro | `property=value` | `?name=john&surname=doe` |
| Paginação | `page`, `pageSize` | Numéricos, > 0. Semântica de multiplicador: `page=4&pageSize=10` → registros 31 a 40. Resposta deve trazer `hasNext`. |

> ⚠️ Esse contrato também é a base usada pelo **PO Sync** (sincronização offline/Ionic) e por outros mecanismos PO-UI — é o "padrão de API" oficial da biblioteca, não apenas convenção de um componente isolado.

---

## Passo 4 — Estrutura de feature (padrão CRUD)

```
src/app/features/<nome-da-feature>/
├── <nome>.module.ts          ← NgModule + imports PO-UI
├── <nome>-routing.module.ts  ← rotas: '', 'novo', ':id', ':id/editar'
├── <nome>-list/
│   ├── <nome>-list.component.ts
│   └── <nome>-list.component.html
├── <nome>-form/
│   ├── <nome>-form.component.ts
│   └── <nome>-form.component.html
├── <nome>.service.ts
└── <nome>.model.ts           ← interfaces TypeScript
```

### Rotas padrão

```typescript
const routes: Routes = [
  { path: '',           component: NomeListComponent },
  { path: 'novo',       component: NomeFormComponent },
  { path: ':id',        component: NomeDetailComponent },
  { path: ':id/editar', component: NomeFormComponent }
];
```

### Lazy load no app-routing

```typescript
{
  path: 'minha-feature',
  loadChildren: () => import('./features/minha-feature/nome.module')
    .then(m => m.NomeModule)
}
```

---

## Passo 5 — Convenções obrigatórias

- **Idioma:** todos os labels, placeholders, mensagens de erro e notificações em **PT-BR**
- **Notificações:** sempre via `PoNotificationService` — nunca `alert()` ou `console.log()` para o usuário
- **Campos obrigatórios:** `required: true` no `PoDynamicFormField` ou `Validators.required` no Reactive Form
- **Datas Protheus:** o banco armazena `YYYYMMDD`; exibir sempre como `dd/MM/yyyy`
- **Filial:** sempre incluída no payload e nos filtros de listagem
- **Loading:** usar `po-loading-overlay` com `[p-screen-lock]` durante operações assíncronas

---

## Passo 6 — Grid System e Espaçamento (`@po-ui/style`)

### Grid System

Estrutura de 12 colunas. Classe: `po-<tamanho-tela>-<tamanho-coluna>` (soma das colunas de uma linha deve ser 12). Envolver com `po-row` (opcional) para organizar múltiplas linhas.

| Prefixo | Largura de tela |
|---|---|
| `po-sm-*` | até 480px |
| `po-md-*` | 481px – 960px |
| `po-lg-*` | 961px – 1366px |
| `po-xl-*` | a partir de 1367px |

```html
<div class="po-row">
  <div class="po-xl-6 po-lg-6 po-md-6 po-sm-6">...</div>
  <div class="po-xl-6 po-lg-6 po-md-6 po-sm-6">...</div>
</div>
```

- `po-md-*` e `po-lg-*` têm comportamento de fallback: telas menores assumem tamanho 12 automaticamente.
- **Responsividade:** redefinir o tamanho por breakpoint, ex.: `po-xl-6 po-lg-6 po-md-12 po-sm-12` (colunas empilham em telas menores).
- **Visibilidade condicional:** `po-visible-[tamanho]` / `po-hidden-[tamanho]` (ex.: `po-visible-sm-6`, `po-hidden-md`).
- **Deslocamento:** `po-offset-[sm|md|lg|xl]-[1-11]` para empurrar coluna à direita. Soma de offset + tamanho da coluna deve ser ≤ 12.
- Breakpoints são customizáveis via tokens CSS (`--gridSystemMdMinWidth`, etc.) e `PoMediaQueryService`, caso necessário no futuro.

### Espaçamento (margin/padding utilitário)

Padrão: `po-<m|p><lado?>-<breakpoint?>-<tamanho>`

- Propriedade: `m` (margin) ou `p` (padding)
- Lado (opcional): `t`, `r`, `b`, `l` — omitir para todos os lados
- Breakpoint (opcional): `sm`, `md`, `lg`, `xl`
- Tamanho: `0` (0px) → `1` (8px) → `2` (16px) → `3` (24px) → `4` (32px) → `5` (40px)

```html
<div class="po-m-5">margin todos os lados, 40px</div>
<div class="po-ml-2">margin-left 16px</div>
<div class="po-ml-md-3">margin-left 24px a partir de md</div>
```

> Boa prática: preferir `margin-bottom` para espaçamento entre elementos adjacentes, evitando colapso de margem entre elementos verticais.

---

## Passo 7 — Boas práticas para `po-chart`

### Quando usar cada tipo

| Gráfico | Uso recomendado |
|---|---|
| Área | Totais acumulados ao longo do tempo; tendências entre atributos relacionados |
| Barra | Comparações/séries temporais com **muitos** itens (mais espaço para rótulos) |
| Coluna | Comparações/séries temporais com **poucos** itens |
| Coluna com linha (Pareto) | Priorização 80/20 — identificar onde concentrar esforço |
| Gauge semicircular | Desempenho vs. meta (ex.: vendas da equipe) |
| Linha | Tendência contínua ao longo do tempo. **Não usar** para distribuição (preferir coluna) |
| Pizza | Proporção de um todo. Evitar mais de 5 fatias |
| Rosca | Proporção comparativa. Fatias < 10% devem ser agrupadas em "Outros" |
| Radar | Perfil de desempenho multi-categoria |

### Guia de cores

- Uma cor por tipo de dado, consistente em todo o gráfico/dashboard.
- Garantir contraste suficiente entre cores.
- **Evitar**: associar vermelho a valores positivos ou verde a negativos (e vice-versa de forma não convencional) — a associação cromática influencia diretamente a interpretação do usuário.
- **Evitar** combinações de alto contraste tipo vermelho/verde ou azul/amarelo (salvo direcionamento de marca).
- **Evitar** combinações de baixo contraste tipo azul claro/cinza (salvo direcionamento de marca).
- Combinações sugeridas: cinza+azul (atual vs. passado), azul+laranja (positivo/negativo), verde+vermelho (positivo/negativo), azul+cinza+verde (composição de 3 cores).

> Relevante para dashboards financeiros/fiscais (contas a pagar vs. receber, indicadores de faturamento, etc.).

---

## Fora de escopo (não aplicar sem necessidade explícita)

- **PO Sync (`@po-ui/ng-sync`)**: voltado a apps **Ionic offline-first**. Não se aplica ao cenário atual (Angular web puro). Só considerar se houver demanda futura de app mobile/híbrido consumindo o Protheus offline.
- **PO Theme CLI**: criação de temas customizados via `@po-ui/theme-cli` (`po-theme new`, `po-theme build`). Relevante apenas se houver uma demanda de design system próprio além do tema padrão `@totvs/po-theme`.

---

## Checklist antes de entregar código

- [ ] Consultei a doc do(s) componente(s) PO-UI usados (via MCP `@po-ui/mcp` ou, na ausência dele, `web_fetch`)?
- [ ] Avaliei se existe schematic oficial (`ng generate`) para o scaffold antes de criar manualmente?
- [ ] Zero `standalone: true` no código?
- [ ] Módulo declara o componente e importa os `PoModule` corretos?
- [ ] Service usa `ProtheusLibCoreService` (ou o mecanismo de auth do projeto)?
- [ ] `ngOnDestroy` com `this.subs.unsubscribe()` em componentes com subscriptions?
- [ ] Interfaces TypeScript para todos os modelos?
- [ ] `catchError` no service?
- [ ] O endpoint TLPP REST segue o contrato de API (erro/sucesso/coleção/paginação/filtro/ordenação) do Passo 3?
- [ ] Nenhum componente depreciado em uso (ex.: `po-gauge`)?
- [ ] Tudo em PT-BR?
- [ ] Filial incluída nos payloads e filtros?
