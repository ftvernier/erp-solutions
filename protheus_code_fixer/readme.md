# 🛠️ Protheus Code Fixer - Release 2510

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![TOTVS](https://img.shields.io/badge/TOTVS-Release%202510-red.svg)](https://tdn.totvs.com/)

> **Ferramenta automatizada para adaptar código ADVPL/TLPP ao Release 2510 do Protheus**

Identifica e corrige automaticamente atribuições diretas às variáveis `cEmpAnt` e `__cUserId` que foram bloqueadas por motivos de segurança no Protheus 12.1.2510.

![Screenshot da aplicação](https://via.placeholder.com/800x500.png?text=Protheus+Code+Fixer+Screenshot)

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [O Problema](#-o-problema)
- [A Solução](#-a-solução)
- [Funcionalidades](#-funcionalidades)
- [Instalação](#-instalação)
- [Como Usar](#-como-usar)
- [Exemplos](#-exemplos)
- [Roadmap](#-roadmap)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)
- [Contato](#-contato)

---

## 🎯 Sobre o Projeto

A partir do **Release 12.1.2510 do Protheus**, a TOTVS bloqueou a atribuição direta às variáveis globais `cEmpAnt` e `__cUserId` por motivos de segurança e integridade de dados. Essa mudança impacta diretamente códigos legados que utilizavam essa prática.

O **Protheus Code Fixer** automatiza o processo de:
1. ✅ **Identificação** de código incompatível
2. ✅ **Análise** detalhada dos problemas
3. ✅ **Geração automática** de código corrigido seguindo as boas práticas da TOTVS

---

## ⚠️ O Problema

### Código que **NÃO funciona mais** no Release 2510:

```advpl
User Function MinhaRotina()
    Local cEmpBkp := cEmpAnt
    
    cEmpAnt := "02"  // ❌ BLOQUEADO!
    
    // Processamento
    MsExecAuto(...)
    
    cEmpAnt := cEmpBkp  // ❌ BLOQUEADO!
Return
```

### Por que foi bloqueado?

- **Inconsistência de Dados**: Alteração direta não garantia que todas as tabelas refletissem a mudança
- **Falhas de Segurança**: Permitia execução de operações em escopo não autorizado
- **Problemas com Parâmetros**: Tabelas como SX6 permaneciam no contexto incorreto

---

## ✅ A Solução

### Código corrigido automaticamente pela ferramenta:

```advpl
User Function MinhaRotina()
    // Correcao aplicada conforme documentacao TOTVS Release 2510
    // Secao: 1. Rotinas ADVPL em Geral
    StartJob("U_MinhaRotinaJob", GetEnvServer(), .F., "02", cFilAnt)
Return .T.

Static Function U_MinhaRotinaJob(cEmp, cFil)
    RPCSetEnv(cEmp, cFil)
    
    // Processamento
    MsExecAuto(...)
    
    RPCClearEnv()
Return .T.
```

---

## 🚀 Funcionalidades

### 📊 Interface Gráfica Intuitiva

- **3 Abas de Visualização**:
  - 📊 **Resumo**: Visão consolidada por arquivo
  - 🔍 **Detalhes**: Lista completa de problemas linha a linha
  - 📝 **Relatório**: Texto formatado exportável

### 🔍 Análise Inteligente

- ✅ Varredura recursiva de diretórios
- ✅ Suporte a arquivos `.prw` e `.tlpp`
- ✅ Detecção de atribuições diretas
- ✅ Ignora comentários automaticamente
- ✅ Identifica contexto da função
- ✅ Extrai valores sendo atribuídos

### 🔧 Correção Automática

- ✅ Gera arquivos `_FIXED.prw` com código corrigido
- ✅ Preserva arquivos originais (não sobrescreve)
- ✅ Segue **exatamente** a documentação oficial TOTVS
- ✅ Aplica padrões para diferentes cenários:
  - **Cenário 1**: `cEmpAnt` → `StartJob` + `RPCSetEnv`
  - **Cenário 2**: `__cUserId` → Sistema de tokens
- ✅ Adiciona comentários explicativos
- ✅ Marca TODOs para revisão manual

### 📤 Exportação de Relatórios

- ✅ Relatórios em formato `.txt`
- ✅ Estatísticas detalhadas
- ✅ Lista completa de arquivos e linhas problemáticas

---

## 💻 Instalação

### Pré-requisitos

- Python 3.7 ou superior
- tkinter (geralmente já vem com Python)

### Passo a Passo

1. **Clone o repositório**:
```bash
git clone https://github.com/seu-usuario/protheus-code-fixer.git
cd protheus-code-fixer
```

2. **Nenhuma dependência adicional necessária!** 🎉

A ferramenta usa apenas bibliotecas padrão do Python.

---

## 🎮 Como Usar

### 1. Execute a aplicação:

```bash
python protheus_code_fixer.py
```

### 2. Interface gráfica:

1. **Selecione o diretório** dos seus fontes Protheus
2. **Escolha as extensões** (.PRW e/ou .TLPP)
3. **Clique em "Analisar"**
4. **Revise os resultados** nas 3 abas
5. **Duplo clique** em qualquer problema para ver sugestão detalhada
6. **Clique em "Gerar Correções"** para criar arquivos `_FIXED`
7. **Revise o código gerado** antes de usar em produção

### 3. Exemplo de uso via linha de comando:

```bash
# Analisar diretório específico
python protheus_code_fixer.py

# A interface gráfica será aberta automaticamente
```

---

## 📚 Exemplos

### Exemplo 1: Atribuição a cEmpAnt

**Código Original** (linha 34 de `ALTFIL.PRW`):
```advpl
cEmpAnt := cEmpBkp
```

**Código Gerado**:
```advpl
User Function ALTFIL()
    StartJob("U_ALTFILJob", GetEnvServer(), .F., cEmpBkp, cFilAnt)
Return .T.

Static Function U_ALTFILJob(cEmp, cFil)
    RPCSetEnv(cEmp, cFil)
    // TODO: Mover codigo original aqui
    RPCClearEnv()
Return .T.
```

### Exemplo 2: Atribuição a __cUserId

**Código Original**:
```advpl
__cUserId := "000000"
```

**Código Gerado**:
```advpl
User Function MinhaFunc()
    Local cToken := totvs.framework.users.rpc.getAuthToken()
    StartJob("U_MinhaFuncJob", GetEnvServer(), .F., cToken)
Return .T.

Static Function U_MinhaFuncJob(cToken)
    totvs.framework.users.rpc.authByToken(cToken)
    // TODO: Mover codigo original aqui
Return .T.
```

---

## 📊 Estatísticas de Análise

A ferramenta fornece estatísticas detalhadas:

```
⚠️ 5 problemas encontrados em 3 arquivo(s)
├── cEmpAnt: 3 ocorrências
└── __cUserId: 2 ocorrências

📄 Arquivos afetados:
├── ALTFIL.PRW (2 problemas)
├── InnJobs.tlpp (2 problemas)
└── GPEWORK.PRW (1 problema)
```

---

## 🗺️ Roadmap

### ✅ Versão 1.0 (Atual)
- [x] Interface gráfica
- [x] Análise de código
- [x] Geração automática de correções
- [x] Exportação de relatórios
- [x] Suporte UTF-8

---

## 🤝 Contribuindo

Contribuições são **muito bem-vindas**! 

### Como contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: nova funcionalidade incrível'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Diretrizes:

- ✅ Código Python limpo e documentado
- ✅ Seguir PEP 8
- ✅ Adicionar testes quando possível
- ✅ Atualizar documentação

---

## 📖 Documentação Oficial TOTVS

Este projeto segue **100%** a documentação oficial da TOTVS sobre as mudanças no Release 2510:

- [TDN TOTVS - Restrições Release 2510](https://tdn.totvs.com/)

### Cenários cobertos pela ferramenta:

1. ✅ **Rotinas ADVPL em Geral** → `StartJob` + `RPCSetEnv`
2. ✅ **Transferência de Credenciais** → Sistema de tokens
3. 📝 **Webservices REST** → Documentação (não requer correção de código)
4. 📝 **Webservices SOAP** → Documentação (configuração AppServer.ini)

---

## ⚖️ Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---

## 💬 Conecte-se Comigo

Gostou do conteúdo? Vamos conversar sobre integração de sistemas, arquitetura de software e transformação digital!

- 💼 **LinkedIn**: [Fernando Vernier](https://www.linkedin.com/in/fernando-v-10758522/)
- 📧 **Email**: fernando.vernier@hotmail.com
- 💻 **GitHub**: [github.com/ftvernier/erp-solutions](https://github.com/ftvernier/erp-solutions)

### 🤝 Apoie Este Projeto

Se este conteúdo agregou valor para você ou sua empresa, considere apoiar o projeto:

💵 **PIX**: `fernandovernier@gmail.com`

---

## 🙏 Agradecimentos

- TOTVS pela documentação clara do Release 2510
- Comunidade ADVPL/TLPP
- Todos os contribuidores do projeto

---


## ⭐ Mostre seu apoio

Se este projeto foi útil para você, considere dar uma ⭐️!

---

<div align="center">

**Desenvolvido com ❤️ para a comunidade TOTVS Protheus**

[⬆ Voltar ao topo](#-protheus-code-fixer---release-2510)

</div>
