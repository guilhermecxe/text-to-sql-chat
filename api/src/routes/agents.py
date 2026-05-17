from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4
import logging

from src.di import (
    get_sql_agent,
    get_agent_dispatcher_service,
    get_agent_executor_service,
)
from src.services.agent_dispatcher_service import AgentDispatcherService
from src.services.agent_executor_service import AgentExecutorService
from src.schemas.agents import AskConversationalAgentRequest


router = APIRouter()

@router.post("/ask-sql-agent")
async def ask_sql_agent(
    user_prompt: str,
    async_mode: bool = False,
    agent_executor_service: AgentExecutorService = Depends(get_agent_executor_service),
    agent_dispatcher_service: AgentDispatcherService = Depends(get_agent_dispatcher_service)
):
    # try:
    #     response = await sql_agent.ainvoke({"messages": [{"role": "user", "content": user_prompt}]})
    #     answer = response["messages"][-1].content
    #     return {"answer": answer}
    # except Exception as e:
    #     logging.exception("Error on /ask_sql_agent")
    #     raise HTTPException(status_code=500, detail=str(e))

    try:
        agent_name = "sql_agent"
        agent_input = {"message": user_prompt}

        if async_mode:
            job_id = await agent_dispatcher_service.dispatch(agent_name, agent_input)
            return {"job_id": job_id}
        
        else:
            result = await agent_executor_service.execute(agent_name, agent_input)
            return {
                "answer": result["answer"]
            }

    except Exception as e:
        logging.exception("Error on /ask_conversational_agent")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/ask-conversational-agent")
async def ask_conversational_agent(
    payload: AskConversationalAgentRequest,
    agent_executor_service: AgentExecutorService = Depends(get_agent_executor_service),
    agent_dispatcher_service: AgentDispatcherService = Depends(get_agent_dispatcher_service)
):
    try:
        agent_name = "conversational_agent"
        agent_input = {
            "message": payload.user_prompt,
            "thread_id": payload.thread_id if payload.thread_id else str(uuid4()),
            "theme": payload.theme
        }

        if payload.async_mode:
            job_id = await agent_dispatcher_service.dispatch(agent_name, agent_input)
            return {"job_id": job_id}
        
        else:
            result = await agent_executor_service.execute(agent_name, agent_input)
            return {
                "answer": result["answer"],
                "charts": result["charts"],
                "thread_id": result["thread_id"]
            }

    except Exception as e:
        logging.exception("Error on /ask_conversational_agent")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pull_answer")
async def pull_answer(
    job_id: str,
    agent_executor_service: AgentExecutorService = Depends(get_agent_executor_service),
):
    try:
        result = await agent_executor_service.get_result(job_id)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Error on /pull_answer")
        raise HTTPException(status_code=500, detail=str(e))
