from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, RemoveMessage
from langgraph.runtime import Runtime
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from src.agents.prompts.conversational_agent import system_prompt


@before_model
def trim_messages(state: AgentState, runtime: Runtime):
    """Keep only the last 20 messages to fit context window."""

    messages = state["messages"]
    if len(messages) < 20:
        return None # No update necessary

    new_messages = messages[-20:]

    if isinstance(messages[0], SystemMessage):
        new_messages = [messages[0]] + new_messages

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }

def create_conversational_agent(model: str, tools: list, checkpointer=None, debug: bool = False):
    llm = init_chat_model(model)
    agent = create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=checkpointer,
        middleware=[trim_messages],
        debug=debug
	)
    return agent