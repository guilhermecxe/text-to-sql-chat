from redis import Redis
from redis.exceptions import ResponseError
import logging
import json

from api.src.services.agent_executor_service import AgentExecutorService

class WorkerService:
    """
    Worker resposible for consuming the queue of pendent jobs and call the
    agent executor to run it.
    """
    def __init__(self, redis:Redis, agent_executor: AgentExecutorService):
        self._redis = redis
        self._agent_executor = agent_executor
        
        self._GROUP = "workers"
        self._STREAM = "jobs:queue"
        self._WORKER_NAME = "worker-1"

        try:
            self._redis.xgroup_create(self._STREAM, self._GROUP, id="0", mkstream=True)
        except ResponseError as e:
            # BUSYGROUP = group already exists
            if "BUSYGROUP" not in str(e):
                raise

    async def _process_job(self, job_id: str, payload: dict, debug: bool = False):
        agent_name = payload["agent_name"]
        thread_id = payload["thread_id"]
        user_prompt = payload["user_prompt"]

        await self._agent_executor.execute(
            job_id=job_id,
            agent_name=agent_name,
            thread_id=thread_id,
            user_prompt=user_prompt,
            debug=debug
        )

    async def loop(self):
        while True:
            entries = self._redis.xreadgroup(
                groupname=self._GROUP,
                consumername=self._WORKER_NAME,
                streams={self._STREAM: ">"}, # apenas mensagens novas
                count=1,
                block=5000 # tempo de espera até um retorno vazio
            )

            if not entries:
                logging.debug(f"No job found")
                continue

            logging.debug(f"Job encontrado: {entries}")

            for _, messages in entries:
                for message_id, data in messages:
                    job_id = data["job_id"]
                    payload = json.loads(data["payload"])
                    debug = payload.get("debug", "false") == "true"

                    await self._process_job(job_id, payload, debug=debug)

                    self._redis.xack(self._STREAM, self._GROUP, message_id)
