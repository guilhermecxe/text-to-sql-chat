from langgraph.checkpoint.memory import InMemorySaver
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi import FastAPI, HTTPException, Depends, status
from contextlib import asynccontextmanager
from langfuse.langchain import CallbackHandler
from langfuse import get_client
from dotenv import load_dotenv
from redis.asyncio import Redis
import asyncio
import logging
import os

from src.routes.agents import router as agents_router
from src.agents.sql_agent import create_sql_agent
from src.agents.conversational_agent import create_conversational_agent
from src.services.redis_service import RedisService
from src.services.worker_service import WorkerService
from src.services.agent_executor_service import AgentExecutorService

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
    app.state.redis_service = RedisService()
    app.state.redis_client = Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=os.getenv("REDIS_PORT", 6379),
        decode_responses=True,
    )

    # Langfuse
    if os.getenv("LANGFUSE_BASE_URL"):
        app.state.langfuse_client = get_client()
        app.state.langfuse_handler = CallbackHandler()

    # Para salvar o histórico das sessões do agente em memória
    checkpointer = InMemorySaver()

    # Criação dos agentes
    app.state.sql_agent = create_sql_agent(
        model=os.getenv("SQL_AGENT_MODEL"),
        db_uri="sqlite:///data/Chinook.db",
        debug=DEBUG,
    )
    sql_agent_tool = create_sql_agent(
        model=os.getenv("SQL_AGENT_MODEL"),
        db_uri="sqlite:///data/Chinook.db",
        as_tool=True,
        debug=DEBUG,
    )
    app.state.conversational_agent = create_conversational_agent(
        model=os.getenv("DEFAULT_CONVERSATIONAL_AGENT_MODEL"),
        langfuse_handler=app.state.langfuse_handler,
        tools=[sql_agent_tool],
        checkpointer=checkpointer,
        debug=DEBUG
    )

    # Serviços
    app.state.agent_executor_service = AgentExecutorService(
        redis=app.state.redis_client,
        agents={
            "conversational_agent": app.state.conversational_agent,
            "sql_agent": app.state.sql_agent
        },
        langfuse_client=app.state.langfuse_client,
        langfuse_handler=app.state.langfuse_handler
    )
    app.state.worker_service = WorkerService(
        redis=app.state.redis_client,
        agent_executor=app.state.agent_executor_service
    )

    # Iniciando a thread responsável por processar as requisições
    worker_task = asyncio.create_task(
        app.state.worker_service.loop()
    )
    
    yield

    worker_task.cancel()

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
app.include_router(agents_router, prefix="/api/agents", dependencies=[Depends(validate_api_key)])

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
    