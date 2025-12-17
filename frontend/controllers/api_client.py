import requests
import os

class APIClient:
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL")
        self.api_key = os.getenv("API_KEY")

    def ask_conversational_agent(self, user_prompt: str, thread_id: str):
        headers = {
            "X-API-KEY": self.api_key
        }
        data = {"user_prompt": user_prompt, "thread_id": thread_id}
        response = requests.post(
            url=f"{self.base_url}/agents/ask-conversational-agent",
            headers=headers,
            json=data
        )
        return response.json().get("answer")