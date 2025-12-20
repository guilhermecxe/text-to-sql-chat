import redis
import logging
import json
import os

class RedisClient:
    """
    Responsible for handling Redis operations.
    """
    def __init__(self):
        self._r = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=os.getenv("REDIS_PORT", 6379),
            decode_responses=True,
        )

    def check_progress(self, job_id: str, last_id: str="0-0"):
        """
        Checks the progress of a job in Redis. It runs until a progress
        item is found.

        Args:
            job_id (str): The ID of the job.
        """
        # TODO: finish the method docstring.
        while True:
            entries = self._r.xread(
                streams={f"jobs:progress:{job_id}": last_id},
                count=1,
                block=5000
            )

            if not entries:
                return None, last_id

            for _, messages in entries:
                for message_id, data in messages:
                    data["result"] = json.loads(data["result"])
                    data["progress"] = float(data["progress"])
                    return data, message_id
