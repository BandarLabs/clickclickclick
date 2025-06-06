import openai
from typing import Any
from . import Planner, logger
import json
from clickclickclick.config import BaseConfig


class ChatGPTPlanner(Planner):
    def __init__(self, c: BaseConfig):
        # Get the prompts
        prompts = c.prompts
        system_instruction = (
            f"{prompts['common-planner-prompt']}\n{prompts['specific-planner-prompt']}"
        )
        planner_config = c.models.get("planner_config")
        openai.api_key = planner_config.get("api_key")
        openai.azure_endpoint = planner_config.get("azure_endpoint")
        openai.api_type = planner_config.get("api_type")
        openai.api_version = planner_config.get("api_version")
        base_url = planner_config.get("base_url")
        if base_url:
            openai.base_url = base_url
        self.model_name = planner_config.get("model_name")
        self.functions = c.function_declarations

        self.system_instruction = system_instruction
        self.chat_history = [{"role": "system", "content": system_instruction}]

    def build_prompt(self, query_text=None, base64_image=None):
        # Handle case when base64_image is None or empty
        if not base64_image:
            if query_text is None:
                return [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "No screenshot available - device may not be connected"},
                        ],
                    }
                ]
            else:
                return [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": query_text},
                        ],
                    }
                ]
        
        # Normal case with valid screenshot
        if query_text is None:
            return [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "low",
                            },
                        }
                    ],
                }
            ]
        else:
            return [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "low",
                            },
                        },
                    ],
                }
            ]

    def llm_response(self, prompt=None, screenshot=None) -> list[tuple[str, dict]]:
        # Remove all prev screenshots
        new_chat_history = []
        for message in self.chat_history:
            if message["role"] == "user" and any(
                item["type"] == "image_url" for item in message["content"]
            ):

                filtered_content = [
                    item for item in message["content"] if item["type"] != "image_url"
                ]
                new_chat_history.append({"role": message["role"], "content": filtered_content})

            else:
                new_chat_history.append(message)
        # Append the current prompt to the chat history
        if screenshot:
            prompt_with_image = self.build_prompt(
                prompt, f"{screenshot}"
            )  # data:image/jpeg;base64,
            new_chat_history.extend(prompt_with_image)
        else:
            new_chat_history.extend(self.build_prompt(prompt))
        self.chat_history = new_chat_history

        completion = openai.chat.completions.create(
            model=self.model_name,
            messages=self.chat_history,
            tools=[
                {
                    "type": "function",
                    "function": {
                        **fn,
                        "parameters": {**fn["parameters"], "additionalProperties": False},
                        "strict": True,
                    },
                }
                for fn in self.functions
            ],
            tool_choice="required"
        )
        print(completion)
        response_message = completion.choices[0].message
        function_name = None
        function_args = None
        list_of_functions_to_call = []
        for tool in response_message.tool_calls:
            function_name = tool.function.name
            function_args = json.loads(tool.function.arguments)
            self.chat_history.append(
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Function: {function_name} with args: {function_args}",
                        }
                    ],
                }
            )
            list_of_functions_to_call.append((function_name, function_args))

        print(list_of_functions_to_call)

        if len(list_of_functions_to_call) == 0:
            list_of_functions_to_call.append((None, None))
        return list_of_functions_to_call

    def add_finder_message(self, message):
        self.chat_history.append({"role": "user", "content": [{"type": "text", "text": message}]})

    def task_finished(self, reason: str, observation: str):
        logger.info(f"Task finished with reason: {reason}")
