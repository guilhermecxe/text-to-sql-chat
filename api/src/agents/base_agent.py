from abc import ABC, abstractmethod


class BaseAgent(ABC):
    description: str = ""

    @abstractmethod
    async def ainvoke(): ...
    