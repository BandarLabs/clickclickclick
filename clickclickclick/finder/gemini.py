import google.generativeai as genai
from . import BaseFinder
from clickclickclick.config import BaseConfig
from clickclickclick.executor import Executor
from tempfile import NamedTemporaryFile
from PIL import Image


class GeminiFinder(BaseFinder):

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
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=system_prompt,
        )

    def process_segment(self, segment, model, prompt, retries=3):
        attempt = 0
        segment_image, coordinates = segment
        while attempt < retries:
            try:
                with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    segment_image.save(temp_file, format="PNG")
                    temp_file_path = temp_file.name

                with Image.open(temp_file_path) as segment_image:
                    response = self.model.generate_content(
                        [segment_image, self.element_finder_prompt(prompt)]
                    )
                    response_text = response.text
                    print(response_text, " resp text")
                    return (response_text, coordinates)
            except Exception as e:
                # Log the exception or handle it as necessary
                print(f"Attempt {attempt + 1} failed with exception: {e}")

                # Increment the attempt counter
                attempt += 1
        raise Exception("Failed to process segment after several retries")
