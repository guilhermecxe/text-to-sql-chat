from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, RemoveMessage, ToolMessage, AIMessage
from langgraph.runtime import Runtime
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from src.agents.prompts.conversational_agent import system_prompt

@before_model
def trim_messages(state: AgentState, runtime: Runtime):
    """Keep only the last 20 messages to fit context window."""

    messages = state["messages"]
    if len(messages) < 20:
        return None # No update necessary

    # Obtendo as últimas 20 mensagens
    new_messages = messages[-20:]

    # Como demandado pela OpenAI, descartando respostas de tools
    # onde as chamadas já não aparecem no histórico
    new_new_messages = []
    ai_tool_calls = set()
    for message in new_messages:
        # Desconsiderando respostas de tools onde as chamadas
        # não foram encontradas
        if isinstance(message, ToolMessage):
            if not message.tool_call_id in ai_tool_calls:
                continue

        # Listando as chamadas de tool encontradas
        elif isinstance(message, AIMessage):
            for tool_call in message.tool_calls:
                ai_tool_calls.add(tool_call["id"])

        new_new_messages.append(message)

    new_messages = new_new_messages

    # Se há uma mensagem de sistema, ela é mantida no início do histórico
    if isinstance(messages[0], SystemMessage):
        new_messages = [messages[0]] + new_messages

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }

def create_conversational_agent(model: str, tools: list, langfuse_handler, checkpointer=None, debug: bool = False):
    llm = init_chat_model(model)
    agent = create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=checkpointer,
        middleware=[trim_messages],
        debug=debug
	).with_config({"callbacks": [langfuse_handler]})
    return agent