#Include "Protheus.ch"
#Include "RestFul.ch"

/*/{Protheus.doc} WEBHUBLIB
    Biblioteca para integraÃ§Ã£o do Protheus com Webhook Hub
    
    @type Function
    @author Fernando Vernier
    @since 27/10/2025
    @version 1.0
    
    @example
    // Exemplo de uso:
    WHSendEvent("pedido.criado", JsonObject():new())
/*/

//-------------------------------------------------------------------
/*/{Protheus.doc} WHSendEvent
    Envia um evento para o Webhook Hub
    
    @type Function
    @param cEventType - Tipo do evento (ex: "pedido.criado", "nfe.emitida")
    @param oData - Objeto JSON com os dados do evento
    @return lSuccess - Indica se o envio foi bem sucedido
    
    @example
    Local oData := JsonObject():new()
    oData["numero_pedido"] = SC5->C5_NUM
    oData["cliente"] = SC5->C5_CLIENTE
    oData["valor_total"] = SC5->C5_TOTAL
    
    WHSendEvent("pedido.criado", oData)
/*/
//-------------------------------------------------------------------
Function WHSendEvent(cEventType, oData)
    Local lSuccess := .F.
    Local oRestClient
    Local oPayload
    Local cUrl := GetMV("MV_WEBHURL", .F., "http://localhost:8000")
    Local cEndpoint := cUrl + "/webhook"
    Local cResponse := ""
    Local nStatus := 0
    
    // Valida parÃ¢metros
    If Empty(cEventType)
        ConOut("[WEBHOOK HUB] Erro: Tipo de evento nÃ£o informado")
        Return .F.
    EndIf
    
    If ValType(oData) != "J"
        ConOut("[WEBHOOK HUB] Erro: Dados devem ser um objeto JSON")
        Return .F.
    EndIf
    
    // Cria payload
    oPayload := JsonObject():new()
    oPayload["event_type"] := cEventType
    oPayload["data"] := oData
    oPayload["source"] := "protheus"
    oPayload["timestamp"] := FWTimeStamp(3)
    
    // Cria cliente REST
    oRestClient := FWRest():New(cEndpoint)
    oRestClient:setPath("")
    
    // Define headers
    oRestClient:SetHeader("Content-Type", "application/json")
    
    // Envia requisiÃ§Ã£o POST
    lSuccess := oRestClient:Post(oPayload:toJson())
    
    If lSuccess
        nStatus := oRestClient:GetHTTPCode()
        cResponse := oRestClient:GetResult()
        
        If nStatus == 202
            ConOut("[WEBHOOK HUB] âœ“ Evento enviado: " + cEventType)
            lSuccess := .T.
        Else
            ConOut("[WEBHOOK HUB] âœ— Erro HTTP " + cValToChar(nStatus))
            ConOut("[WEBHOOK HUB] Response: " + cResponse)
            lSuccess := .F.
        EndIf
    Else
        ConOut("[WEBHOOK HUB] âœ— Erro ao conectar: " + oRestClient:GetLastError())
        lSuccess := .F.
    EndIf
    
Return lSuccess

//-------------------------------------------------------------------
/*/{Protheus.doc} WHPedidoCriado
    Exemplo de integraÃ§Ã£o - Envia evento quando pedido Ã© criado
    
    @type Function
    @example
    // No ponto de entrada MA410MNU ou apÃ³s gravaÃ§Ã£o do pedido:
    WHPedidoCriado()
/*/
//-------------------------------------------------------------------
Function WHPedidoCriado()
    Local oData := JsonObject():new()
    
    // Dados do pedido
    oData["numero_pedido"] := SC5->C5_NUM
    oData["tipo"] := SC5->C5_TIPO
    oData["cliente"] := SC5->C5_CLIENTE
    oData["loja"] := SC5->C5_LOJACLI
    oData["nome_cliente"] := Posicione("SA1", 1, xFilial("SA1") + SC5->C5_CLIENTE + SC5->C5_LOJACLI, "A1_NOME")
    oData["emissao"] := DtoC(SC5->C5_EMISSAO)
    oData["valor_total"] := SC5->C5_TOTAL
    oData["condicao_pagamento"] := SC5->C5_CONDPAG
    oData["vendedor"] := SC5->C5_VEND1
    oData["filial"] := cFilAnt
    
    // Envia evento
    WHSendEvent("pedido.criado", oData)
    
Return

//-------------------------------------------------------------------
/*/{Protheus.doc} WHNFeEmitida
    Exemplo de integraÃ§Ã£o - Envia evento quando NF-e Ã© emitida
    
    @type Function
    @example
    // No ponto de entrada apÃ³s emissÃ£o da nota:
    WHNFeEmitida()
/*/
//-------------------------------------------------------------------
Function WHNFeEmitida()
    Local oData := JsonObject():new()
    
    // Dados da nota fiscal
    oData["numero_nfe"] := SF2->F2_DOC
    oData["serie"] := SF2->F2_SERIE
    oData["cliente"] := SF2->F2_CLIENTE
    oData["loja"] := SF2->F2_LOJA
    oData["nome_cliente"] := Posicione("SA1", 1, xFilial("SA1") + SF2->F2_CLIENTE + SF2->F2_LOJA, "A1_NOME")
    oData["emissao"] := DtoC(SF2->F2_EMISSAO)
    oData["valor_total"] := SF2->F2_VALBRUT
    oData["chave_nfe"] := SF2->F2_CHVNFE
    oData["filial"] := cFilAnt
    
    // Envia evento
    WHSendEvent("nfe.emitida", oData)
    
Return

//-------------------------------------------------------------------
/*/{Protheus.doc} WHEstoqueBaixo
    Exemplo de integraÃ§Ã£o - Alerta de estoque baixo
    
    @type Function
    @example
    // Rotina para verificar estoque:
    WHEstoqueBaixo("000001", "01")
/*/
//-------------------------------------------------------------------
Function WHEstoqueBaixo(cProduto, cLocal)
    Local oData := JsonObject():new()
    Local nSaldo := 0
    Local nEstMin := 0
    
    Default cLocal := "01"
    
    // Posiciona no produto
    DbSelectArea("SB1")
    SB1->(DbSetOrder(1))
    If !SB1->(DbSeek(xFilial("SB1") + cProduto))
        Return
    EndIf
    
    // ObtÃ©m saldo
    DbSelectArea("SB2")
    SB2->(DbSetOrder(1))
    If SB2->(DbSeek(xFilial("SB2") + cProduto + cLocal))
        nSaldo := SaldoSB2()
    EndIf
    
    nEstMin := SB1->B1_EMIN
    
    // Verifica se estÃ¡ abaixo do mÃ­nimo
    If nSaldo < nEstMin
        oData["produto"] := cProduto
        oData["descricao"] := SB1->B1_DESC
        oData["local"] := cLocal
        oData["saldo_atual"] := nSaldo
        oData["estoque_minimo"] := nEstMin
        oData["diferenca"] := nEstMin - nSaldo
        oData["filial"] := cFilAnt
        
        // Envia alerta
        WHSendEvent("estoque.baixo", oData)
    EndIf
    
Return

//-------------------------------------------------------------------
/*/{Protheus.doc} WHClienteCadastrado
    Exemplo de integraÃ§Ã£o - Novo cliente cadastrado
    
    @type Function
    @example
    // No ponto de entrada apÃ³s inclusÃ£o de cliente:
    WHClienteCadastrado()
/*/
//-------------------------------------------------------------------
Function WHClienteCadastrado()
    Local oData := JsonObject():new()
    
    oData["codigo"] := SA1->A1_COD
    oData["loja"] := SA1->A1_LOJA
    oData["nome"] := SA1->A1_NOME
    oData["nome_fantasia"] := SA1->A1_NREDUZ
    oData["cnpj_cpf"] := SA1->A1_CGC
    oData["email"] := SA1->A1_EMAIL
    oData["telefone"] := SA1->A1_TEL
    oData["cidade"] := SA1->A1_MUN
    oData["estado"] := SA1->A1_EST
    oData["vendedor"] := SA1->A1_VEND
    oData["data_cadastro"] := DtoC(dDataBase)
    oData["filial"] := cFilAnt
    
    WHSendEvent("cliente.cadastrado", oData)
    
Return

//-------------------------------------------------------------------
/*/{Protheus.doc} WHTestConnection
    Testa a conexÃ£o com o Webhook Hub
    
    @type Function
    @return lSuccess - Indica se a conexÃ£o foi bem sucedida
    
    @example
    If WHTestConnection()
        MsgInfo("ConexÃ£o OK!")
    EndIf
/*/
//-------------------------------------------------------------------
Function WHTestConnection()
    Local lSuccess := .F.
    Local oRestClient
    Local cUrl := GetMV("MV_WEBHURL", .F., "http://localhost:8000")
    Local cEndpoint := cUrl + "/health"
    
    ConOut("[WEBHOOK HUB] Testando conexÃ£o: " + cEndpoint)
    
    oRestClient := FWRest():New(cEndpoint)
    oRestClient:setPath("")
    
    lSuccess := oRestClient:Get()
    
    If lSuccess
        ConOut("[WEBHOOK HUB] âœ“ ConexÃ£o bem sucedida!")
        ConOut("[WEBHOOK HUB] Response: " + oRestClient:GetResult())
    Else
        ConOut("[WEBHOOK HUB] âœ— Falha na conexÃ£o: " + oRestClient:GetLastError())
    EndIf
    
Return lSuccess

//-------------------------------------------------------------------
// INSTRUÃ‡Ã•ES DE INSTALAÃ‡ÃƒO
//-------------------------------------------------------------------
/*
1. Compile este fonte no Protheus
2. Configure o parÃ¢metro MV_WEBHURL com a URL da API
   Exemplo: http://192.168.1.100:8000
   
3. Teste a conexÃ£o:
   U_WHTestConnection()
   
4. Use nos pontos de entrada ou customizações
   
5. Exemplos de uso:
   
   // Após gravar pedido
   WHPedidoCriado()
   
   // Após emitir nota
   WHNFeEmitida()
   
   // Verificação de estoque (job/schedule)
   WHEstoqueBaixo("000001", "01")
   
   // Após cadastrar cliente
   WHClienteCadastrado()
   
   // Evento customizado
   Local oData := JsonObject():new()
   oData["info"] := "Meus dados"
   WHSendEvent("meu.evento", oData)
*/
