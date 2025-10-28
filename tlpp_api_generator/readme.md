# 🚀 Gerador de APIs TLPP - Protheus

> **Crie APIs REST modernas com TLPP e annotations de forma automática**

Uma ferramenta web interativa que gera código TLPP (TOTVS Language Plus Plus) para criação de APIs REST no Protheus, incluindo documentação Swagger automática e código para consumo de APIs externas.

Acesse: [[https://ftvernier.github.io/erp-solutions/](https://api-tlpp-generator.netlify.app)](https://api-tlpp-generator.netlify.app)

## ✨ Funcionalidades

### 🎯 Geração de APIs REST
- **Operações CRUD Completas**: GET (único e listagem), POST, PUT, DELETE
- **Paginação Inteligente**: Implementação automática de paginação nos endpoints de listagem
- **Múltiplos Métodos de Gravação**:
  - MSExecAuto (Recomendado)
  - MVC (Moderno) 
  - RecLock (Manual)
- **Documentação Swagger**: Geração automática de documentação OpenAPI 3.0

### 🔧 Consumidor de APIs
- **Cliente FWRest**: Código para consumir APIs externas
- **Múltiplos Métodos HTTP**: GET, POST, PUT, DELETE
- **Configuração Completa**: Headers, User-Agent, Content-Type, Body

### 📋 Templates Prontos
- **Produtos (SB1)** - MATA010
- **Clientes (SA1)** - MATA030  
- **Pedidos (SC5)** - MATA410
- **Fornecedores (SA2)** - MATA020

## 🖥️ Interface

### Configurações da API
- Nome da API e endpoint personalizáveis
- Seleção de operações REST necessárias
- Configuração da tabela principal e campos
- Escolha do método de gravação (MSExecAuto/MVC/RecLock)
- Opções para paginação e documentação

### Código Gerado
- Visualização em tempo real do código TLPP
- Estatísticas: linhas de código, métodos, tempo economizado
- Estrutura de arquivos sugerida
- Funcionalidades de cópia e download

## 🏗️ Estrutura do Código Gerado

```
src/
├── api_produtos.tlpp           # Classe principal da API
├── swagger_produtos.json       # Documentação OpenAPI (opcional)
└── components_produtos.tlpp    # Componentes auxiliares
```

### Exemplo de Código Gerado (Produtos)

```tlpp
#Include "tlpp-core.th"
#Include "tlpp-rest.th"
#Include "tlpp-doc.th"

Using Namespace tlpp.core

Class ProdutosAPI
    Public Method New() Constructor
    Public Method GetById()
    Public Method GetAll()
    Public Method Post()
    Public Method Put()
    Public Method Delete()
EndClass

@Get("/api/v1/produtos", description="API para gerenciamento de produtos - Listagem com paginação")
Method GetAll() Class ProdutosAPI
    Local oResponse := JsonObject():New()
    Local aData     := {}
    Local nLimit    := Val(oRest:getQueryRequest("limit"))
    Local nPage     := Val(oRest:getQueryRequest("page"))
    // ... implementação completa
Return .T.
```

## 🚀 Como Usar

### 1. Configuração Básica
1. Abra o arquivo `tlpp_api_generator.html` no navegador
2. Preencha o nome da API e descrição
3. Configure o endpoint (ex: `/api/v1/produtos`)
4. Selecione a tabela principal (ex: `SB1`)

### 2. Seleção de Operações
Marque as operações REST necessárias:
- ✅ **GET Único**: Busca por ID
- ✅ **GET Todos**: Listagem com paginação
- ✅ **POST**: Criação de registros
- ✅ **PUT**: Alteração de registros
- ✅ **DELETE**: Exclusão de registros

### 3. Método de Gravação

#### MSExecAuto (Recomendado)
```tlpp
// Configure a rotina ExecAuto
Private lMsErroAuto := .F.
Private aRotAuto    := {}

aAdd(aRotAuto, {"B1_COD", jBody["b1_cod"], Nil})
aAdd(aRotAuto, {"B1_DESC", jBody["b1_desc"], Nil})

MSExecAuto({|x,y| MATA010(x,y)}, aRotAuto, 3)
```

#### MVC (Moderno)
```tlpp
// Configuração para modelos MVC
Local oModel := FwLoadModel("MATA010")
oModel:SetOperation(MODEL_OPERATION_INSERT)
oModel:SetValue("SB1MASTER", "B1_COD", jBody["b1_cod"])
```

### 4. Configuração de Campos
Liste os campos da tabela (um por linha):
```
B1_COD
B1_DESC
B1_UM
B1_GRUPO
B1_TIPO
```

### 5. Gerar e Usar o Código
1. Clique em **"Gerar Código TLPP"**
2. Copie o código ou faça download
3. Compile no Protheus
4. Configure o endpoint no Application Server

## 📊 Consumidor de APIs

### Configuração
- **Nome da Função**: `xFWREST`
- **URL Base**: `https://api.exemplo.com`
- **Path**: `/produtos?id=123`
- **Método HTTP**: GET, POST, PUT, DELETE
- **Headers**: User-Agent, Content-Type, etc.

### Exemplo de Código Gerado
```tlpp
User Function xFWREST()
    Local aArea         := FWGetArea()
    Local cResultado    := ""
    Local aHeader       := {}
    Local oRestClient   := FWRest():New("https://api.exemplo.com")
    
    aAdd(aHeader, "User-Agent: Mozilla/4.0 (compatible; Protheus 12.1.x)")
    aAdd(aHeader, "Content-Type: application/json")
    
    oRestClient:setPath("/produtos")
    
    If oRestClient:Get(aHeader)
        cResultado := oRestClient:GetResult()
        ShowLog("Sucesso: " + cResultado)
    Else
        ShowLog("Erro: " + oRestClient:GetLastError())
    EndIf
    
    FWRestArea(aArea)
Return Nil
```

## 📚 Documentação Swagger

### Recursos Gerados
- **OpenAPI 3.0** completo
- **Schemas** automáticos baseados nos campos
- **Parâmetros** de paginação e path
- **Responses** padronizados com códigos HTTP
- **Exemplos** de request/response

### Estrutura da Documentação
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Produtos API",
    "description": "API para gerenciamento de produtos",
    "version": "1.0.0"
  },
  "paths": {
    "/api/v1/produtos": {
      "get": {
        "summary": "Listar todos os produtos",
        "parameters": [
          {
            "name": "page",
            "in": "query",
            "schema": { "type": "integer", "default": 1 }
          }
        ]
      }
    }
  }
}
```

## ⚙️ Características Técnicas

### Tecnologias Utilizadas
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Backend**: TLPP (TOTVS Language Plus Plus)
- **Documentação**: OpenAPI 3.0 (Swagger)
- **Estilo**: CSS3 com gradientes modernos

### Compatibilidade
- **Protheus**: 12.1.2210 ou superior
- **Navegadores**: Chrome, Firefox, Edge, Safari
- **TLPP**: Versões com suporte a REST annotations

### Recursos Implementados
- ✅ Annotations REST (@Get, @Post, @Put, @Delete)
- ✅ Paginação automática
- ✅ Tratamento de erros
- ✅ Validações de dados
- ✅ Response padronizado
- ✅ Documentação automática

## 📈 Estatísticas

A ferramenta calcula automaticamente:
- **Linhas de Código**: Total gerado
- **Métodos REST**: Quantidade de endpoints
- **Tempo Economizado**: Estimativa em horas

## 🎨 Interface Moderna

### Design Responsivo
- Layout adaptável para desktop e mobile
- Cards informativos com estatísticas
- Syntax highlighting para código
- Modal para visualização do Swagger

### Funcionalidades UX
- Templates prontos para uso imediato
- Preview em tempo real do código
- Download direto dos arquivos
- Cópia para clipboard

## 🤝 Contribuição

### Desenvolvido por
**Fernando Vernier**  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/fernando-v-10758522/)

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

**💡 Dica**: Use os templates prontos para começar rapidamente e personalize conforme suas necessidades!
