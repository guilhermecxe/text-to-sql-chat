from redis.asyncio import Redis
import logging
import json
import os

from src.ports.message_broker import MessageBroker
from src.settings import Settings


class RedisMessageBroker(MessageBroker):
    def __init__(self, settings: Settings):
        self._redis_client = Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=os.getenv("REDIS_PORT", 6379),
            decode_responses=True, # Já converte bytes -> utf-8
        )
        self._tasks_queue_name = os.getenv("TASKS_QUEUE_NAME")

    async def enqueue(self, task: dict, job_id: str) -> None:
        await self._redis_client.rpush(
            self._tasks_queue_name,
            json.dumps({"task": task, "job_id": job_id})
        )

    async def dequeue(self, timeout=5) -> dict | None:
        item = await self._redis_client.blpop(
            self._tasks_queue_name,
            timeout=timeout
        )

        if not item:
            return None
        
        task = item[1]
        task = json.loads(task)

        # Marcando o job para que outro worker, se existir,
        # não o consuma também
        job_id = task.get("job_id")
        claim = await self._redis_client.setnx(f"job:{job_id}:lock", "1")
        if not claim:
            return None
        
        return task
    
    async def set(self, job_id: str, object: dict, expire: int = 3600):
        await self._redis_client.set(
            name=f"result:{job_id}",
            value=json.dumps(object),
            ex=expire
        )

    async def get(self, job_id: str) -> dict:
        value = await self._redis_client.get(name=f"result:{job_id}")
        if not value:
            return None
        return json.loads(value)
    