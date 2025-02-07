from clickclickclick.config import BaseConfig
from . import BaseFinder, logger
try:
    from mlx_vlm import load, generate
    from mlx_vlm.prompt_utils import apply_chat_template
    from mlx_vlm.utils import load_config
except Exception as e:
    print(f"warn: mlx-vlm import issue {e}")
from tempfile import NamedTemporaryFile
import re
import json
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def extract_coordinates(response_text):
    # Attempt to find key-value pairs first
    pattern = r'(\w+)\s*[:=]\s*"?(\d*\.\d+|\d+)"?'
    matches = re.findall(pattern, response_text)

    # If matches are found, process as key-value pairs
    if matches:
        coordinates_dict = {}
        for match in matches:
            key = match[0]
            value = match[1]
            coordinates_dict[key] = float(value)
    else:
        # Assume input is a comma-separated list of values in the order ymin,ymax,xmin,xmax
        try:
            values = [float(value.strip()) for value in response_text.split(',')]
        except ValueError as e:
            logger.info(e)
            return json.dumps({"ymin": 0, "ymax": 0, "xmin": 0, "xmax": 0})
        if len(values) == 4:
            coordinates_dict = {
                'ymin': values[0],
                'ymax': values[1],
                'xmin': values[2],
                'xmax': values[3]
            }
        else:
            # Handle error case where input doesn't match expected format
            raise ValueError("Input does not contain valid key-value pairs or valid coordinate list.")

    # Define the normalization mapping
    conversion_map = {
        'x1': 'xmin',
        'y1': 'ymin',
        'x2': 'xmax',
        'y2': 'ymax'
    }

    # Transform the extracted coordinates into a standardized format
    standardized_coordinates = {conversion_map.get(key, key): value for key, value in coordinates_dict.items()}

    # Convert the standardized dictionary to a JSON string
    response_json = json.dumps(standardized_coordinates)

    return response_json

class MLXFinder(BaseFinder):
    def __init__(self, c: BaseConfig, executor):
        self.executor = executor
        finder_config = c.models.get("finder_config")
        model_path = finder_config.get("model_path")
        self.config = load_config(model_path)
        self.model, self.processor = load(model_path, {"trust_remote_code": True})
        # self.image_finder_prompt = c.prompts["image-finder-prompt"]
        self.system_prompt = c.prompts["finder-system-prompt"]

        self.IMAGE_WIDTH = finder_config.get("image_width")
        self.IMAGE_HEIGHT = finder_config.get("image_height")
        self.OUTPUT_WIDTH = finder_config.get("output_width")
        self.OUTPUT_HEIGHT = finder_config.get("output_height")
        self.model_name = finder_config.get("model_name")

    def process_image(self, image_path, prompt):
        formatted_prompt = apply_chat_template(
            self.processor, self.config, prompt, num_images=1
        )
        output = generate(self.model, self.processor, [image_path], formatted_prompt, verbose=False)
        print(output)
        try:
            logger.debug(output)
            return output
        except Exception as e:
            logger.error("Error processing image:", e)
            return ""

    # Example usage
    def process_segment(self, segment, model_name, prompt):
        prompt = f'UI bounds of "{prompt}" as ymin=,ymax=,xmin=,xmax= format strictly.  '
        segment_image, coordinates = segment
        with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            segment_image.save(temp_file, format="PNG")
            temp_file_path = temp_file.name
            response_text = self.process_image(temp_file_path, prompt)
            response_json_str = extract_coordinates(response_text)

            return (response_json_str, coordinates)

# Example instantiation and usage would resemble how you manage the base classes and client interactions.