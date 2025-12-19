from langgraph.checkpoint.memory import InMemorySaver
from redis import Redis
from dotenv import load_dotenv
import logging
import asyncio
import os

from api.src.services.agent_executor_service import AgentExecutorService
from api.src.services.worker_service import WorkerService
from api.src.agents.sql_agent import create_sql_agent
from api.src.agents.conversational_agent import create_conversational_agent

load_dotenv()

MODE = os.getenv("MODE")
logging.basicConfig(
    level=(logging.DEBUG if MODE == "dev" else logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("stainless").setLevel(logging.WARNING)


async def main():
    redis = Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=os.getenv("REDIS_PORT", 6379),
        decode_responses=True,
    )

    sql_agent = create_sql_agent(
        model="openai:gpt-5-nano",
        db_uri="sqlite:///api/data/Chinook.db"
    )
    sql_agent_tool = create_sql_agent(
        model="openai:gpt-5-nano",
        db_uri="sqlite:///api/data/Chinook.db",
        as_tool=True,
    )

    checkpointer = InMemorySaver()
    conversational_agent = create_conversational_agent(
        model="openai:gpt-5-nano",
        tools=[sql_agent_tool],
        checkpointer=checkpointer,
    )

    agent_executor = AgentExecutorService(
        redis=redis,
        agents={
            "conversational_agent": conversational_agent,
            "sql_agent": sql_agent
        }
    )

    worker = WorkerService(
        redis=redis,
        agent_executor=agent_executor
    )

    logging.info("Starting worker")
    await worker.loop()

if __name__ == "__main__":
    asyncio.run(main())