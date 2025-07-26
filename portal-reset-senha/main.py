from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr
import httpx
import smtplib
import random
import string
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import Dict, Optional
from collections import defaultdict

app = FastAPI(title="Portal Reset Senha Protheus", version="1.0.0")

class Config:
    PROTHEUS_BASE_URL = os.getenv("PROTHEUS_URL", "http://localhost:8080/rest")
    PROTHEUS_USER = os.getenv("PROTHEUS_USER", "admin")
    PROTHEUS_PASS = os.getenv("PROTHEUS_PASS", "admin123")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "seu-email@gmail.com")
    SMTP_PASS = os.getenv("SMTP_PASS", "sua-senha-app")
    SECRET_KEY = os.getenv("SECRET_KEY", "chave-super-secreta-123")

config = Config()

class EmailRequest(BaseModel):
    email: EmailStr

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str
    confirm_password: str

reset_codes: Dict[str, dict] = {}
rate_limits: Dict[str, list] = defaultdict(list)

def check_rate_limit(email: str, max_attempts: int = 3, window_hours: int = 1) -> bool:
    now = time.time()
    window_start = now - (window_hours * 3600)
    rate_limits[email] = [t for t in rate_limits[email] if t > window_start]
    if len(rate_limits[email]) >= max_attempts:
        return False
    rate_limits[email].append(now)
    return True

def generate_code() -> str:
    return ''.join(random.choices(string.digits, k=6))

async def get_protheus_user_by_email(email: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.PROTHEUS_BASE_URL}/users",
                params={"foundBy": "MAIL", "count": 1},
                auth=(config.PROTHEUS_USER, config.PROTHEUS_PASS),
                timeout=30.0
            )
            if response.status_code == 200:
                data = response.json()
                users = data.get("Resources", data if isinstance(data, list) else [])
                if not isinstance(users, list):
                    users = [data] if data else []
                for user in users:
                    emails = user.get("emails", [])
                    for user_email in emails:
                        if user_email.get("value", "").lower() == email.lower():
                            return user
            return None
    except Exception as e:
        print(f"Erro ao consultar Protheus: {e}")
        return None

async def update_protheus_password(user_id: str, new_password: str) -> bool:
    try:
        payload = {
            "schemas": [
                "urn:scim:schemas:core:2.0:User",
                "urn:scim:schemas:extension:totvs:2.0:User"
            ],
            "password": new_password,
            "urn:scim:schemas:extension:totvs:2.0:User/forceChangePassword": False
        }
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{config.PROTHEUS_BASE_URL}/users/{user_id}",
                json=payload,
                auth=(config.PROTHEUS_USER, config.PROTHEUS_PASS),
                timeout=30.0,
                headers={"Content-Type": "application/json", "Accept": "application/json"}
            )
            if response.status_code == 200:
                result = response.json()
                return result is True or result == "true"
            return False
    except Exception as e:
        print(f"Erro ao atualizar senha no Protheus: {e}")
        return False

def send_email(to_email: str, code: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = config.SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = "Código de Verificação - Reset Senha Protheus"
        body = f"""
        <html>
        <body>
            <h2>🔐 Reset de Senha - Protheus</h2>
            <p>Você solicitou a redefinição de sua senha do sistema Protheus.</p>
            <p><strong>Seu código de verificação é: <span style="font-size: 24px; color: #007bff;">{code}</span></strong></p>
            <p>Este código é válido por 15 minutos.</p>
            <p>Se você não solicitou esta alteração, ignore este email.</p>
            <hr>
            <small>Portal de Reset de Senha - Protheus</small>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False

@app.post("/api/send-code")
async def send_verification_code(request: EmailRequest):
    if not check_rate_limit(request.email):
        raise HTTPException(status_code=429, detail="Muitas tentativas. Tente novamente em 1 hora.")
    
    user = await get_protheus_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email não encontrado no sistema.")
    
    if not user.get("active", False):
        raise HTTPException(status_code=403, detail="Usuário inativo. Contate o administrador.")
    
    code = generate_code()
    reset_codes[request.email] = {
        "code": code,
        "user_id": user.get("id"),
        "user_name": user.get("displayName", user.get("userName", "")),
        "expires_at": time.time() + (15 * 60),
        "attempts": 0
    }
    
    if not send_email(request.email, code):
        raise HTTPException(status_code=500, detail="Erro ao enviar email. Tente novamente.")
    
    return JSONResponse({
        "success": True,
        "message": f"Código enviado para {request.email}",
        "user_name": user.get("displayName", user.get("userName", ""))
    })

@app.post("/api/verify-code")
async def verify_code_and_reset(request: VerifyCodeRequest):
    if request.email not in reset_codes:
        raise HTTPException(status_code=404, detail="Código não encontrado. Solicite um novo código.")
    
    code_data = reset_codes[request.email]
    
    if time.time() > code_data["expires_at"]:
        del reset_codes[request.email]
        raise HTTPException(status_code=410, detail="Código expirado. Solicite um novo código.")
    
    if code_data["attempts"] >= 3:
        del reset_codes[request.email]
        raise HTTPException(status_code=429, detail="Muitas tentativas incorretas. Solicite um novo código.")
    
    if code_data["code"] != request.code:
        code_data["attempts"] += 1
        raise HTTPException(status_code=400, detail=f"Código incorreto. Tentativas restantes: {3 - code_data['attempts']}")
    
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="As senhas não coincidem.")
    
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres.")
    
    success = await update_protheus_password(code_data["user_id"], request.new_password)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao atualizar senha no Protheus. Tente novamente.")
    
    del reset_codes[request.email]
    return JSONResponse({
        "success": True,
        "message": "Senha alterada com sucesso!",
        "user_name": code_data["user_name"]
    })

@app.get("/", response_class=HTMLResponse)
async def get_portal():
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Portal de Reset de Senha - Protheus</h1><p>Arquivo index.html não encontrado.</p>", status_code=500)

@app.get("/health")
async def health_check():
    protheus_status = "disconnected"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.PROTHEUS_BASE_URL}/users/GetUserId",
                auth=(config.PROTHEUS_USER, config.PROTHEUS_PASS),
                timeout=10.0
            )
            if response.status_code == 200:
                protheus_status = "connected"
    except Exception:
        pass
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "protheus_connection": protheus_status,
        "reset_codes_active": len(reset_codes)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
