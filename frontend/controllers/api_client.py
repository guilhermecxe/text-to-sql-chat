import requests
import logging
import os
import re

class APIClient:
    """
    Responsible for handling API requests to the backend.
    """
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
    
    def _resize_svg(self, svg: str, width: int) -> str:
        # Extrai width e height originais
        w = float(re.search(r'width="([\d.]+)"', svg).group(1))
        h = float(re.search(r'height="([\d.]+)"', svg).group(1))
        
        scale = width / w
        new_w = width
        new_h = round(h * scale)
        
        svg = re.sub(r'width="[\d.]+"', f'width="{new_w}"', svg, count=1)
        svg = re.sub(r'height="[\d.]+"', f'height="{new_h}"', svg, count=1)
        return svg

    def _place_charts(self, answer: str, charts: dict[str, str]) -> str:
        logging.debug(f"Charts: {charts}")

        def replace_chart(match):
            chart_id = match.group(1)
            svg = charts[chart_id]
            if svg is None:
                return match.group(0)
            return self._resize_svg(svg, width=600)

        result = re.sub(r'\[\[chart=(\d+)\]\]', replace_chart, answer)
        return result

    def pull_answer(self, job_id: str):
        headers = {"X-API-KEY": self.api_key}
        try:
            response = requests.get(
                url=f"{self.base_url}/agents/pull_answer?job_id={job_id}",
                headers=headers,
            )
            response.raise_for_status()

            response_json = response.json()

            result = {}
            result["thread_id"] = response_json["thread_id"]
            result["answer"] = self._place_charts(response_json["answer"], response_json["charts"])
            result["success"] = True
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            logging.exception(f"Error for job_id={job_id}")
            return {"success": False}
        except requests.exceptions.ConnectionError:
            logging.exception(f"Error for job_id={job_id}")
            return {"success": False}

    def ask_conversational_agent(
            self, user_prompt: str, thread_id: str | None, async_mode: bool,
            theme: str, model: str = None
    ):
        """
        Sends a user prompt to the conversational agent and retrieves the response.

        Args:
            user_prompt (str): The user's input prompt.
            thread_id (str): The ID of the conversation thread.

        Returns:
            dict: The JSON response from the API, containing the updated thread information.
        """

        headers = {"X-API-KEY": self.api_key}
        data = {
            "user_prompt": user_prompt,
            "async_mode": async_mode,
            "thread_id": thread_id,
            "theme": theme
        }

        logging.info(f"Data: {data}")

        try:
            response = requests.post(
                url=f"{self.base_url}/agents/ask-conversational-agent",
                headers=headers,
                json=data
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            logging.exception(f"Error for thread_id={thread_id}, user_prompt={user_prompt}")
            result = {"success": False}
        else:
            response_json = response.json()
            if response_json:
                result = {"sucess": True}

                if "job_id" in response_json:
                    result["job_id"] = response_json["job_id"]
                else:
                    result["thread_id"] = response_json["thread_id"]
                    result["answer"] = self._place_charts(response_json["answer"], response_json["charts"])
            else:
                logging.error(f"Empty body for thread_id={thread_id}, user_prompt={user_prompt}")
                result = {"success": False}
        
        return result
    