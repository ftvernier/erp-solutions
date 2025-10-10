# Parâmetros do Protheus (SX6)

Configure os seguintes parâmetros no Protheus para habilitar a publicação de eventos no Kafka.

## Parâmetros Obrigatórios

### MV_KFKURL
- **Tipo:** Caractere
- **Descrição:** URL do middleware que publica eventos no Kafka
- **Valor padrão:** `http://localhost:3000/events`
- **Exemplo:** `http://192.168.1.100:3000/events` ou `http://middleware.empresa.com:3000/events`

### MV_KFKENAB
- **Tipo:** Lógico
- **Descrição:** Habilita/Desabilita a publicação de eventos no Kafka
- **Valor padrão:** `.T.` (Habilitado)
- **Valores possíveis:** 
  - `.T.` - Habilita publicação
  - `.F.` - Desabilita publicação

### MV_KFKTOUT
- **Tipo:** Numérico
- **Descrição:** Timeout em segundos para requisição HTTP ao middleware
- **Valor padrão:** `30`
- **Recomendação:** Entre 10 e 60 segundos

---

## Como Criar os Parâmetros

### Opção 1: Via Configurador (CFGX024)

1. Acesse o **Configurador** do Protheus
2. Vá em **Ambiente > Cadastros > Parâmetros (SX6)**
3. Clique em **Incluir** e preencha:

**Parâmetro 1:**
- Filial: `  ` (em branco para todos)
- Variável: `MV_KFKURL`
- Tipo: `C` (Caractere)
- Conteúdo: `http://localhost:3000/events`
- Descrição: `URL do middleware Kafka`

**Parâmetro 2:**
- Filial: `  ` (em branco para todos)
- Variável: `MV_KFKENAB`
- Tipo: `L` (Lógico)
- Conteúdo: `.T.`
- Descrição: `Habilita publicacao Kafka`

**Parâmetro 3:**
- Filial: `  ` (em branco para todos)
- Variável: `MV_KFKTOUT`
- Tipo: `N` (Numérico)
- Conteúdo: `30`
- Descrição: `Timeout requisicao Kafka`

### Opção 2: Via SQL (Direto no Banco)

```sql
-- Ajuste o nome da tabela conforme seu ambiente (SX6010, SX6990, etc)

INSERT INTO SX6010 (X6_FIL, X6_VAR, X6_TIPO, X6_CONTEUD, X6_DESCRIC, X6_DSCSPA, X6_DSCENG, D_E_L_E_T_, R_E_C_N_O_)
VALUES ('  ', 'MV_KFKURL', 'C', 'http://localhost:3000/events', 'URL do middleware Kafka', 'URL del middleware Kafka', 'Kafka middleware URL', ' ', 
(SELECT ISNULL(MAX(R_E_C_N_O_), 0) + 1 FROM SX6010));

INSERT INTO SX6010 (X6_FIL, X6_VAR, X6_TIPO, X6_CONTEUD, X6_DESCRIC, X6_DSCSPA, X6_DSCENG, D_E_L_E_T_, R_E_C_N_O_)
VALUES ('  ', 'MV_KFKENAB', 'L', '.T.', 'Habilita publicacao Kafka', 'Habilita publicacion Kafka', 'Enable Kafka publishing', ' ',
(SELECT ISNULL(MAX(R_E_C_N_O_), 0) + 1 FROM SX6010));

INSERT INTO SX6010 (X6_FIL, X6_VAR, X6_TIPO, X6_CONTEUD, X6_DESCRIC, X6_DSCSPA, X6_DSCENG, D_E_L_E_T_, R_E_C_N_O_)
VALUES ('  ', 'MV_KFKTOUT', 'N', '30', 'Timeout requisicao Kafka', 'Timeout solicitud Kafka', 'Kafka request timeout', ' ',
(SELECT ISNULL(MAX(R_E_C_N_O_), 0) + 1 FROM SX6010));
```

---

## Validação

Execute o comando abaixo no console ADVPL para verificar se os parâmetros foram criados corretamente:

```advpl
ConOut("MV_KFKURL: " + AllTrim(SuperGetMV("MV_KFKURL", .F., "")))
ConOut("MV_KFKENAB: " + If(SuperGetMV("MV_KFKENAB", .F., .F.), ".T.", ".F."))
ConOut("MV_KFKTOUT: " + cValToChar(SuperGetMV("MV_KFKTOUT", .F., 0)))
```

---

## Dicas de Configuração

### Ambientes Diferentes

Você pode configurar URLs diferentes por filial:

```
Filial 01 (Matriz) -> http://middleware-matriz.empresa.com:3000/events
Filial 02 (Filial)  -> http://middleware-filial.empresa.com:3000/events
```

### Desabilitando em Ambiente de Testes

Para desabilitar temporariamente sem remover o código:

```advpl
// Via função
PutMV("MV_KFKENAB", .F.)

// Ou altere direto no Configurador
MV_KFKENAB = .F.
```

### Troubleshooting

Se os eventos não estão sendo publicados, verifique:

1. ✅ Parâmetros existem e estão preenchidos corretamente
2. ✅ `MV_KFKENAB` está como `.T.`
3. ✅ URL do middleware está acessível da rede do Protheus
4. ✅ Console do Protheus para ver logs de erro
5. ✅ Middleware está rodando e respondendo no `/health`
