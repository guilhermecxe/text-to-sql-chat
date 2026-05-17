from langchain_core.tools import StructuredTool
from langchain.messages import SystemMessage
from langchain.agents.middleware import dynamic_prompt, wrap_model_call, ModelRequest
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.base import BaseCheckpointSaver
from langfuse.langchain import CallbackHandler
from langfuse import propagate_attributes
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

from src.settings import Settings
from src.agents.prompts.conversational_agent import SYSTEM_PROMPT
from src.agents.middlewares import trim_messages
from src.agents.base_agent import BaseAgent
from src.agents.tools.chart_toolkit import ChartToolkit
from src.services.chart_service import ChartService


class ConversationalAgent(BaseAgent):
    def __init__(
            self, settings: Settings, checkpointer: BaseCheckpointSaver, subagents: list[BaseAgent] = [],
            tools: list[StructuredTool] = [], toolkits: list = [], chart_service: ChartService = None
        ):
        self._default_model = settings.conversational_agent_default_model
        self._settings = settings
        self._checkpointer = checkpointer
        self._subagents = subagents
        self._chart_service = chart_service

        # Tools padrão
        self._chart_toolkit = ChartToolkit(self._chart_service)

        self._build(tools, toolkits)

    def _build(self, tools: list[StructuredTool] = [], toolkits: list = []):
        model = init_chat_model(self._default_model)
        middlewares = [trim_messages, self._prompt, self._model]

        # Tools padrão
        tools += self._chart_toolkit.get_tools()

        # Subagents como tools
        subagents_as_tools = [
            StructuredTool.from_function(
                coroutine=subagent.ainvoke_as_tool,
                name=type(subagent).__name__,
                description=subagent.description,
            )
            for subagent in self._subagents
        ]
        tools += subagents_as_tools

        # Tools de toolkits
        for toolkit in toolkits:
            tools.extend(toolkit.get_tools())

        # Definição do agente
        self._agent = create_agent(
            model=model,
            system_prompt=None, # adicionado a cada mensagem para permitir personalização dinâmica
            tools=tools,
            checkpointer=self._checkpointer,
            middleware=middlewares,
        ).with_config({"callbacks": [CallbackHandler()]})

    @dynamic_prompt
    def _prompt(self) -> SystemMessage:
        """
        Gera o SystemMessage para cada invocação, permitindo a inclusão de informações dinâmicas como data e hora atuais.
        """
        return SYSTEM_PROMPT.format(
            current_datetime=datetime.now(tz=ZoneInfo("America/Sao_Paulo")).isoformat()
        )

    @wrap_model_call
    async def _model(request: ModelRequest, handler):
        """
        Wrapper para a chamada do modelo, permitindo a substituição dinâmica do modelo
        com base no estado da requisição.
        """
        model_name = request.state.get("model")
        if model_name:
            request = request.override(model=init_chat_model(model_name))
        return await handler(request)

    async def ainvoke(self, message: str, theme: str, thread_id: str = None, model: str = None) -> dict:
        """Envia uma mensagem ao agente e retorna a resposta.

        Args:
            message (str): Mensagem do usuário.
            thread_id (str | None): ID da conversa. Se ``None``, inicia uma nova.
            model (str | None): Modelo a usar nesta invocação.

        Returns:
            dict: Dicionário com as chaves:
                - ``answer`` (str): Resposta gerada pelo agente.
                - ``thread_id`` (str): ID da conversa usada.
        """

        input = {"messages": [{"role": "user", "content": message}]}

        # Se um modelo específico for solicitado e for diferente do modelo atual,
        # incluimos essa informação no estado para que o middleware de modelo possa lidar.
        if model and model != self._default_model:
            input["model"] = model

        # Executando o agente
        with propagate_attributes(trace_name="ConversationalAgent", session_id=thread_id):
            with self._chart_toolkit.apply_theme(theme=theme):
                response = await self._agent.ainvoke(
                    input=input,
                    config={
                        "configurable": {"thread_id": thread_id}
                    }
                )
        answer = response["messages"][-1].content

        # Obtendo os gráficos mencionados na resposta, se houver
        charts_svgs = self._chart_toolkit.gather_charts(answer)

        # TODO: Se um gráfico for mencionado na resposta, mas não for encontrado,
        # voltar ao loop do agente fazendo essa sinalização.
        # TODO: Se um gráfico for gerado, mas não for mencionado, fazer uma nova inferência
        # para confirmar a não necessidade

        return {
            "answer": answer,
            "charts": charts_svgs,
            "thread_id": thread_id
        }
    