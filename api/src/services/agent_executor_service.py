from redis.asyncio import Redis
import datetime
import logging
import json
import os


class AgentExecutorService:
    def __init__(self, redis:Redis, agents: dict):
        self._redis = redis
        self._agents = agents
        self._steps = 0
        self._calls = 0
        self._limit_of_calls_per_day = 50
        self._usage = self._get_usage()

    def _get_usage(self):
        if not os.path.exists("data/usage.json"):
            return {}

        with open("data/usage.json", "r") as f:
            return json.load(f)
        
    def _save_usage(self):
        with open("data/usage.json", "w") as f:
            json.dump(self._usage, f)
        
    async def _publish_progress(self, job_id: str, step: str, progress: float, message: str = "", result: dict = {}):
        progress = {
            "step": step,
            "progress": progress,
            "message": message,
            "result": json.dumps(result)
        }
        await self._redis.xadd(f"jobs:progress:{job_id}", progress)
        logging.debug(f"Progress: {progress}")
    
    async def execute(self, job_id: str, agent_name: str, thread_id: str, user_prompt: str, debug: bool = False):
        logging.debug(f"Executing agent: {agent_name}")

        # Controlling the daily usage
        today = datetime.datetime.today().strftime("%Y-%m-%d")
        if today not in self._usage.keys():
            self._usage[today] = 0
        if self._usage[today] >= self._limit_of_calls_per_day:
            await self._publish_progress(
                job_id=job_id, step="",
                progress=1.0,
                message="",
                result={
                    "answer": "Sorry, we have reached the limit of calls per day. Please try again tomorrow."
                }
            )
            return

        agent = self._agents[agent_name]
        input = {"messages": [{"role": "user", "content": user_prompt}]}
        config = {"configurable": {"thread_id": thread_id}}

        steps = 0
        estimated_steps = (self._steps / self._calls) if self._calls > 5 else 10

        try:
            async for step in agent.astream(
                input=input, config=config, subgraphs=True,
                stream_mode="updates", debug=debug
            ):
                step_depth = len(step[0])
                step_str = ""

                if "model" in step[1].keys(): # Model call
                    model_message = step[1]["model"]["messages"][0]
                    if model_message.tool_calls:
                        tool_call = model_message.tool_calls[0] # NOTE: considering only one tool call per message
                        tool_name = tool_call.get("name")
                        tool_args = json.dumps(tool_call.get("args"), indent=4)

                        step_str = f'Calling `{tool_name}` with:\n```\n{tool_args}\n```\n---\n'
                elif "tools" in step[1].keys(): # Tool return
                    tool_message = step[1]["tools"]["messages"][0] # NOTE: considering only one tool call per message
                    tool_name = tool_message.name
                    tool_return = tool_message.content
                    step_str = f"Analyzing `{tool_name}` which returned:\n```\n{tool_return}\n```\n---\n"

                message = "Thinking..." if steps < estimated_steps else "Sorry, it is taking longer than expected. Please wait."

                await self._publish_progress(
                    job_id=job_id,
                    step=step_str,
                    progress=min(steps/estimated_steps, 0.95),
                    message=message,
                )
                steps += 1

            answer = step[1]["model"]["messages"][0].content
            await self._publish_progress(job_id=job_id, step=steps, progress=1.0, message="Result", result={"answer": answer})
        except Exception as e:
            raise e
        finally:
            self._calls += 1
            self._steps += steps

            # Registering the usage
            self._usage[today] += 1
            self._save_usage()