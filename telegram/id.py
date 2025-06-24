import requests

# Seu token 
bot_token = "SEU TOKEN"

# Função para descobrir chat ID
def obter_chat_id():
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    response = requests.get(url)
    print(response.json())

# 1. Adicione seu bot no chat/grupo
# 2. Envie uma mensagem para o bot
# 3. Execute esta função para pegar o chat_id
obter_chat_id()
