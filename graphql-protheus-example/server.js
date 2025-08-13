// =============================================
// GRAPHQL + PROTHEUS - EXEMPLO DIDÁTICO
// Simulação de Gateway GraphQL para Protheus
// =============================================

const { ApolloServer, gql } = require('apollo-server-express');
const express = require('express');

// =============================================
// 1. DADOS FICTÍCIOS (SIMULANDO PROTHEUS)
// =============================================

const dadosProtheus = {
  // Tabela SA1 - Clientes
  clientes: [
    {
      A1_COD: "000001",
      A1_LOJA: "01", 
      A1_NOME: "EMPRESA MODELO LTDA",
      A1_NREDUZ: "EMPRESA MODELO",
      A1_EMAIL: "contato@empresamodelo.com.br",
      A1_TEL: "(11) 9999-9999",
      A1_END: "RUA DAS FLORES, 123",
      A1_BAIRRO: "CENTRO",
      A1_MUN: "SAO PAULO",
      A1_EST: "SP",
      A1_CEP: "01234-567"
    },
    {
      A1_COD: "000002", 
      A1_LOJA: "01",
      A1_NOME: "DISTRIBUIDORA BRASIL S/A",
      A1_NREDUZ: "DIST BRASIL",
      A1_EMAIL: "vendas@distbrasil.com.br", 
      A1_TEL: "(21) 8888-8888",
      A1_END: "AV. BRASIL, 456",
      A1_BAIRRO: "COPACABANA", 
      A1_MUN: "RIO DE JANEIRO",
      A1_EST: "RJ",
      A1_CEP: "22000-000"
    }
  ],

  // Tabela SB1 - Produtos
  produtos: [
    {
      B1_COD: "PROD001",
      B1_DESC: "NOTEBOOK DELL INSPIRON 15",
      B1_UM: "PC",
      B1_PRV1: 2500.00,
      B1_GRUPO: "INFORMATICA",
      B1_MSBLQL: "2"
    },
    {
      B1_COD: "PROD002", 
      B1_DESC: "MOUSE WIRELESS LOGITECH",
      B1_UM: "PC",
      B1_PRV1: 89.90,
      B1_GRUPO: "INFORMATICA", 
      B1_MSBLQL: "2"
    },
    {
      B1_COD: "PROD003",
      B1_DESC: "TECLADO MECANICO RGB",
      B1_UM: "PC", 
      B1_PRV1: 299.90,
      B1_GRUPO: "INFORMATICA",
      B1_MSBLQL: "2"
    }
  ],

  // Tabela SA3 - Vendedores
  vendedores: [
    {
      A3_COD: "001",
      A3_NOME: "CARLOS SILVA",
      A3_EMAIL: "carlos.silva@empresa.com.br",
      A3_COMIS: 5.0
    },
    {
      A3_COD: "002", 
      A3_NOME: "MARIA SANTOS",
      A3_EMAIL: "maria.santos@empresa.com.br",
      A3_COMIS: 7.5
    }
  ],

  // Tabela SC5 - Pedidos de Venda
  pedidos: [
    {
      C5_NUM: "000001",
      C5_EMISSAO: "20241201", 
      C5_CLIENTE: "000001",
      C5_LOJACLI: "01",
      C5_VEND1: "001",
      C5_DESCONT: 0,
      C5_FRETE: 0,
      C5_DESPESA: 0,
      C5_SEGURO: 0,
      C5_LIBEROK: "S",
      C5_NOTA: "",
      C5_OBS: "PEDIDO DE TESTE - URGENTE"
    },
    {
      C5_NUM: "000002",
      C5_EMISSAO: "20241202",
      C5_CLIENTE: "000002", 
      C5_LOJACLI: "01",
      C5_VEND1: "002",
      C5_DESCONT: 100.00,
      C5_FRETE: 50.00,
      C5_DESPESA: 0,
      C5_SEGURO: 0,
      C5_LIBEROK: "S", 
      C5_NOTA: "",
      C5_OBS: "CLIENTE VIP - DESCONTO ESPECIAL"
    }
  ],

  // Tabela SC6 - Itens do Pedido
  itensPedido: [
    {
      C6_NUM: "000001",
      C6_ITEM: "01", 
      C6_PRODUTO: "PROD001",
      C6_QTDVEN: 2,
      C6_PRCVEN: 2500.00,
      C6_VALOR: 5000.00,
      C6_DESCONT: 0
    },
    {
      C6_NUM: "000001",
      C6_ITEM: "02",
      C6_PRODUTO: "PROD002", 
      C6_QTDVEN: 1,
      C6_PRCVEN: 89.90,
      C6_VALOR: 89.90,
      C6_DESCONT: 0
    },
    {
      C6_NUM: "000002",
      C6_ITEM: "01",
      C6_PRODUTO: "PROD003",
      C6_QTDVEN: 5, 
      C6_PRCVEN: 299.90,
      C6_VALOR: 1499.50,
      C6_DESCONT: 100.00
    }
  ]
};

// =============================================
// 2. SCHEMA GRAPHQL - TIPOS BASEADOS NO PROTHEUS
// =============================================

const typeDefs = gql`
  # Tipo Cliente (Baseado na SA1)
  type Cliente {
    codigo: String!
    loja: String!
    nome: String!
    nomeFantasia: String!
    email: String
    telefone: String
    endereco: String
    bairro: String
    cidade: String
    uf: String
    cep: String
    pedidos: [Pedido!]!
  }

  # Tipo Produto (Baseado na SB1)
  type Produto {
    codigo: String!
    descricao: String!
    unidade: String!
    preco: Float!
    grupo: String!
    ativo: Boolean!
  }

  # Tipo Vendedor (Baseado na SA3)
  type Vendedor {
    codigo: String!
    nome: String!
    email: String
    comissao: Float!
  }

  # Tipo Item do Pedido (Baseado na SC6)
  type ItemPedido {
    item: String!
    produto: Produto!
    quantidade: Int!
    preco: Float!
    valor: Float!
    desconto: Float!
  }

  # Tipo Pedido (Baseado na SC5)
  type Pedido {
    numero: String!
    emissao: String!
    cliente: Cliente!
    vendedor: Vendedor!
    itens: [ItemPedido!]!
    desconto: Float!
    frete: Float!
    total: Float!
    liberado: Boolean!
    observacao: String
  }

  # Tipo Dashboard - Agregação de dados
  type DashboardVendedor {
    vendedor: Vendedor!
    totalVendas: Float!
    quantidadePedidos: Int!
    ticketMedio: Float!
    pedidosRecentes: [Pedido!]!
  }

  # Queries disponíveis
  type Query {
    # Buscar pedido específico
    pedido(numero: String!): Pedido
    
    # Listar todos os pedidos
    pedidos: [Pedido!]!
    
    # Buscar cliente
    cliente(codigo: String!, loja: String!): Cliente
    
    # Listar todos os clientes
    clientes: [Cliente!]!
    
    # Buscar produto
    produto(codigo: String!): Produto
    
    # Listar todos os produtos
    produtos: [Produto!]!
    
    # Dashboard do vendedor
    dashboardVendedor(codigo: String!): DashboardVendedor
  }
`;

// =============================================
// 3. FUNÇÕES AUXILIARES (SIMULANDO CONSULTAS SQL)
// =============================================

// Simula consulta na SA1
function buscarCliente(codigo, loja) {
  return dadosProtheus.clientes.find(
    c => c.A1_COD === codigo && c.A1_LOJA === loja
  );
}

// Simula consulta na SB1
function buscarProduto(codigo) {
  return dadosProtheus.produtos.find(p => p.B1_COD === codigo);
}

// Simula consulta na SA3
function buscarVendedor(codigo) {
  return dadosProtheus.vendedores.find(v => v.A3_COD === codigo);
}

// Simula consulta na SC5
function buscarPedido(numero) {
  return dadosProtheus.pedidos.find(p => p.C5_NUM === numero);
}

// Simula consulta na SC6
function buscarItensPedido(numeroPedido) {
  return dadosProtheus.itensPedido.filter(i => i.C6_NUM === numeroPedido);
}

// Calcula total do pedido
function calcularTotalPedido(pedido) {
  const itens = buscarItensPedido(pedido.C5_NUM);
  const subtotal = itens.reduce((total, item) => total + item.C6_VALOR, 0);
  return subtotal + (pedido.C5_FRETE || 0) - (pedido.C5_DESCONT || 0);
}

// =============================================
// 4. RESOLVERS - LÓGICA DE NEGÓCIO
// =============================================

const resolvers = {
  Query: {
    // Buscar pedido específico
    pedido: (_, { numero }) => {
      const pedido = buscarPedido(numero);
      if (!pedido) {
        throw new Error(`Pedido ${numero} não encontrado`);
      }
      return pedido;
    },

    // Listar todos os pedidos
    pedidos: () => dadosProtheus.pedidos,

    // Buscar cliente
    cliente: (_, { codigo, loja }) => {
      const cliente = buscarCliente(codigo, loja);
      if (!cliente) {
        throw new Error(`Cliente ${codigo}/${loja} não encontrado`);
      }
      return cliente;
    },

    // Listar todos os clientes
    clientes: () => dadosProtheus.clientes,

    // Buscar produto
    produto: (_, { codigo }) => {
      const produto = buscarProduto(codigo);
      if (!produto) {
        throw new Error(`Produto ${codigo} não encontrado`);
      }
      return produto;
    },

    // Listar todos os produtos
    produtos: () => dadosProtheus.produtos,

    // Dashboard do vendedor
    dashboardVendedor: (_, { codigo }) => {
      const vendedor = buscarVendedor(codigo);
      if (!vendedor) {
        throw new Error(`Vendedor ${codigo} não encontrado`);
      }

      // Busca pedidos do vendedor
      const pedidosVendedor = dadosProtheus.pedidos.filter(
        p => p.C5_VEND1 === codigo
      );

      // Calcula estatísticas
      const totalVendas = pedidosVendedor.reduce(
        (total, pedido) => total + calcularTotalPedido(pedido), 0
      );
      
      const quantidadePedidos = pedidosVendedor.length;
      const ticketMedio = quantidadePedidos > 0 ? totalVendas / quantidadePedidos : 0;

      return {
        vendedor,
        totalVendas,
        quantidadePedidos,
        ticketMedio,
        pedidosRecentes: pedidosVendedor.slice(-5) // Últimos 5
      };
    }
  },

  // Resolvers para o tipo Pedido
  Pedido: {
    cliente: (pedido) => {
      return buscarCliente(pedido.C5_CLIENTE, pedido.C5_LOJACLI);
    },

    vendedor: (pedido) => {
      return buscarVendedor(pedido.C5_VEND1);
    },

    itens: (pedido) => {
      return buscarItensPedido(pedido.C5_NUM);
    },

    emissao: (pedido) => {
      // Converte YYYYMMDD para DD/MM/YYYY
      const data = pedido.C5_EMISSAO;
      return `${data.substr(6,2)}/${data.substr(4,2)}/${data.substr(0,4)}`;
    },

    total: (pedido) => {
      return calcularTotalPedido(pedido);
    },

    liberado: (pedido) => {
      return pedido.C5_LIBEROK === "S";
    },

    desconto: (pedido) => pedido.C5_DESCONT || 0,
    frete: (pedido) => pedido.C5_FRETE || 0,
    observacao: (pedido) => pedido.C5_OBS
  },

  // Resolvers para o tipo Cliente
  Cliente: {
    codigo: (cliente) => cliente.A1_COD,
    loja: (cliente) => cliente.A1_LOJA,
    nome: (cliente) => cliente.A1_NOME,
    nomeFantasia: (cliente) => cliente.A1_NREDUZ,
    email: (cliente) => cliente.A1_EMAIL,
    telefone: (cliente) => cliente.A1_TEL,
    endereco: (cliente) => cliente.A1_END,
    bairro: (cliente) => cliente.A1_BAIRRO,
    cidade: (cliente) => cliente.A1_MUN,
    uf: (cliente) => cliente.A1_EST,
    cep: (cliente) => cliente.A1_CEP,

    // Busca pedidos do cliente
    pedidos: (cliente) => {
      return dadosProtheus.pedidos.filter(
        p => p.C5_CLIENTE === cliente.A1_COD && p.C5_LOJACLI === cliente.A1_LOJA
      );
    }
  },

  // Resolvers para o tipo Produto
  Produto: {
    codigo: (produto) => produto.B1_COD,
    descricao: (produto) => produto.B1_DESC,
    unidade: (produto) => produto.B1_UM,
    preco: (produto) => produto.B1_PRV1,
    grupo: (produto) => produto.B1_GRUPO,
    ativo: (produto) => produto.B1_MSBLQL === "2"
  },

  // Resolvers para o tipo Vendedor
  Vendedor: {
    codigo: (vendedor) => vendedor.A3_COD,
    nome: (vendedor) => vendedor.A3_NOME,
    email: (vendedor) => vendedor.A3_EMAIL,
    comissao: (vendedor) => vendedor.A3_COMIS
  },

  // Resolvers para o tipo ItemPedido
  ItemPedido: {
    item: (item) => item.C6_ITEM,
    quantidade: (item) => item.C6_QTDVEN,
    preco: (item) => item.C6_PRCVEN,
    valor: (item) => item.C6_VALOR,
    desconto: (item) => item.C6_DESCONT || 0,

    produto: (item) => {
      return buscarProduto(item.C6_PRODUTO);
    }
  }
};

// =============================================
// 5. CONFIGURAÇÃO DO SERVIDOR
// =============================================

async function startServer() {
  // Cria servidor Apollo
  const server = new ApolloServer({
    typeDefs,
    resolvers,
    introspection: true,
    playground: true,
    formatError: (err) => {
      console.error('GraphQL Error:', err);
      return err;
    }
  });

  // Cria app Express
  const app = express();

  // Inicia o servidor Apollo
  await server.start();

  // Aplica middleware GraphQL
  server.applyMiddleware({ app, path: '/graphql' });

  const PORT = process.env.PORT || 4000;

  app.listen(PORT, () => {
    console.log('🚀 Servidor GraphQL rodando!');
    console.log(`📊 GraphQL Playground: http://localhost:${PORT}/graphql`);
    console.log('');
    console.log('📋 Queries de exemplo:');
    console.log('');
    console.log('# Buscar pedido completo:');
    console.log('{ pedido(numero: "000001") { numero emissao total cliente { nome } } }');
    console.log('');
    console.log('# Dashboard do vendedor:');
    console.log('{ dashboardVendedor(codigo: "001") { totalVendas quantidadePedidos } }');
    console.log('');
    console.log('# Lista otimizada para mobile:');
    console.log('{ pedidos { numero emissao total cliente { nome } } }');
  });
}

// =============================================
// 6. EXEMPLOS DE QUERIES COMENTADAS
// =============================================

/*
EXEMPLO 1: Query Simples - Lista de Pedidos (Mobile)
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

EXEMPLO 2: Query Completa - Detalhes do Pedido (Web)
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
      nome
      email
      telefone
      cidade
      uf
    }
    vendedor {
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
        grupo
      }
    }
  }
}

EXEMPLO 3: Dashboard Gerencial
{
  dashboardVendedor(codigo: "001") {
    vendedor {
      nome
      email
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
      }
    }
  }
}

EXEMPLO 4: Query Otimizada - Só o Necessário
{
  cliente(codigo: "000001", loja: "01") {
    nome
    telefone
    pedidos {
      numero
      total
    }
  }
}
*/

// Inicia o servidor
if (require.main === module) {
  startServer().catch(error => {
    console.error('Erro ao iniciar servidor:', error);
    process.exit(1);
  });
}

module.exports = { typeDefs, resolvers, dadosProtheus };
