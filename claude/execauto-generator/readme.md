Faz alguns anos que trabalho com Protheus. Nesse tempo, vi o mesmo erro aparecer em bases diferentes, times diferentes, empresas diferentes.

Alguém precisava automatizar uma inclusão via código. Escrevia o ExecAuto, testava em desenvolvimento, funcionava. Subia para produção — e quebrava de um jeito difícil de reproduzir.

Na maioria das vezes, a causa era uma dessas:

→ BEGIN TRANSACTION em volta do MSExecAuto, concorrendo com o controle interno da própria rotina  
→ lMsErroAuto não resetado antes da chamada  
→ GetErrorMessage() sendo tratado como string, quando é um array de 9 posições  
→ PREPARE ENVIRONMENT dentro de Web Service, quando o ambiente já vem do AppServer.ini  
→ Confusão entre FWLoadModel + GetModel e FWMVCRotAuto — dois padrões MVC com usos diferentes

Não são bugs do Protheus. São detalhes que a documentação cobre, mas que ficam espalhados em artigos, fóruns e anos de experiência acumulada.

---

Recentemente comecei a usar Claude Code no meu fluxo de desenvolvimento. E percebi que, sem contexto específico do Protheus, ele cometia exatamente esses erros.

Não porque a ferramenta é ruim. Mas porque ExecAuto tem particularidades que não estão no treinamento de nenhum modelo.

A solução foi criar uma Skill — um conjunto de instruções e exemplos reais que o Claude Code lê antes de gerar qualquer código de rotina automática.

Cobri os três padrões:
- ExecAuto clássico simples (sem itens)
- ExecAuto clássico com cabeçalho e itens (array de arrays)
- ExecAuto MVC via FWLoadModel e via FWMVCRotAuto

Com exemplos de inclusão, alteração e exclusão. Com tratamento de erro correto. Com as regras que a TOTVS documenta mas que ficam fáceis de esquecer no dia a dia.

---

Não é sobre IA escrever código por você.

É sobre garantir que, quando ela escreve, ela conhece as regras do ambiente onde o código vai rodar.

A skill está disponível gratuitamente no meu GitHub, junto com os exemplos em ADVPL:

🔗 https://github.com/ftvernier/erp-solutions/tree/main/claude/execauto-generator

Se você trabalha com Protheus e usa ou quer usar Claude Code, pode ser útil.

---

#Protheus #ADVPL #TLPP #TOTVS #ClaudeCode #IA #ERPDevelopment #OpenSource
