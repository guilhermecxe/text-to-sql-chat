from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
import traceback
import logging

from api.src.di import get_sql_agent, get_conversational_agent, get_redis_service
from api.src.services.redis_service import RedisService

router = APIRouter()


class AskConversationalAgentPayload(BaseModel):
    user_prompt: str
    thread_id: Optional[str | None] = None

@router.post("/ask-sql-agent")
async def ask_sql_agent(
    user_prompt: str,
    sql_agent = Depends(get_sql_agent)
):
    try:
        response = await sql_agent.ainvoke({"messages": [{"role": "user", "content": user_prompt}]})
        answer = response["messages"][-1].content
        return {"answer": answer}
    except Exception as e:
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/ask-conversational-agent")
async def ask_conversational_agent(
    payload: AskConversationalAgentPayload,
    redis: RedisService = Depends(get_redis_service),
):
    try:
        logging.info(f"Message received: {payload.user_prompt}")
        
        thread_id = payload.thread_id if payload.thread_id else str(uuid4())

        await redis.create_job(
            agent_name="conversational_agent",
            user_prompt=payload.user_prompt,
            thread_id=thread_id
        )

        return {"thread_id": thread_id}
    except Exception as e:
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))