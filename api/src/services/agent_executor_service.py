import logging

from src.ports.message_broker import MessageBroker
from src.agents.base_agent import BaseAgent


class AgentExecutorService:
    def __init__(self, message_broker: MessageBroker, agents: dict[str, BaseAgent]):
        self._message_broker = message_broker
        self._agents = agents

    async def get_result(self, job_id: str):
        return await self._message_broker.get(job_id)

    async def execute(self, agent_name: str, agent_input: dict):
        return await self._agents[agent_name].ainvoke(**agent_input)        

    async def run(self):
        while True:
            try:
                task = await self._message_broker.dequeue(timeout=30)

                if not task:
                    continue
                
                # Executando o agente
                agent_name = task["task"]["agent_name"]
                agent_input = task["task"]["input"]
                result = await self.execute(agent_name=agent_name, agent_input=agent_input)

                # Salvando o resultado do agente
                job_id = task["job_id"]
                await self._message_broker.set(job_id=job_id, object=result)

            except:
                logging.exception("Erro durante execução de um agente.")
