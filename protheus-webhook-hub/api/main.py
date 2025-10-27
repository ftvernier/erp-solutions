from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import redis
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configurações
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://webhook_user:webhook_pass@db:5432/webhook_hub")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# FastAPI App
app = FastAPI(
    title="Protheus Webhook Hub",
    description="Sistema de webhooks para integração do ERP Protheus com aplicações modernas",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis Connection
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Database Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class WebhookConfig(Base):
    __tablename__ = "webhook_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    destination_url = Column(String(500), nullable=False)
    destination_type = Column(String(50), nullable=False)  # slack, teams, whatsapp, custom
    active = Column(Boolean, default=True)
    headers = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)  # pending, success, failed
    destination_url = Column(String(500))
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class WebhookEventRequest(BaseModel):
    event_type: str = Field(..., description="Tipo do evento (ex: pedido.criado, nfe.emitida)")
    data: Dict[str, Any] = Field(..., description="Dados do evento")
    source: str = Field(default="protheus", description="Sistema de origem")
    timestamp: Optional[datetime] = None

class WebhookConfigCreate(BaseModel):
    name: str
    event_type: str
    destination_url: str
    destination_type: str
    headers: Optional[Dict[str, str]] = None
    active: bool = True

class WebhookConfigResponse(BaseModel):
    id: int
    name: str
    event_type: str
    destination_url: str
    destination_type: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class WebhookLogResponse(BaseModel):
    id: int
    event_type: str
    status: str
    destination_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Routes
@app.get("/")
async def root():
    return {
        "message": "Protheus Webhook Hub API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "webhook": "/webhook",
            "configs": "/configs",
            "logs": "/logs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    try:
        # Test Redis
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    try:
        # Test Database
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if redis_status == "healthy" and db_status == "healthy" else "unhealthy",
        "redis": redis_status,
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/webhook", status_code=202)
async def receive_webhook(event: WebhookEventRequest, db: Session = Depends(get_db)):
    """
    Endpoint principal que recebe eventos do Protheus
    """
    try:
        # Set timestamp if not provided
        if not event.timestamp:
            event.timestamp = datetime.utcnow()
        
        # Save to database log
        log = WebhookLog(
            event_type=event.event_type,
            payload=json.dumps(event.dict()),
            status="pending"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        # Add to Redis queue for processing
        queue_data = {
            "log_id": log.id,
            "event_type": event.event_type,
            "data": event.data,
            "source": event.source,
            "timestamp": event.timestamp.isoformat()
        }
        
        redis_client.lpush("webhook_queue", json.dumps(queue_data))
        
        return {
            "status": "accepted",
            "log_id": log.id,
            "message": "Evento recebido e enfileirado para processamento"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar webhook: {str(e)}")

@app.get("/configs", response_model=List[WebhookConfigResponse])
async def list_configs(db: Session = Depends(get_db)):
    """
    Lista todas as configurações de webhook
    """
    configs = db.query(WebhookConfig).all()
    return configs

@app.post("/configs", response_model=WebhookConfigResponse, status_code=201)
async def create_config(config: WebhookConfigCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova configuração de webhook
    """
    db_config = WebhookConfig(
        name=config.name,
        event_type=config.event_type,
        destination_url=config.destination_url,
        destination_type=config.destination_type,
        headers=json.dumps(config.headers) if config.headers else None,
        active=config.active
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@app.delete("/configs/{config_id}")
async def delete_config(config_id: int, db: Session = Depends(get_db)):
    """
    Remove uma configuração de webhook
    """
    config = db.query(WebhookConfig).filter(WebhookConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuração não encontrada")
    
    db.delete(config)
    db.commit()
    return {"message": "Configuração removida com sucesso"}

@app.get("/logs", response_model=List[WebhookLogResponse])
async def list_logs(
    limit: int = 100,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista os logs de webhooks processados
    """
    query = db.query(WebhookLog)
    
    if event_type:
        query = query.filter(WebhookLog.event_type == event_type)
    if status:
        query = query.filter(WebhookLog.status == status)
    
    logs = query.order_by(WebhookLog.created_at.desc()).limit(limit).all()
    return logs

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Retorna estatísticas do sistema
    """
    total_configs = db.query(WebhookConfig).count()
    active_configs = db.query(WebhookConfig).filter(WebhookConfig.active == True).count()
    total_logs = db.query(WebhookLog).count()
    success_logs = db.query(WebhookLog).filter(WebhookLog.status == "success").count()
    failed_logs = db.query(WebhookLog).filter(WebhookLog.status == "failed").count()
    pending_logs = db.query(WebhookLog).filter(WebhookLog.status == "pending").count()
    
    queue_size = redis_client.llen("webhook_queue")
    
    return {
        "configs": {
            "total": total_configs,
            "active": active_configs
        },
        "logs": {
            "total": total_logs,
            "success": success_logs,
            "failed": failed_logs,
            "pending": pending_logs
        },
        "queue": {
            "size": queue_size
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
