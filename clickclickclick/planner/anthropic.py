import anthropic
from typing import Any
from . import Planner, logger
import json
from clickclickclick.config import BaseConfig


class AnthropicPlanner(Planner):
    def __init__(self, c: BaseConfig):
        # Get the prompts
        prompts = c.prompts
        system_instruction = (
            f"{prompts['common-planner-prompt']}\n{prompts['specific-planner-prompt']}"
        )
        planner_config = c.models.get("planner_config")
        api_key = planner_config.get("api_key")
        self.model_name = planner_config.get("model_name")
        self.functions = c.function_declarations

        self.client = anthropic.Anthropic(api_key=api_key)
        self.system_instruction = system_instruction
        self.chat_history = []

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
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
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
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
                            },
                        },
                    ],
                }
            ]

    def llm_response(self, prompt=None, screenshot=None) -> list[tuple[str, dict]]:
        # Remove all prev screenshots from chat history
        new_chat_history = []
        for message in self.chat_history:
            if message["role"] == "user" and any(
                item["type"] == "image" for item in message["content"] if isinstance(item, dict)
            ):
                filtered_content = [
                    item for item in message["content"] if isinstance(item, dict) and item["type"] != "image"
                ]
                if filtered_content:
                    new_chat_history.append({"role": message["role"], "content": filtered_content})
            else:
                new_chat_history.append(message)
        
        # Append the current prompt to the chat history
        if screenshot:
            prompt_with_image = self.build_prompt(prompt, f"{screenshot}")
            new_chat_history.extend(prompt_with_image)
        else:
            new_chat_history.extend(self.build_prompt(prompt))
        
        self.chat_history = new_chat_history

        # Convert function declarations to Anthropic tool format
        tools = []
        for fn in self.functions:
            tool = {
                "name": fn["name"],
                "description": fn["description"],
                "input_schema": fn["parameters"]
            }
            tools.append(tool)

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=1024,
            system=self.system_instruction,
            messages=self.chat_history,
            tools=tools,
            tool_choice={"type": "any"}
        )
        
        print(response)
        
        list_of_functions_to_call = []
        
        # Handle tool calls in Anthropic response
        for content in response.content:
            if content.type == "tool_use":
                function_name = content.name
                function_args = content.input
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