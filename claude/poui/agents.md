# AGENTS.md — PO-UI Protheus Angular

Instruções permanentes para o Codex neste projeto.
Leia este arquivo antes de qualquer tarefa de desenvolvimento Angular/PO-UI.

---

## Stack do projeto

| Item | Versão |
|---|---|
| Angular | 21.x (NgModules — **NUNCA** `standalone: true`) |
| @po-ui/ng-components | 21.x |
| @po-ui/ng-templates | 21.x |
| @totvs/po-theme | 21.x |
| @totvs/protheus-lib-core | 21.x |
| RxJS | 7.8.x |
| SubSink | 1.x |

> **Adapte as versões acima para as do seu `package.json` antes de usar.**

---

## Passo 1 — Consultar documentação oficial do PO-UI

O PO-UI disponibiliza documentação estruturada para LLMs nos seguintes endereços.
**Antes de implementar qualquer componente, consulte a referência oficial.**

```
# Índice geral
https://po-ui.io/llms.txt

# Documentação completa (todos os componentes em um arquivo)
https://po-ui.io/llms-full.txt

# Componente específico — padrão: po-<nome>.md
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

# Interfaces
https://po-ui.io/llms-generated/po-table-column.md
https://po-ui.io/llms-generated/po-dynamic-form-field.md
https://po-ui.io/llms-generated/po-page-action.md
https://po-ui.io/llms-generated/po-modal-action.md
```

**Padrão de nomenclatura:**
- Componentes e interfaces: `po-<nome>.md`
- Serviços: `po-<nome>-service.md`
- Enums: `po-<nome>.md`

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
      const msg = e?.error?.errorMessage ?? e?.message ?? 'Erro desconhecido.';
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

## Passo 3 — Estrutura de feature (padrão CRUD)

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

## Passo 4 — Convenções obrigatórias

- **Idioma:** todos os labels, placeholders, mensagens de erro e notificações em **PT-BR**
- **Notificações:** sempre via `PoNotificationService` — nunca `alert()` ou `console.log()` para o usuário
- **Campos obrigatórios:** `required: true` no `PoDynamicFormField` ou `Validators.required` no Reactive Form
- **Datas Protheus:** o banco armazena `YYYYMMDD`; exibir sempre como `dd/MM/yyyy`
- **Filial:** sempre incluída no payload e nos filtros de listagem
- **Loading:** usar `po-loading-overlay` com `[p-screen-lock]` durante operações assíncronas

---

## Checklist antes de entregar código

- [ ] Consultei a documentação oficial do(s) componente(s) PO-UI usados?
- [ ] Zero `standalone: true` no código?
- [ ] Módulo declara o componente e importa os `PoModule` corretos?
- [ ] Service usa `ProtheusLibCoreService` (ou o mecanismo de auth do projeto)?
- [ ] `ngOnDestroy` com `this.subs.unsubscribe()` em componentes com subscriptions?
- [ ] Interfaces TypeScript para todos os modelos?
- [ ] `catchError` no service?
- [ ] Tudo em PT-BR?
- [ ] Filial incluída nos payloads e filtros?
