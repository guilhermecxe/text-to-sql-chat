from abc import ABC, abstractmethod

class MessageBroker(ABC):
    @abstractmethod
    async def enqueue(self, task: dict, job_id: str) -> None: ...

    @abstractmethod
    async def dequeue(self, timeout=5) -> dict | None: ...

    @abstractmethod
    async def set(self, job_id: str, object: dict, expire: int = 3600): ...

    @abstractmethod
    async def get(self, job_id: str) -> dict: ...
    