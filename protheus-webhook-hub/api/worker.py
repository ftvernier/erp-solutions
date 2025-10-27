import redis
import json
import httpx
import time
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configurações
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://webhook_user:webhook_pass@db:5432/webhook_hub")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Database Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class WebhookConfig(Base):
    __tablename__ = "webhook_configs"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    event_type = Column(String(100))
    destination_url = Column(String(500))
    destination_type = Column(String(50))
    active = Column(Boolean)
    headers = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    id = Column(Integer, primary_key=True)
    event_type = Column(String(100))
    payload = Column(Text)
    status = Column(String(50))
    destination_url = Column(String(500))
    error_message = Column(Text)
    created_at = Column(DateTime)
    processed_at = Column(DateTime)

# Redis Connection
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def format_slack_message(event_type: str, data: dict) -> dict:
    """Formata mensagem para Slack"""
    return {
        "text": f"🔔 Novo evento: {event_type}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📦 {event_type}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}"
                    }
                    for key, value in list(data.items())[:5]  # Primeiros 5 campos
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    }
                ]
            }
        ]
    }

def format_teams_message(event_type: str, data: dict) -> dict:
    """Formata mensagem para Microsoft Teams"""
    facts = [{"name": key, "value": str(value)} for key, value in list(data.items())[:5]]
    
    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": f"Evento: {event_type}",
        "themeColor": "0078D7",
        "title": f"📦 {event_type}",
        "sections": [
            {
                "facts": facts,
                "text": f"Evento recebido em {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            }
        ]
    }

def format_custom_message(event_type: str, data: dict, source: str) -> dict:
    """Formata mensagem para webhook customizado"""
    return {
        "event_type": event_type,
        "data": data,
        "source": source,
        "timestamp": datetime.utcnow().isoformat()
    }

async def send_webhook(config: WebhookConfig, event_data: dict):
    """Envia webhook para o destino configurado"""
    try:
        event_type = event_data.get("event_type")
        data = event_data.get("data", {})
        source = event_data.get("source", "protheus")
        
        # Formata payload baseado no tipo de destino
        if config.destination_type == "slack":
            payload = format_slack_message(event_type, data)
        elif config.destination_type == "teams":
            payload = format_teams_message(event_type, data)
        else:  # custom
            payload = format_custom_message(event_type, data, source)
        
        # Prepara headers
        headers = {"Content-Type": "application/json"}
        if config.headers:
            custom_headers = json.loads(config.headers)
            headers.update(custom_headers)
        
        # Envia requisição
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                config.destination_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
        return True, None
    
    except Exception as e:
        return False, str(e)

def process_webhook(event_data: dict):
    """Processa um evento da fila"""
    db = SessionLocal()
    
    try:
        log_id = event_data.get("log_id")
        event_type = event_data.get("event_type")
        
        print(f"[{datetime.utcnow()}] Processando evento {event_type} (log_id: {log_id})")
        
        # Busca configurações ativas para este tipo de evento
        configs = db.query(WebhookConfig).filter(
            WebhookConfig.event_type == event_type,
            WebhookConfig.active == True
        ).all()
        
        if not configs:
            print(f"  ⚠️  Nenhuma configuração ativa encontrada para {event_type}")
            # Atualiza log como success (não há destinos configurados)
            log = db.query(WebhookLog).filter(WebhookLog.id == log_id).first()
            if log:
                log.status = "success"
                log.processed_at = datetime.utcnow()
                db.commit()
            return
        
        print(f"  📤 Enviando para {len(configs)} destino(s)")
        
        # Envia para cada destino configurado
        success_count = 0
        error_messages = []
        
        for config in configs:
            import asyncio
            success, error = asyncio.run(send_webhook(config, event_data))
            
            if success:
                success_count += 1
                print(f"    ✅ {config.name} ({config.destination_type})")
            else:
                error_messages.append(f"{config.name}: {error}")
                print(f"    ❌ {config.name} ({config.destination_type}): {error}")
        
        # Atualiza log
        log = db.query(WebhookLog).filter(WebhookLog.id == log_id).first()
        if log:
            if success_count > 0 and not error_messages:
                log.status = "success"
            elif success_count > 0 and error_messages:
                log.status = "partial"
                log.error_message = "; ".join(error_messages)
            else:
                log.status = "failed"
                log.error_message = "; ".join(error_messages)
            
            log.processed_at = datetime.utcnow()
            log.destination_url = f"{success_count}/{len(configs)} destinos"
            db.commit()
        
        print(f"  ✔️  Processamento concluído: {success_count}/{len(configs)} enviados com sucesso")
    
    except Exception as e:
        print(f"  ❌ Erro ao processar: {str(e)}")
        # Atualiza log como falha
        if log_id:
            log = db.query(WebhookLog).filter(WebhookLog.id == log_id).first()
            if log:
                log.status = "failed"
                log.error_message = str(e)
                log.processed_at = datetime.utcnow()
                db.commit()
    
    finally:
        db.close()

def main():
    """Loop principal do worker"""
    print("🚀 Webhook Worker iniciado")
    print(f"   Redis: {REDIS_HOST}:{REDIS_PORT}")
    print(f"   Database: {DATABASE_URL}")
    print("   Aguardando eventos...\n")
    
    while True:
        try:
            # Aguarda por eventos na fila (bloqueante com timeout de 1 segundo)
            result = redis_client.brpop("webhook_queue", timeout=1)
            
            if result:
                _, event_json = result
                event_data = json.loads(event_json)
                process_webhook(event_data)
            
        except KeyboardInterrupt:
            print("\n👋 Worker finalizado")
            break
        
        except Exception as e:
            print(f"❌ Erro no worker: {str(e)}")
            time.sleep(5)  # Aguarda antes de tentar novamente

if __name__ == "__main__":
    # Aguarda um pouco para o banco estar pronto
    print("⏳ Aguardando serviços iniciarem...")
    time.sleep(10)
    main()
