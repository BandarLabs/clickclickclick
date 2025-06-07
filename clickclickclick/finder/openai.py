import openai
from . import BaseFinder, FinderResponseLLM
from clickclickclick.config import BaseConfig
from clickclickclick.executor import Executor
from tempfile import NamedTemporaryFile


class OpenAIFinder(BaseFinder):

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
        openai.api_key = api_key
        openai.azure_endpoint = finder_config.get("azure_endpoint")
        openai.api_type = finder_config.get("api_type")
        openai.api_version = finder_config.get("api_version")
        base_url = finder_config.get("base_url")
        if base_url:
            openai.base_url = base_url

    def process_segment(self, segment, model_name, prompt):
        segment_image, coordinates = segment

        with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            segment_image.save(temp_file, format="PNG")
            temp_file_path = temp_file.name

        encoded_image = self.encode_image_to_base64(temp_file_path)

        response = openai.beta.chat.completions.parse(
            model=model_name,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "detail": "low",
                                "url": f"data:image/png;base64,{encoded_image}",
                            },
                        },
                        {"type": "text", "text": self.element_finder_prompt(prompt)},
                    ],
                },
            ],
            response_format=FinderResponseLLM,
        )
        try:
            response_text = response.choices[0].message.content
            print(response_text, " resp text")
            return (response_text, coordinates)
        except Exception as e:
            print("Error processing segment:", e)
            return ("", coordinates)
