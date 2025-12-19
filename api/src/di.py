from fastapi import Request

def get_sql_agent(request: Request):
    return request.app.state.sql_agent

def get_conversational_agent(request: Request):
    return request.app.state.conversational_agent

def get_agent_executor_service(request: Request):
    return request.app.state.agent_executor_service

def get_redis_service(request: Request):
    return request.app.state.redis_service