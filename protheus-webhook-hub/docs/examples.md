# 📚 Exemplos Práticos - Protheus Webhook Hub

## Índice
1. [Notificações de Vendas](#notificações-de-vendas)
2. [Alertas de Estoque](#alertas-de-estoque)
3. [Gestão de Inadimplência](#gestão-de-inadimplência)
4. [Acompanhamento de Produção](#acompanhamento-de-produção)
5. [Integração com CRM](#integração-com-crm)
6. [Automação de Processos](#automação-de-processos)

---

## 1. Notificações de Vendas

### 📊 Caso de Uso
Notificar a equipe comercial no Slack toda vez que um pedido for criado ou aprovado.

### Configuração no Painel
```
Nome: Notificação de Vendas
Tipo de Evento: pedido.criado
Destino: Slack
URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Código ADVPL

```advpl
#Include "Protheus.ch"

/*
  Ponto de Entrada: MTA410I
  Após inclusão do pedido de vendas
*/
User Function MTA410I()
    Local oData := JsonObject():new()
    Local nTotal := 0
    
    // Calcula valor total do pedido
    DbSelectArea("SC6")
    SC6->(DbSetOrder(1))
    SC6->(DbSeek(xFilial("SC6") + SC5->C5_NUM))
    
    While !SC6->(Eof()) .And. SC6->C6_NUM == SC5->C5_NUM
        nTotal += SC6->C6_VALOR
        SC6->(DbSkip())
    End
    
    // Monta dados do evento
    oData["numero_pedido"] := SC5->C5_NUM
    oData["tipo_pedido"] := Iif(SC5->C5_TIPO=="N", "Normal", "Devolução")
    oData["cliente_cod"] := SC5->C5_CLIENTE
    oData["cliente_nome"] := Posicione("SA1",1,xFilial("SA1")+SC5->C5_CLIENTE+SC5->C5_LOJACLI,"A1_NOME")
    oData["vendedor"] := Posicione("SA3",1,xFilial("SA3")+SC5->C5_VEND1,"A3_NOME")
    oData["valor_total"] := nTotal
    oData["condicao_pagto"] := AllTrim(Posicione("SE4",1,xFilial("SE4")+SC5->C5_CONDPAG,"E4_DESCRI"))
    oData["data_emissao"] := DtoC(SC5->C5_EMISSAO)
    oData["data_entrega"] := DtoC(SC5->C5_ENTREG)
    
    // Envia webhook
    WHSendEvent("pedido.criado", oData)
    
Return
```

### Resultado no Slack
```
🎉 Novo Pedido Criado!

Pedido: 123456
Cliente: EMPRESA ABC LTDA
Vendedor: João Silva
Valor: R$ 15.000,00
Condição: 30/60/90 dias
Entrega: 15/11/2025
```

---

## 2. Alertas de Estoque

### 📦 Caso de Uso
Alertar o time de compras quando um produto atingir o estoque mínimo.

### Configuração no Painel
```
Nome: Alerta Estoque Crítico
Tipo de Evento: estoque.critico
Destino: Microsoft Teams
URL: https://outlook.office.com/webhook/YOUR/WEBHOOK/URL
```

### Código ADVPL

```advpl
User Function JOBESTQ01()
    Local aArea := GetArea()
    
    DbSelectArea("SB2")
    SB2->(DbSetOrder(1))
    SB2->(DbGoTop())
    
    While !SB2->(Eof())
        
        DbSelectArea("SB1")
        SB1->(DbSetOrder(1))
        If SB1->(DbSeek(xFilial("SB1") + SB2->B2_COD))
            
            Local nSaldo := SaldoSB2()
            Local nEstMin := SB1->B1_EMIN
            
            // Verifica se está abaixo do mínimo
            If nSaldo > 0 .And. nSaldo < nEstMin
                Local oData := JsonObject():new()
                
                oData["produto_codigo"] := SB2->B2_COD
                oData["produto_descricao"] := SB1->B1_DESC
                oData["local"] := SB2->B2_LOCAL
                oData["saldo_atual"] := nSaldo
                oData["estoque_minimo"] := nEstMin
                oData["percentual"] := Round((nSaldo/nEstMin)*100, 2)
                oData["urgencia"] := Iif(nSaldo < (nEstMin/2), "ALTA", "MÉDIA")
                
                // Informações de compra
                oData["fornecedor"] := Posicione("SA2",1,xFilial("SA2")+SB1->B1_PROC+SB1->B1_LOJPROC,"A2_NOME")
                oData["lead_time"] := SB1->B1_PE
                
                WHSendEvent("estoque.critico", oData)
            EndIf
            
        EndIf
        
        SB2->(DbSkip())
    End
    
    RestArea(aArea)
    
Return
```

### Schedule no Protheus
```advpl
// Executar a cada 6 horas
U_JOBESTQ01()
```

---

## 3. Gestão de Inadimplência

### 💰 Caso de Uso
Notificar diariamente títulos vencidos e enviar relatório para o financeiro.

### Configuração no Painel
```
Nome: Inadimplência Diária
Tipo de Evento: inadimplencia.detectada
Destino: Slack - Canal #financeiro
```

### Código ADVPL

```advpl
User Function JOBINAD01()
    Local aArea := GetArea()
    Local dDataBase := Date()
    
    DbSelectArea("SE1")
    SE1->(DbSetOrder(1)) // E1_FILIAL+E1_PREFIXO+E1_NUM+E1_PARCELA+E1_TIPO
    SE1->(DbGoTop())
    
    While !SE1->(Eof())
        
        // Verifica se está vencido e em aberto
        If SE1->E1_SALDO > 0 .And. SE1->E1_VENCREA < dDataBase
            
            Local nDiasAtraso := dDataBase - SE1->E1_VENCREA
            Local oData := JsonObject():new()
            
            // Dados do título
            oData["titulo"] := AllTrim(SE1->E1_PREFIXO) + " " + AllTrim(SE1->E1_NUM) + "/" + AllTrim(SE1->E1_PARCELA)
            oData["cliente_codigo"] := SE1->E1_CLIENTE
            oData["cliente_nome"] := Posicione("SA1",1,xFilial("SA1")+SE1->E1_CLIENTE+SE1->E1_LOJA,"A1_NOME")
            oData["cliente_telefone"] := Posicione("SA1",1,xFilial("SA1")+SE1->E1_CLIENTE+SE1->E1_LOJA,"A1_TEL")
            oData["valor_titulo"] := SE1->E1_VALOR
            oData["valor_saldo"] := SE1->E1_SALDO
            oData["data_emissao"] := DtoC(SE1->E1_EMISSAO)
            oData["data_vencimento"] := DtoC(SE1->E1_VENCREA)
            oData["dias_atraso"] := nDiasAtraso
            
            // Classifica urgência
            If nDiasAtraso > 60
                oData["status"] := "CRÍTICO"
            ElseIf nDiasAtraso > 30
                oData["status"] := "ALERTA"
            Else
                oData["status"] := "ATENÇÃO"
            EndIf
            
            // Dados do vendedor
            Local cVendedor := Posicione("SA1",1,xFilial("SA1")+SE1->E1_CLIENTE+SE1->E1_LOJA,"A1_VEND")
            oData["vendedor"] := Posicione("SA3",1,xFilial("SA3")+cVendedor,"A3_NOME")
            
            WHSendEvent("inadimplencia.detectada", oData)
            
        EndIf
        
        SE1->(DbSkip())
    End
    
    RestArea(aArea)
    
Return
```

---

## 4. Acompanhamento de Produção

### 🏭 Caso de Uso
Notificar quando uma ordem de produção for finalizada.

### Código ADVPL

```advpl
User Function MT650FIM()
    Local oData := JsonObject():new()
    
    DbSelectArea("SC2")
    
    oData["ordem_producao"] := SC2->C2_NUM + SC2->C2_ITEM + SC2->C2_SEQUEN
    oData["produto_codigo"] := SC2->C2_PRODUTO
    oData["produto_descricao"] := Posicione("SB1",1,xFilial("SB1")+SC2->C2_PRODUTO,"B1_DESC")
    oData["quantidade"] := SC2->C2_QUANT
    oData["data_inicio"] := DtoC(SC2->C2_DATPRI)
    oData["data_fim"] := DtoC(SC2->C2_DATPRF)
    oData["centro_custo"] := SC2->C2_CC
    
    // Calcula tempo de produção
    Local nDias := SC2->C2_DATPRF - SC2->C2_DATPRI
    oData["tempo_producao_dias"] := nDias
    
    WHSendEvent("producao.finalizada", oData)
    
Return
```

---

## 5. Integração com CRM

### 📱 Caso de Uso
Sincronizar novos clientes com o CRM externo via webhook.

### Código ADVPL

```advpl
User Function MA030TOK()
    
    // Apenas para inclusões
    If Inclui
        
        Local oData := JsonObject():new()
        
        // Dados cadastrais
        oData["codigo"] := M->A1_COD
        oData["loja"] := M->A1_LOJA
        oData["razao_social"] := M->A1_NOME
        oData["nome_fantasia"] := M->A1_NREDUZ
        oData["cnpj"] := M->A1_CGC
        oData["inscricao_estadual"] := M->A1_INSCR
        
        // Endereço
        oData["endereco"] := M->A1_END
        oData["bairro"] := M->A1_BAIRRO
        oData["cidade"] := M->A1_MUN
        oData["estado"] := M->A1_EST
        oData["cep"] := M->A1_CEP
        
        // Contato
        oData["telefone"] := M->A1_TEL
        oData["email"] := M->A1_EMAIL
        oData["contato"] := M->A1_CONTATO
        
        // Dados comerciais
        oData["vendedor"] := M->A1_VEND
        oData["vendedor_nome"] := Posicione("SA3",1,xFilial("SA3")+M->A1_VEND,"A3_NOME")
        oData["tipo"] := Iif(M->A1_TIPO=="F", "Consumidor Final", "Solidário")
        
        WHSendEvent("cliente.novo", oData)
        
    EndIf
    
Return .T.
```

---

## 6. Automação com Zapier

### ⚡ Caso de Uso
Criar automaticamente cards no Trello quando um orçamento for aprovado.

### Passos:

1. **No Painel Webhook Hub:**
```
Nome: Orçamento → Trello
Tipo de Evento: orcamento.aprovado
Destino: Custom Webhook
URL: [URL gerada pelo Zapier]
```

2. **No Zapier:**
   - Trigger: Webhooks by Zapier (Catch Hook)
   - Action: Trello (Create Card)
   
3. **Código ADVPL:**

```advpl
User Function ORCAPROV()
    Local oData := JsonObject():new()
    
    oData["numero_orcamento"] := SCJ->CJ_NUM
    oData["cliente"] := SCJ->CJ_CLIENTE
    oData["cliente_nome"] := Posicione("SA1",1,xFilial("SA1")+SCJ->CJ_CLIENTE+SCJ->CJ_LOJA,"A1_NOME")
    oData["valor"] := SCJ->CJ_XTOTAL
    oData["prazo_entrega"] := DtoC(SCJ->CJ_XPRAZO)
    oData["observacoes"] := SCJ->CJ_OBS
    
    WHSendEvent("orcamento.aprovado", oData)
    
Return
```

---

## 🎯 Dicas de Performance

### Use Jobs para Verificações em Massa

```advpl
// Não faça verificações síncronas em loops grandes
// Use jobs agendados

User Function JOBCHECK()
    StartJob("U_PROCESSA", GetEnvServer(), .F.)
Return
```

### Agrupe Notificações

```advpl
// Em vez de enviar 100 webhooks, agrupe em um resumo
User Function RESUMO()
    Local oData := JsonObject():new()
    Local aItens := {}
    
    // Coleta dados
    While !EOF()
        aAdd(aItens, {"item": campo1, "valor": campo2})
        DbSkip()
    End
    
    oData["total_itens"] := Len(aItens)
    oData["itens"] := aItens
    
    WHSendEvent("resumo.diario", oData)
Return
```

---

## 📊 Monitoramento

### Verifique Logs Regularmente

```bash
# Ver logs do worker
docker-compose logs -f worker

# Ver apenas erros
docker-compose logs worker | grep "❌"
```

### Dashboard de Estatísticas

Acesse: http://localhost:4200

- Total de eventos enviados
- Taxa de sucesso
- Eventos na fila
- Configurações ativas

---

## 🆘 Troubleshooting

### Evento não chegou no destino

1. Verifique logs no painel
2. Teste a URL manualmente:
```bash
curl -X POST https://sua-url-webhook \
  -H "Content-Type: application/json" \
  -d '{"text":"teste"}'
```

### Performance lenta

1. Aumente workers no docker-compose.yml:
```yaml
worker:
  deploy:
    replicas: 3
```

---

**💡 Tem mais ideias de uso? Contribua no GitHub!**

[Fernando Vernier](https://github.com/ftvernier/erp-solutions)
