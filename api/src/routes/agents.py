from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
import traceback
import logging

from api.src.di import get_sql_agent, get_conversational_agent

router = APIRouter()


class AskConversationalAgentPayload(BaseModel):
    user_prompt: str
    thread_id: Optional[str] = None


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
    conversational_agent = Depends(get_conversational_agent)
):
    try:
        logging.info(f"Message received: {payload.user_prompt}")
        
        thread_id = payload.thread_id or str(uuid4())

        response = await conversational_agent.ainvoke(
            input={"messages": [{"role": "user", "content": payload.user_prompt}]},
            config={"configurable": {"thread_id": thread_id}}
        )

        answer = response["messages"][-1].content
        return {"answer": answer}
    except Exception as e:
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))