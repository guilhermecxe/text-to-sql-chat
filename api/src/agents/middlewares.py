from langchain.agents import AgentState
from langchain.agents.middleware import before_model
from langchain.messages import SystemMessage, RemoveMessage, ToolMessage, AIMessage
from langgraph.runtime import Runtime
from langgraph.graph.message import REMOVE_ALL_MESSAGES


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