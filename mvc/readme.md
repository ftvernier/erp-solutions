# 🚀 Gerador MVC - Protheus

Uma ferramenta web moderna para gerar código AdvPL MVC de forma rápida e eficiente, baseada na documentação oficial da TOTVS.

## 🌐 Acesso Direto

**[➡️ Usar a Ferramenta Online](https://erp-mvc-generator.netlify.app/)**

## 📋 Sobre

O Gerador MVC é uma ferramenta desenvolvida para acelerar o desenvolvimento de aplicações AdvPL utilizando o padrão MVC (Model-View-Controller) no ERP Protheus. Com uma interface intuitiva e moderna, permite gerar código estruturado seguindo as melhores práticas da TOTVS.

## ✨ Características

### Tipos de Modelo Suportados
- **Uma Entidade**: Modelo simples com apenas uma tabela (cadastros básicos)
- **Master-Detail (1 Tabela)**: Tabela não normalizada com cabeçalho e itens
- **Master-Detail (2 Tabelas)**: Duas tabelas relacionadas em estrutura pai-filho

### Recursos da Interface
- 🎨 Interface moderna e responsiva
- ⚡ Geração de código em tempo real
- 🔍 Validações básicas de entrada
- 📱 Compatível com dispositivos móveis
- 🎯 Configuração visual de relacionamentos
- 📊 Opções avançadas organizadas em abas

## 🛠️ Funcionalidades Geradas

### Código Completo MVC
- **Browse Principal**: FWMBrowse configurado
- **MenuDef**: Menu completo com todas as operações (CRUD)
- **ModelDef**: Modelo de dados com validações
- **ViewDef**: Interface responsiva e funcional
- **Funções de Validação**: Templates para validações personalizadas

### Recursos Avançados
- Relacionamentos entre tabelas
- Filtros de browse
- Chaves primárias personalizadas
- Títulos de componentes
- Layout configurável (percentuais de tela)
- Comentários e documentação integrada

## ⚠️ Limitações Importantes

**Esta ferramenta gera um ponto de partida para desenvolvimento**. O código gerado requer revisão e adaptação antes do uso em produção:

- ✅ **Dicionário de dados**: Assume que as tabelas estão definidas no SX3
- ✅ **Relacionamentos**: Configure corretamente os relacionamentos entre tabelas  
- ✅ **Validações**: Adicione validações de negócio específicas
- ✅ **Testes**: Sempre teste em ambiente de desenvolvimento primeiro
- ✅ **Personalização**: Adapte o código às necessidades específicas do projeto

## 🚀 Como Usar

1. **Acesse a ferramenta**: [https://erp-mvc-generator.netlify.app/](https://erp-mvc-generator.netlify.app/)

2. **Configure os dados básicos**:
   - Nome da função (ex: COMP011_MVC)
   - ID do modelo (ex: COMP011M)  
   - Descrição da aplicação

3. **Selecione o tipo de modelo**:
   - Escolha entre 1 entidade ou Master-Detail

4. **Configure as tabelas**:
   - Defina tabela master e detail (se aplicável)
   - Configure relacionamentos

5. **Opções avançadas**:
   - Filtros, validações e interface

6. **Gere e copie o código**:
   - Revise o código gerado
   - Adapte conforme necessário
   - Teste em ambiente de desenvolvimento

## 📚 Documentação Base

Esta ferramenta foi desenvolvida baseada na documentação oficial:
- Manual AdvPL utilizando MVC (TOTVS)
- Melhores práticas de desenvolvimento Protheus
- Padrões da comunidade AdvPL

## 🔧 Tecnologias Utilizadas

- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Design**: Interface moderna com gradientes e animações
- **Responsividade**: Layout adaptativo para todos os dispositivos
- **Deploy**: Netlify

## 💡 Exemplos de Uso

### Cadastro Simples (1 Entidade)
```advpl
// Exemplo: Cadastro de Clientes
Função: ZCLIENTE_MVC
Tabela: ZA1 (Master)
Tipo: Uma Entidade
```

### Master-Detail (2 Tabelas)
```advpl
// Exemplo: Pedidos de Venda
Função: ZPEDIDO_MVC  
Tabela Master: ZA1 (Cabeçalho)
Tabela Detail: ZA2 (Itens)
Relacionamento: ZA2_PEDIDO -> ZA1_NUMERO
```

## 📦 Instalação Local

Para executar localmente:

```bash
# Clone o repositório
git clone https://github.com/ftvernier/erp-solutions.git

# Navegue até a pasta da ferramenta
cd erp-solutions/mvc-generator

# Abra o index.html em um navegador
# Ou use um servidor local como Live Server (VS Code)
```

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:

- Reportar bugs
- Sugerir melhorias
- Propor novas funcionalidades
- Submeter pull requests

## 📄 Checklist Pós-Geração

Após gerar o código, sempre verifique:

- [ ] Tabelas existem no dicionário SX3
- [ ] Relacionamentos entre tabelas estão corretos  
- [ ] Campos de chave primária existem
- [ ] Implementar validações de negócio específicas
- [ ] Testar todas as operações (CRUD)
- [ ] Verificar permissões de acesso
- [ ] Documentar customizações adicionais

## 🎯 Projeto ERP Solutions

Esta ferramenta faz parte do projeto **ERP Solutions**, focado em automação e simplificação de processos relacionados ao ERP Protheus.

### Outros Projetos
- Validador de XML para documentos fiscais
- Utilitários de desenvolvimento AdvPL
- Scripts de automação

## 👨‍💻 Autor

**Fernando Vernier**
- 💼 [LinkedIn](https://www.linkedin.com/in/fernando-v-10758522/)
- 🌐 [GitHub](https://github.com/ftvernier)

---

## 📜 Licença

Este projeto é open source e está disponível sob a [MIT License](LICENSE).

---

**⚠️ Aviso Legal**: Esta ferramenta é fornecida "como está" sem garantias. O código gerado deve ser revisado e testado antes do uso em produção. O autor não se responsabiliza por problemas decorrentes do uso inadequado da ferramenta.
