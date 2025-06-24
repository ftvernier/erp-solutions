import requests
from datetime import datetime
import time

def enviar_grupo(mensagem):
    """Envia mensagem para o grupo"""
    bot_token = "SEU TOKEN"  
    chat_id_grupo = "SEU ID DO GRUPO"  # Seu grupo!
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = {
        "chat_id": chat_id_grupo,
        "text": mensagem,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=data)
        resultado = response.json()
        
        if resultado.get('ok'):
            print("✅ Mensagem enviada para o GRUPO!")
            print(f"📱 Message ID: {resultado['result']['message_id']}")
            return True
        else:
            print("❌ Erro:", resultado.get('description'))
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def teste_basico_grupo():
    """Teste básico no grupo"""
    
    mensagem = f"""
🎉 <b>MONITOR PROTHEUS ATIVO NO GRUPO!</b>

✅ Bot configurado com sucesso
👥 Grupo conectado: -4796377928
🤖 Alertas automáticos habilitados
📊 Integração com Protheus em andamento

━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 <b>Próximos Alertas Disponíveis:</b>
• 📦 Estoque baixo
• 💰 Relatórios de vendas
• ⚠️ Inadimplência
• 📈 Metas e performance
• 🔔 Status do sistema

📅 <i>{datetime.now().strftime('%d/%m/%Y às %H:%M')}</i>
👨‍💻 <i>Desenvolvido por Fernando Vernier</i>

<b>Todos do grupo receberão os alertas automaticamente!</b>
    """
    
    print("📤 Enviando mensagem de teste para o grupo...")
    return enviar_grupo(mensagem)

def demo_alerta_estoque_grupo():
    """Demo de alerta de estoque para o grupo"""
    
    mensagem = f"""
🚨 <b>ALERTA CRÍTICO - ESTOQUE BAIXO</b>

⚠️ <b>ATENÇÃO GESTORES!</b> Produtos abaixo do estoque mínimo detectados:

🔴 <b>MOUSE001 - Mouse Gamer RGB</b>
   └ Atual: <b>2 unidades</b> | Mínimo: <b>10</b>
   └ 📍 Filial 01 - MATRIZ

🔴 <b>TECL001 - Teclado Mecânico</b>
   └ Atual: <b>0 unidades</b> | Mínimo: <b>5</b>
   └ 📍 Filial 01 - MATRIZ

🔴 <b>MON001 - Monitor 24" Full HD</b>
   └ Atual: <b>1 unidade</b> | Mínimo: <b>8</b>
   └ 📍 Filial 01 - MATRIZ

━━━━━━━━━━━━━━━━━━━━━━━━━
📋 <b>AÇÕES NECESSÁRIAS:</b>
• 🛒 Gerar pedidos de compra urgentes
• 📞 Contatar fornecedores disponíveis
• 📊 Revisar política de estoque mínimo

👥 <b>RESPONSÁVEIS:</b>
• Setor de Compras: @compras
• Gerência: @gerencia
• Estoque: @estoque

⏰ <b>Alerta gerado em:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
🤖 <b>Sistema:</b> Monitor Protheus Automático

<i>Este alerta foi enviado para todos os gestores do grupo.</i>
    """
    
    print("📤 Enviando alerta de estoque baixo para o grupo...")
    return enviar_grupo(mensagem)

def demo_vendas_grupo():
    """Demo de relatório de vendas para o grupo"""
    
    mensagem = f"""
💰 <b>RELATÓRIO DE VENDAS - GRUPO GESTÃO</b>

📅 <b>Vendas de {datetime.now().strftime('%d/%m/%Y')}</b>

💵 <b>FATURAMENTO DO DIA:</b> R$ 42.847,65
📊 <b>Meta Diária:</b> R$ 35.000,00
🎯 <b>Performance:</b> <b>122,4% da meta ✅</b>
📈 <b>vs Ontem:</b> +18,5% (R$ 6.695,22)

━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 <b>RANKING DE VENDEDORES:</b>
1️⃣ <b>João Silva</b> - R$ 15.450,00 (36,1%)
2️⃣ <b>Maria Santos</b> - R$ 12.230,50 (28,5%)
3️⃣ <b>Pedro Costa</b> - R$ 8.890,15 (20,7%)
4️⃣ <b>Ana Lima</b> - R$ 4.277,00 (10,0%)
5️⃣ <b>Carlos Oliveira</b> - R$ 2.000,00 (4,7%)

📦 <b>PRODUTOS MAIS VENDIDOS:</b>
• Mouse Gamer RGB: <b>42 unidades</b>
• Teclado Mecânico: <b>28 unidades</b>
• Headset Premium: <b>15 unidades</b>
• Monitor 24": <b>12 unidades</b>

📊 <b>ESTATÍSTICAS DO DIA:</b>
• Total de Pedidos: <b>67</b>
• Ticket Médio: <b>R$ 639,22</b>
• Maior Venda: <b>R$ 4.567,80</b>
• Conversão: <b>78,2%</b>

🎉 <b>PARABÉNS EQUIPE!</b> Meta superada!

⏰ <b>Relatório gerado:</b> {datetime.now().strftime('%H:%M:%S')}
    """
    
    print("📤 Enviando relatório de vendas para o grupo...")
    return enviar_grupo(mensagem)

def demo_meta_batida():
    """Alerta especial quando meta é batida"""
    
    mensagem = f"""
🎉 <b>META MENSAL ATINGIDA!</b> 🎉

🏆 <b>CONQUISTA DESBLOQUEADA!</b>

💰 <b>Meta do Mês:</b> R$ 750.000,00
💵 <b>Realizado:</b> R$ 751.234,56
📈 <b>Performance:</b> <b>100,16% ✅</b>

━━━━━━━━━━━━━━━━━━━━━━━━━
🥇 <b>MVP DO MÊS:</b>
👑 <b>João Silva</b> - R$ 125.450,00

🔥 <b>EQUIPE DE VENDAS EM FESTA!</b>

📅 Meta batida em: <b>{datetime.now().strftime('%d/%m/%Y')}</b>
🍾 Comemoração merecida!

<b>PARABÉNS A TODOS! 👏👏👏</b>
    """
    
    print("🎉 Enviando alerta de meta batida para o grupo...")
    return enviar_grupo(mensagem)

def demo_sequencial():
    """Executa uma sequência de demos com intervalos"""
    
    print("🚀 INICIANDO DEMO SEQUENCIAL PARA O GRUPO")
    print("=" * 50)
    
    # Demo 1: Teste básico
    print("\n1️⃣ Teste básico...")
    if teste_basico_grupo():
        print("✅ Sucesso!")
    else:
        print("❌ Falhou - parando demo")
        return
    
    input("\nPressione ENTER para continuar com alerta de estoque...")
    
    # Demo 2: Estoque
    print("\n2️⃣ Alerta de estoque baixo...")
    demo_alerta_estoque_grupo()
    
    input("\nPressione ENTER para continuar com relatório de vendas...")
    
    # Demo 3: Vendas
    print("\n3️⃣ Relatório de vendas...")
    demo_vendas_grupo()
    
    input("\nPressione ENTER para continuar com meta batida...")
    
    # Demo 4: Meta batida
    print("\n4️⃣ Meta batida (celebração)...")
    demo_meta_batida()
    
    print("\n🎉 DEMO COMPLETO FINALIZADO!")
    print("👥 Todos do grupo receberam os alertas!")
    print("\n🔐 LEMBRE-SE: Regenerar token para segurança!")

if __name__ == "__main__":
    print("🤖 DEMO MONITOR PROTHEUS - GRUPO")
    print("=" * 40)
    print("1 - Teste básico no grupo")
    print("2 - Alerta de estoque baixo")
    print("3 - Relatório de vendas")
    print("4 - Meta batida (celebração)")
    print("5 - Demo sequencial completo")
    print("0 - Sair")
    
    opcao = input("\nEscolha uma opção: ")
    
    if opcao == "1":
        teste_basico_grupo()
    elif opcao == "2":
        demo_alerta_estoque_grupo()
    elif opcao == "3":
        demo_vendas_grupo()
    elif opcao == "4":
        demo_meta_batida()
    elif opcao == "5":
        demo_sequencial()
    else:
        print("👋 Até logo!")
