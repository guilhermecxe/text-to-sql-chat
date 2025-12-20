import requests
import os

class APIClient:
    """
    Responsible for handling API requests to the backend.
    """
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL")
        self.api_key = os.getenv("API_KEY")

    def ask_conversational_agent(self, user_prompt: str, thread_id: str):
        """
        Sends a user prompt to the conversational agent and retrieves the response.

        Args:
            user_prompt (str): The user's input prompt.
            thread_id (str): The ID of the conversation thread.

        Returns:
            dict: The JSON response from the API, containing the updated thread information.
        """
        
        headers = {
            "X-API-KEY": self.api_key
        }
        data = {"user_prompt": user_prompt, "thread_id": thread_id}
        response = requests.post(
            url=f"{self.base_url}/agents/ask-conversational-agent",
            headers=headers,
            json=data
        )
        return response.json()