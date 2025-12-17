from fastapi import Request

def get_sql_agent(request: Request):
    return request.app.state.sql_agent

def get_conversational_agent(request: Request):
    return request.app.state.conversational_agent