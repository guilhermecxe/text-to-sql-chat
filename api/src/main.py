from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi import FastAPI, HTTPException, Depends, status
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncio
import logging
import os

from src.di import get_agent_executor_service
from src.routes.agents import router as agents_router


load_dotenv()

# Controle dos logs
DEBUG = os.getenv("DEBUG") == "dev"
MODE = os.getenv("MODE")
logging.basicConfig(
    level=(logging.DEBUG if MODE == "dev" else logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("stainless").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Iniciando uma thread de execução assíncrona de agentes
    agent_executor_service = get_agent_executor_service()
    agent_executor_task = asyncio.create_task(agent_executor_service.run())
    
    yield

    agent_executor_task.cancel()

app = FastAPI(
    title="SQL Agent API",
    lifespan=lifespan,
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chave de API
API_KEY = os.getenv("API_KEY", "")
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def validate_api_key(api_key: str = Depends(api_key_header)):
    if os.getenv("MODE", "hom") == "dev":
        return True
    
    if api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

# Endpoints principais
app.include_router(agents_router, prefix="/api/agents", tags=["Agents"], dependencies=[Depends(validate_api_key)])

# Endpoints auxiliares
@app.get("/")
async def root():
    """
    Rota raiz que retorna informações básicas sobre a API
    """
    return {
        "message": "SQL Agent API",
        "version": "0.1.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    try:
        return {
            "status": "healthy",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    