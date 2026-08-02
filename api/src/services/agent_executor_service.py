from datetime import date
import logging
import json
import os

from src.ports.message_broker import MessageBroker
from src.agents.base_agent import BaseAgent


class AgentExecutorService:
    def __init__(self, message_broker: MessageBroker, agents: dict[str, BaseAgent]):
        self._message_broker = message_broker
        self._agents = agents

        self._usage_daily_limit = int(os.getenv("DAILY_USAGE_LIMIT", 30))
        self._usage_file_path = "data/usage.json"
        self._usage = None

    async def _read_usage(self):
        try:
            with open(self._usage_file_path, "r") as f:
                self._usage = json.load(f)
        except FileNotFoundError:
            await self._write_usage()
            await self._read_usage()

    async def _write_usage(self):
        with open(self._usage_file_path, "w") as f:
            json.dump(self._usage, f)

    async def _update_usage(self):
        await self._read_usage()

        today = date.today().strftime("%Y-%m-%d")
        if not today in self._usage:
            self._usage[today] = 1
        else:
            self._usage[today] += 1

        await self._write_usage()

    async def _can_execute(self):
        await self._read_usage()
        
        today = date.today().strftime("%Y-%m-%d")

        if not today in self._usage or self._usage[today] < self._usage_daily_limit:
            return True
        return False

    async def get_result(self, job_id: str):
        return await self._message_broker.get(job_id)

    async def execute(self, agent_name: str, agent_input: dict):
        if await self._can_execute():
            await self._update_usage()
            return await self._agents[agent_name].ainvoke(**agent_input)
        return {"error": "Daily usage limit reached."}

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
