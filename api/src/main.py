from langgraph.checkpoint.memory import InMemorySaver
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi import FastAPI, HTTPException, Depends, status
from dotenv import load_dotenv
import logging
import os

from api.src.routes.agents import router as agents_router
from api.src.agents.sql_agent import create_sql_agent
from api.src.agents.conversational_agent import create_conversational_agent

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="SQL Agent API",
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("API_KEY", "")
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def validate_api_key(api_key: str = Depends(api_key_header)):
    if os.getenv("MODE", "hom") == "dev":
        return True
    
    if api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

app.include_router(agents_router, prefix="/api/agents", dependencies=[Depends(validate_api_key)])

@app.on_event("startup")
async def startup():
    debug = os.getenv("DEBUG_MODE", "false") == "true"

    app.state.sql_agent = create_sql_agent(
        model="openai:gpt-5-nano",
        db_uri="sqlite:///api/data/Chinook.db",
        debug=debug,
    )

    sql_agent_tool = create_sql_agent(
        model="openai:gpt-5-nano",
        db_uri="sqlite:///api/data/Chinook.db",
        as_tool=True,
        debug=debug,
    )
    checkpointer = InMemorySaver()
    app.state.conversational_agent = create_conversational_agent(
        model="openai:gpt-5-nano",
        tools=[sql_agent_tool],
        checkpointer=checkpointer,
        debug=debug
    )

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
    