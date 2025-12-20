import redis.asyncio as redis
import logging
import json
import os

class RedisService:
    def __init__(self):
        self._r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=os.getenv("REDIS_PORT", 6379),
            decode_responses=True,
        )

    async def create_job(self, agent_name: str, user_prompt: str, thread_id: str, debug: bool = False):
        await self._r.xadd(
            "jobs:queue", {
                "job_id": thread_id,
                "payload": json.dumps({
                    "agent_name": agent_name,
                    "thread_id": thread_id,
                    "user_prompt": user_prompt,
                    "debug": "true" if debug else "false"
                })
            }
        )
        logging.debug("Job added to the queue")

        return True