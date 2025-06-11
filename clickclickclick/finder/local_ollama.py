from clickclickclick.config import BaseConfig
from . import BaseFinder, logger
from ollama import Client
from clickclickclick.executor import Executor
from tempfile import NamedTemporaryFile


class OllamaFinder(BaseFinder):

    def __init__(self, c: BaseConfig, executor: Executor, host=None):
        if host is None:
            host = "http://localhost:11434"
        self.client = Client(host=host)

        self.executor = executor
        prompts = c.prompts
        self.element_finder_prompt = c.element_finder_prompt
        self.system_prompt = prompts["finder-system-prompt"]
        finder_config = c.models.get("finder_config")
        self.IMAGE_WIDTH = finder_config.get("image_width")
        self.IMAGE_HEIGHT = finder_config.get("image_height")
        self.OUTPUT_WIDTH = finder_config.get("output_width")
        self.OUTPUT_HEIGHT = finder_config.get("output_height")
        self.model_name = finder_config.get("model_name")

    def process_segment(self, segment, model_name, prompt):
        segment_image, coordinates = segment

        with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            segment_image.save(temp_file, format="PNG")
            temp_file_path = temp_file.name

        response = self.client.chat(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt,
                },
                {
                    "role": "user",
                    "content": self.element_finder_prompt(prompt),
                    "images": [temp_file_path],
                },
            ],
        )
        try:
            response_text = response["message"]["content"]
            logger.debug(response_text)
            return (response_text, coordinates)
        except Exception as e:
            logger.error("Error processing segment:", e)
            return ("", coordinates)
