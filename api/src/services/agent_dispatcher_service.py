import uuid

from src.ports.message_broker import MessageBroker


class AgentDispatcherService:
    def __init__(self, message_broker: MessageBroker):
        self._message_broker = message_broker

    async def dispatch(self, agent_name: str, agent_input: dict) -> str:
        job_id = str(uuid.uuid4())
        await self._message_broker.enqueue(
            task={"agent_name": agent_name, "input": agent_input},
            job_id=job_id
        )
        return job_id
