from redis.asyncio import Redis
import logging
import json

class AgentExecutorService:
    def __init__(self, redis:Redis, agents: dict):
        self._redis = redis
        self._agents = agents
        
    def _publish_progress(self, job_id: str, step: str, progress: float, message: str = "", result: dict = {}):
        progress = {
            "step": step,
            "progress": progress,
            "message": message,
            "result": json.dumps(result)
        }
        self._redis.xadd(f"jobs:progress:{job_id}", progress)
        logging.debug(f"Progress: {progress}")
    
    async def execute(self, job_id: str, agent_name: str, thread_id:str, user_prompt: str):
        logging.debug(f"Executing agent: {agent_name}")

        agent = self._agents[agent_name]
        input = {"messages": [{"role": "user", "content": user_prompt}]}
        config = {"configurable": {"thread_id": thread_id}}

        estimated_steps = 10
        steps = 0
        async for step in agent.astream(input=input, config=config, subgraphs=True, stream_mode="updates"):
            self._publish_progress(
                job_id=job_id,
                step=steps,
                progress=min(steps/estimated_steps, 0.90),
                message="Thinking",
            )
            steps += 1

        answer = step[1]["model"]["messages"][0].content
        self._publish_progress(job_id=job_id, step=steps, progress=1.0, message="Result", result={"answer": answer})
