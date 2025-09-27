# Protheus Doc Generator

> Ferramenta web para gerar documentação padronizada em Markdown para soluções ERP Protheus

[![Netlify Status](https://api.netlify.com/api/v1/badges/your-site-id/deploy-status)](https://erp-md-generator.netlify.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Sobre o Projeto

O **Protheus Doc Generator** resolve um dos maiores gargalos no desenvolvimento ERP Protheus: a documentação. Com uma interface web intuitiva, permite criar documentação profissional em formato Markdown de forma rápida e padronizada.

**🔗 Acesse a ferramenta:** [erp-md-generator.netlify.app](https://erp-md-generator.netlify.app/)

## ⚡ Funcionalidades

### 📝 Três Tipos de Documentação
- **Função ADVPL**: Documenta funções com parâmetros, tipos, retornos e exemplos
- **Customização**: Para projetos completos de customização do Protheus
- **Integração**: Para APIs, WebServices e integrações entre sistemas

### 🛠️ Recursos Principais
- ✅ **Templates específicos** para o universo Protheus
- ✅ **Preview em tempo real** das documentações
- ✅ **Tipos de dados ADVPL** (Caracter, Numérico, Lógico, Data, Array, Objeto)
- ✅ **Exportação flexível** (copiar ou baixar arquivo .md)
- ✅ **Interface responsiva** que funciona em qualquer dispositivo
- ✅ **Validação de campos** obrigatórios

## 🚀 Como Usar

1. **Acesse a ferramenta** em [erp-md-generator.netlify.app](https://erp-md-generator.netlify.app/)
2. **Escolha o tipo** de documentação (Função, Customização ou Integração)
3. **Preencha os campos** necessários no formulário
4. **Visualize o preview** em tempo real
5. **Exporte** copiando para clipboard ou baixando o arquivo .md

## 📖 Exemplos de Uso

### Documentando uma Função ADVPL

```markdown
# U_VALIDAPEDIDO

## 📋 Descrição
Função para validar pedidos de venda antes da liberação

## ℹ️ Informações
| Campo | Valor |
|-------|-------|
| **Autor** | Fernando Vernier |
| **Desde** | 01/12/2024 |
| **Categoria** | Função |

## 📥 Parâmetros
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|----------|
| `cNumPed` | C | ✅ Sim | Número do pedido de venda |
| `nTpValid` | N | ❌ Não | Tipo de validação |

## 💻 Exemplo de Uso
```advpl
Local lValid := U_VALIDAPEDIDO("000001", 2)
If lValid
    Alert("Pedido válido!")
EndIf
```

### Documentando uma Customização

A ferramenta gera documentação estruturada incluindo:
- Informações do projeto (desenvolvedor, cliente, data)
- Módulos afetados
- Detalhes da implementação
- Cenários de teste realizados
- Observações importantes

### Documentando uma Integração

Para integrações, inclui:
- Informações técnicas (método, endpoint)
- Sistemas integrados
- Fluxo de dados
- Método de autenticação
- Estratégias de monitoramento

## 🎨 Interface

A ferramenta possui design moderno e intuitivo, inspirado nas melhores práticas de UX:

- **Abas organizadas** para cada tipo de documentação
- **Formulários inteligentes** com validação em tempo real
- **Preview instantâneo** para ver o resultado antes de exportar
- **Botões de ação** para copiar ou baixar a documentação

## 🔧 Tecnologias

- **HTML5** + **CSS3** + **JavaScript Vanilla**
- **Design Responsivo** com CSS Grid e Flexbox
- **Sem dependências externas** - funciona offline após carregamento
- **Deploy no Netlify** para alta disponibilidade

## 📈 Benefícios

### Para Desenvolvedores
- ⏱️ **Economia de tempo**: Reduz drasticamente o tempo gasto com documentação
- 📏 **Padronização**: Garante consistência em todos os projetos
- 🎯 **Foco no código**: Menos tempo formatando, mais tempo desenvolvendo

### Para Equipes
- 📚 **Conhecimento compartilhado**: Documentação padronizada facilita o onboarding
- 🔍 **Facilita manutenção**: Código bem documentado é mais fácil de manter
- 📊 **Melhores práticas**: Força o preenchimento de informações importantes

### Para Comunidade
- 🤝 **Compartilhamento**: Documentação pronta para GitHub e repositórios
- 📖 **Legibilidade**: Formato Markdown amplamente adotado
- 🌟 **Qualidade**: Eleva o padrão da documentação Protheus

## 🤝 Contribuição

Este projeto faz parte do **ERP Solutions**, iniciativa focada em automação e simplificação de processos relacionados ao ERP Protheus.

### Como Contribuir
- 🐛 **Reporte bugs** ou problemas encontrados
- 💡 **Sugira melhorias** ou novas funcionalidades
- 📖 **Compartilhe** a ferramenta com outros desenvolvedores
- ⭐ **Avalie** o projeto no GitHub

## 📞 Contato

**Fernando Vernier**
- 🔗 **GitHub**: [erp-solutions](https://github.com/ftvernier/erp-solutions)
- 💼 **LinkedIn**: [fernando-v-10758522](https://www.linkedin.com/in/fernando-v-10758522/)
- 📧 **Email**: fernando.vernier@hotmail.com

## 🏷️ Agradecimentos

Ferramenta desenvolvida atendendo sugestão do **Guilherme Leonel**, demonstrando como a colaboração da comunidade Protheus pode gerar soluções práticas e eficientes.

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

**💡 "Transformando complexidade em simplicidade através do ERP Protheus"**

Feito com dedicação por [Fernando Vernier](https://github.com/ftvernier) - ERP Solutions
