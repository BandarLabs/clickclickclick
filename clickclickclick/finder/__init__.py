from abc import ABC, abstractmethod
from typing import List
import subprocess
import re
import base64
import json
import logging
from clickclickclick.executor import Executor
from PIL import Image
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class FinderResponseLLM(BaseModel):
    ymin: int
    ymax: int
    xmin: int
    xmax: int


class BaseFinder(ABC):
    IMAGE_WIDTH = None
    IMAGE_HEIGHT = None
    OUTPUT_WIDTH = None
    OUTPUT_HEIGHT = None

    def __init__(self, api_key, model_name, generation_config, system_prompt, executor: Executor):
        self.model_name = model_name
        self.generation_config = generation_config
        self.system_prompt = system_prompt
        self.executor = executor

    def encode_image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string

    def resize(self, image, new_size):
        if new_size:
            target_width, target_height = new_size, new_size
            resized_image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            segments = [(resized_image, (0, 0, target_width, target_height))]
            total_width, total_height = target_width, target_height
        return segments, total_width, total_height

    @abstractmethod
    def process_segment(self, segment, model, prompt):
        pass

    def find_element(self, prompt, observation: str) -> str:
        new_size = self.IMAGE_WIDTH  # assuming square image size
        logger.info(prompt)
        screenshot = self.executor.screenshot(observation, False, True)
        image = Image.open(screenshot)

        segments, total_width, total_height = self.resize(image, new_size=new_size)

        results = [self.process_segment(segments[0], self.model_name, prompt)]
        i = 0
        ans = "0,0,0,0"
        for response, coordinates in results:
            i += 1
            print(coordinates, i)

            try:
                response_dict = json.loads(response)
                ymin = int(response_dict["ymin"])
                xmin = int(response_dict["xmin"])
                ymax = int(response_dict["ymax"])
                xmax = int(response_dict["xmax"])
                if ymin == 0 and xmin == 0 and xmax == 0 and ymax == 0:
                    continue
                orig_left, orig_top, _, _ = coordinates

                y_min_percent = (orig_top + ymin) / self.OUTPUT_HEIGHT * self.IMAGE_HEIGHT
                x_min_percent = (orig_left + xmin) / self.OUTPUT_WIDTH * self.IMAGE_WIDTH
                y_max_percent = (orig_top + ymax) / self.OUTPUT_HEIGHT * self.IMAGE_HEIGHT
                x_max_percent = (orig_left + xmax) / self.OUTPUT_WIDTH * self.IMAGE_WIDTH
                ans = ",".join(
                    map(
                        str,
                        map(
                            int,
                            [
                                y_min_percent,
                                x_min_percent,
                                y_max_percent,
                                x_max_percent,
                            ],
                        ),
                    )
                )
                print(ans)
            except json.JSONDecodeError:
                print("Could not decode response")

        return ans

    def scale_coordinates(self, coordinates: List[int]) -> List[int]:
        try:
            # Execute adb shell command to get the screen size
            result = subprocess.run(["adb", "shell", "wm", "size"], stdout=subprocess.PIPE)
            output = result.stdout.decode()
            # Example output format: 'Physical size: 1080x1920'
            match = re.search(r"Physical size: (\d+)x(\d+)", output)
            if match:
                screen_x, screen_y = map(int, match.groups())
            else:
                raise Exception("Failed to parse screen size from adb output.")
        except Exception as e:
            # Attempt to get screen size using pyautogui (for desktops)
            import pyautogui
            screen_x, screen_y = pyautogui.size()

        print(f"Screen size: x y {screen_x} {screen_y}")
        scaling_x = screen_x / self.IMAGE_WIDTH
        scaling_y = screen_y / self.IMAGE_HEIGHT
        coordinates[0] = int(coordinates[0] * scaling_y)
        coordinates[2] = int(coordinates[2] * scaling_y)
        coordinates[1] = int(coordinates[1] * scaling_x)
        coordinates[3] = int(coordinates[3] * scaling_x)

        if scaling_x < scaling_y:
            # For mobile: swap coordinates[0] with coordinates[1] and coordinates[2] with coordinates[3]
            coordinates[0], coordinates[1] = coordinates[1], coordinates[0]
            coordinates[2], coordinates[3] = coordinates[3], coordinates[2]

        return coordinates
