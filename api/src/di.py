from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from fastapi import Request
from functools import lru_cache

from src.settings import Settings
from src.services.chart_service import ChartService
from src.services.agent_dispatcher_service import AgentDispatcherService
from src.services.agent_executor_service import AgentExecutorService
from src.adapters.plotly_adapter import PlotlyChartDesigner
from src.adapters.redis_adapter import RedisMessageBroker
from src.agents.conversational_agent import ConversationalAgent
from src.agents.sql_agent import SQLAgent
from src.agents.tools.chart_toolkit import ChartToolkit

@lru_cache()
def get_settings() -> Settings:
    return Settings()

@lru_cache()
def get_plotly_designer() -> PlotlyChartDesigner:
    return PlotlyChartDesigner(get_settings())

@lru_cache()
def get_redis_message_broker() -> RedisMessageBroker:
    return RedisMessageBroker(get_settings())

@lru_cache()
def get_chart_service() -> ChartService:
    return ChartService(get_plotly_designer())

@lru_cache()
def get_agent_dispatcher_service() -> AgentDispatcherService:
    return AgentDispatcherService(
        message_broker=get_redis_message_broker()
    )

@lru_cache()
def get_checkpointer() -> BaseCheckpointSaver:
    return InMemorySaver()

@lru_cache()
def get_chart_toolkit():
    return ChartToolkit(chart_service=get_chart_service())

@lru_cache()
def get_sql_agent():
    return SQLAgent(settings=get_settings())

@lru_cache()
def get_conversational_agent():
    return ConversationalAgent(
        settings=get_settings(),
        checkpointer=get_checkpointer(),
        subagents=[get_sql_agent()],
        tools=[],
        toolkits=[],
        chart_service=get_chart_service()
    )

@lru_cache()
def get_agent_executor_service():
    return AgentExecutorService(
        message_broker=get_redis_message_broker(),
        agents={
            "conversational_agent": get_conversational_agent(),
            "sql_agent": get_sql_agent(),
        }
    )

def get_redis_service(request: Request):
    return request.app.state.redis_service

def get_redis_client(request: Request):
    return request.app.state.redis_client

def get_langfuse_handler(request: Request):
    return request.app.state.langfuse_handler
