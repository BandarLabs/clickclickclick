import anthropic
from . import BaseFinder, FinderResponseLLM
from clickclickclick.config import BaseConfig
from clickclickclick.executor import Executor
from tempfile import NamedTemporaryFile
import json


class AnthropicFinder(BaseFinder):

    def __init__(self, c: BaseConfig, executor: Executor):
        prompts = c.prompts
        system_prompt = prompts["finder-system-prompt"]
        finder_config = c.models.get("finder_config")
        self.element_finder_prompt = c.element_finder_prompt
        self.IMAGE_WIDTH = finder_config.get("image_width")
        self.IMAGE_HEIGHT = finder_config.get("image_height")
        self.OUTPUT_WIDTH = finder_config.get("output_width")
        self.OUTPUT_HEIGHT = finder_config.get("output_height")
        api_key = finder_config.get("api_key")
        model_name = finder_config.get("model_name")
        generation_config = finder_config.get("generation_config")
        super().__init__(api_key, model_name, generation_config, system_prompt, executor)
        self.client = anthropic.Anthropic(api_key=api_key)

    def process_segment(self, segment, model_name, prompt):
        segment_image, coordinates = segment

        with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            segment_image.save(temp_file, format="PNG")
            temp_file_path = temp_file.name

        encoded_image = self.encode_image_to_base64(temp_file_path)

        # Create the message with image and text
        message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": encoded_image,
                    },
                },
                {"type": "text", "text": self.element_finder_prompt(prompt)},
            ],
        }

        # Define the response schema as a tool
        tools = [
            {
                "name": "return_coordinates",
                "description": "Return the bounding box coordinates of the found element",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ymin": {"type": "integer", "description": "Top coordinate"},
                        "ymax": {"type": "integer", "description": "Bottom coordinate"},
                        "xmin": {"type": "integer", "description": "Left coordinate"},
                        "xmax": {"type": "integer", "description": "Right coordinate"}
                    },
                    "required": ["ymin", "ymax", "xmin", "xmax"]
                }
            }
        ]

        try:
            response = self.client.messages.create(
                model=model_name,
                max_tokens=1024,
                system=self.system_prompt,
                messages=[message],
                tools=tools,
                tool_choice={"type": "tool", "name": "return_coordinates"}
            )

            # Extract tool use from response
            for content in response.content:
                if content.type == "tool_use" and content.name == "return_coordinates":
                    coords = content.input
                    response_text = json.dumps(coords)
                    print(response_text, " resp text")
                    return (response_text, coordinates)
            
            # Fallback if no tool use found
            return ('{"ymin": 0, "xmin": 0, "ymax": 0, "xmax": 0}', coordinates)
            
        except Exception as e:
            print("Error processing segment:", e)
            return ('{"ymin": 0, "xmin": 0, "ymax": 0, "xmax": 0}', coordinates) 