from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# База данных ключей (можно менять прямо здесь)
KEYS_DATABASE = {
    "VALID-KEY-1234": {
        "is_active": True,
        "proxy_config": "192.168.1.50:8080:user:pass"
    },
    "EXPIRED-KEY-5678": {
        "is_active": False,
        "proxy_config": None
    }
}

class ActivationRequest(BaseModel):
    license_key: str

@app.get("/")
def home():
    
return {"status": "working", "message": "API launched successfully!"}

@app.post("/activate")
async def activate_proxy(request: ActivationRequest):
    key = request.license_key
    
    if key not in KEYS_DATABASE:
        raise HTTPException(status_code=404, detail="Ключ не найден.")
        
    key_info = KEYS_DATABASE[key]
    
    if not key_info["is_active"]:
        raise HTTPException(status_code=403, detail="Срок действия ключа истек.")
        
    return {
        "status": "success",
        "proxy": key_info["proxy_config"]
    }
