# 📋 Queries de Exemplo - GraphQL + Protheus

Este arquivo contém exemplos práticos de queries GraphQL que demonstram o poder e flexibilidade da tecnologia aplicada ao ecossistema Protheus.

## 🚀 **Como Usar**

1. Execute o servidor: `npm start`
2. Acesse: http://localhost:4000/graphql
3. Cole qualquer query abaixo no playground
4. Clique no botão ▶️ para executar

---

## 📱 **Queries para Mobile (Dados Mínimos)**

### **Lista de Pedidos Simples**
```graphql
{
  pedidos {
    numero
    emissao
    total
    cliente {
      nome
    }
  }
}
```

### **Lista de Clientes Básica**
```graphql
{
  clientes {
    codigo
    nome
    telefone
    cidade
  }
}
```

### **Produtos para Catálogo Mobile**
```graphql
{
  produtos {
    codigo
    descricao
    preco
    ativo
  }
}
```

---

## 🖥️ **Queries para Web (Dados Completos)**

### **Pedido Completo com Relacionamentos**
```graphql
{
  pedido(numero: "000001") {
    numero
    emissao
    total
    desconto
    frete
    liberado
    observacao
    cliente {
      codigo
      loja
      nome
      nomeFantasia
      email
      telefone
      endereco
      bairro
      cidade
      uf
      cep
    }
    vendedor {
      codigo
      nome
      email
      comissao
    }
    itens {
      item
      quantidade
      preco
      valor
      desconto
      produto {
        codigo
        descricao
        unidade
        preco
        grupo
        ativo
      }
    }
  }
}
```

### **Cliente com Histórico de Pedidos**
```graphql
{
  cliente(codigo: "000001", loja: "01") {
    codigo
    nome
    email
    telefone
    endereco
    cidade
    uf
    pedidos {
      numero
      emissao
      total
      liberado
      observacao
    }
  }
}
```

---

## 📊 **Queries para Dashboard**

### **Dashboard do Vendedor**
```graphql
{
  dashboardVendedor(codigo: "001") {
    vendedor {
      codigo
      nome
      email
      comissao
    }
    totalVendas
    quantidadePedidos
    ticketMedio
    pedidosRecentes {
      numero
      emissao
      total
      cliente {
        nome
        cidade
      }
    }
  }
}
```

### **Resumo Geral (Múltiplas Consultas)**
```graphql
{
  # Total de pedidos
  pedidos {
    numero
    total
  }
  
  # Total de clientes
  clientes {
    codigo
    nome
  }
  
  # Produtos ativos
  produtos {
    codigo
    descricao
    preco
  }
}
```

---

## 🎯 **Queries Otimizadas por Cenário**

### **Relatório de Vendas por Produto**
```graphql
{
  pedidos {
    numero
    emissao
    total
    itens {
      quantidade
      valor
      produto {
        codigo
        descricao
        grupo
      }
    }
  }
}
```

### **Lista de Contatos (CRM)**
```graphql
{
  clientes {
    codigo
    nome
    email
    telefone
    cidade
    uf
    pedidos {
      numero
      emissao
      total
    }
  }
}
```

### **Análise de Performance de Vendedores**
```graphql
{
  dashboardVendedor(codigo: "001") {
    vendedor {
      nome
    }
    totalVendas
    quantidadePedidos
    ticketMedio
  }
  
  # Repita para outros vendedores se necessário
}
```

---

## 🔍 **Queries Específicas (Busca)**

### **Buscar Produto Específico**
```graphql
{
  produto(codigo: "PROD001") {
    codigo
    descricao
    unidade
    preco
    grupo
    ativo
  }
}
```

### **Buscar Pedido Específico**
```graphql
{
  pedido(numero: "000001") {
    numero
    emissao
    total
    liberado
    cliente {
      nome
    }
  }
}
```

### **Buscar Cliente Específico**
```graphql
{
  cliente(codigo: "000001", loja: "01") {
    codigo
    nome
    email
    telefone
    endereco
    pedidos {
      numero
      total
    }
  }
}
```

---

## ⚡ **Queries com Fragments (Reutilização)**

### **Definindo Fragments**
```graphql
fragment ClienteBasico on Cliente {
  codigo
  loja
  nome
  email
  telefone
}

fragment ProdutoBasico on Produto {
  codigo
  descricao
  preco
  ativo
}

# Usando os fragments
{
  pedido(numero: "000001") {
    numero
    total
    cliente {
      ...ClienteBasico
    }
    itens {
      quantidade
      valor
      produto {
        ...ProdutoBasico
      }
    }
  }
}
```

---

## 🏷️ **Queries com Aliases (Múltiplas Consultas)**

```graphql
{
  # Pedido 1
  pedido1: pedido(numero: "000001") {
    numero
    total
    cliente {
      nome
    }
  }
  
  # Pedido 2
  pedido2: pedido(numero: "000002") {
    numero
    total
    cliente {
      nome
    }
  }
  
  # Lista de produtos
  catalogoProdutos: produtos {
    codigo
    descricao
    preco
  }
}
```

---

## 📈 **Comparação: REST vs GraphQL**

### **❌ Abordagem REST (Múltiplas Chamadas)**
```bash
# Para obter dados de um pedido completo:
GET /api/pedidos/000001
GET /api/clientes/000001/01  
GET /api/vendedores/001
GET /api/pedidos/000001/itens
GET /api/produtos/PROD001
GET /api/produtos/PROD002

# Total: 6+ requisições HTTP
```

### **✅ Abordagem GraphQL (Uma Chamada)**
```graphql
{
  pedido(numero: "000001") {
    numero
    total
    cliente { nome }
    vendedor { nome }
    itens {
      quantidade
      produto { descricao }
    }
  }
}

# Total: 1 requisição HTTP
```

---

## 🎨 **Queries para Diferentes Interfaces**

### **Interface Minimalista (Smartwatch)**
```graphql
{
  pedidos {
    numero
    total
  }
}
```

### **Interface Tablet (Dados Médios)**
```graphql
{
  pedidos {
    numero
    emissao
    total
    cliente {
      nome
      telefone
    }
    vendedor {
      nome
    }
  }
}
```

### **Interface Desktop (Dados Completos)**
```graphql
{
  pedidos {
    numero
    emissao
    total
    desconto
    frete
    liberado
    observacao
    cliente {
      codigo
      nome
      email
      telefone
      endereco
      cidade
      uf
    }
    vendedor {
      codigo
      nome
      email
      comissao
    }
    itens {
      item
      quantidade
      preco
      valor
      produto {
        codigo
        descricao
        unidade
        grupo
      }
    }
  }
}
```

---

## 🚀 **Dicas de Performance**

### **❌ Evite Queries Muito Profundas**
```graphql
# RUIM: Muito profundo
{
  pedidos {
    cliente {
      pedidos {
        cliente {
          pedidos {
            cliente {
              nome
            }
          }
        }
      }
    }
  }
}
```

### **✅ Prefira Queries Otimizadas**
```graphql
# BOM: Busca direta e objetiva
{
  pedidos {
    numero
    total
    cliente {
      nome
    }
  }
}
```

---

## 🔧 **Queries para Desenvolvimento**

### **Introspecção do Schema**
```graphql
{
  __schema {
    types {
      name
      description
    }
  }
}
```

### **Verificar Campos Disponíveis**
```graphql
{
  __type(name: "Pedido") {
    fields {
      name
      type {
        name
      }
    }
  }
}
```

---

## 📝 **Próximos Passos**

Estes exemplos cobrem as operações de **consulta (Query)**. Em versões futuras, pretendemos adicionar:

- **Mutations** (CREATE, UPDATE, DELETE)
- **Subscriptions** (dados em tempo real)
- **Paginação** para grandes volumes
- **Filtros e ordenação** avançados

---

**💡 Dica:** Experimente modificar essas queries no playground para entender como GraphQL oferece flexibilidade total sobre os dados retornados!

**🎯 Objetivo:** Demonstrar que com GraphQL você busca exatamente o que precisa, quando precisa, da forma que precisa!
