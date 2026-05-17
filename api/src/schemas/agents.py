from pydantic import BaseModel
from typing import Optional, Literal


class AskConversationalAgentRequest(BaseModel):
    user_prompt: str
    thread_id: Optional[str | None] = None
    async_mode: Optional[bool] = True
    theme: Literal["light", "dark"] = "light"
