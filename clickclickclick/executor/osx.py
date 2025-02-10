from . import Executor
from typing import List, Union
import logging
import io
import base64
from PIL import Image
from tempfile import NamedTemporaryFile
from . import logger

try:
    import pyautogui
    import applescript
except Exception as e:
    print(f"warn: import error in osx.py {e}")


class MacExecutor(Executor):
    def __init__(self):
        super().__init__()
        self.screenshot_as_base64 = False
        self.screenshot_as_tempfile = False

    def move_mouse(self, x: int, y: int, observation: str) -> bool:
        try:
            logger.debug(f"move mouse x y {x} {y}")
            pyautogui.moveTo(y, x, 1)
            return True
        except Exception as e:
            logger.exception("Error in move_mouse")
            return False

    def press_key(self, keys: List[str], observation: str) -> bool:
        try:
            logger.debug(f"press keys {keys}")
            pyautogui.hotkey(*[k.lower() for k in keys])
            return True
        except Exception as e:
            logger.exception("Error in press_key")
            return False

    def type_text(self, text: str, observation: str) -> bool:
        try:
            logger.debug(f"type text {text}")
            pyautogui.write(text)
            return True
        except Exception as e:
            logger.exception("Error in type_text")
            return False

    def click_mouse(self, observation: str, button: str = "left") -> bool:
        try:
            logger.debug(f"click mouse {button}")
            pyautogui.click(button=button)
            return True
        except Exception as e:
            logger.exception("Error in click_mouse")
            return False

    def double_click_mouse(self, button: str, observation: str) -> bool:
        try:
            logger.debug(f"doubleclick mouse {button}")
            pyautogui.doubleClick(button=button)
            return True
        except Exception as e:
            logger.exception("Error in double_click_mouse")
            return False

    def scroll(self, clicks: int, observation: str) -> bool:
        try:
            logger.debug(f"scroll {clicks}")
            pyautogui.scroll(clicks)
            return True
        except Exception as e:
            logger.exception("Error in scroll")
            return False

    def click_at_a_point(self, x: int, y: int, observation: str) -> bool:
        try:
            logger.debug(f"click at a point x y {x} {y}")
            pyautogui.click(x=y, y=x, duration=1)
            return True
        except Exception as e:
            logger.exception("Error in click_at_a_point")
            return False

    def long_press_at_a_point(self, x: int, y: int, observation: str, duration: int = 1000):
        raise NotImplementedError("Long press is not implemented on Mac")

    def swipe_left(self, observation: str) -> bool:
        raise NotImplementedError("Swipe left is not implemented on Mac")

    def swipe_right(self, observation: str) -> bool:
        raise NotImplementedError("Swipe right is not implemented on Mac")

    def swipe_up(self, observation: str) -> bool:
        raise NotImplementedError("Swipe up is not implemented on Mac")

    def swipe_down(self, observation: str) -> bool:
        raise NotImplementedError("Swipe down is not implemented on Mac")

    def volume_up(self, observation: str) -> bool:
        raise NotImplementedError("Volume up is not implemented on Mac")

    def volume_down(self, observation: str) -> bool:
        raise NotImplementedError("Volume down is not implemented on Mac")

    def navigate_back(self, observation: str) -> bool:
        raise NotImplementedError("Navigate back is not implemented on Mac")

    def minimize_app(self, observation: str) -> bool:
        raise NotImplementedError("Minimize app is not implemented on Mac")

    def screenshot(
        self, observation: str, as_base64: bool = False, use_tempfile: bool = False
    ) -> Union[Image.Image, str, tuple]:
        """
        Takes a screenshot.

        Args:
            as_base64 (bool): Whether to return the screenshot as a base64-encoded string. Defaults to False.
            use_tempfile (bool): Whether to use a temporary file for storing the screenshot. Defaults to False.

        Returns:
            Union[Image.Image, str, tuple]: The screenshot as a PIL Image object, a base64-encoded string,
                                             or a tuple containing the PIL Image object and the file path if use_tempfile is True.
        """
        try:
            logger.debug(f"Take a screenshot use_tempfile={use_tempfile}")
            screenshot = pyautogui.screenshot()
            if use_tempfile or self.screenshot_as_tempfile:
                with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                    screenshot.save(temp_file, format="PNG")
                    temp_file_path = temp_file.name
                return temp_file_path

            if as_base64 or self.screenshot_as_base64:
                buffered = io.BytesIO()
                screenshot.save(buffered, format="PNG")
                base64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                return base64_str

            return screenshot
        except Exception as e:
            logger.exception("Error in screenshot")
            return "" if as_base64 or use_tempfile else None

    def apple_script(self, script: str, observation: str) -> bool:
        try:
            logger.debug(f"Run apple script {script}")
            result = applescript.AppleScript(script).run()
            logger.info(result)
            return True
        except Exception as e:
            logger.exception(f"Error in apple_script {e}")
            return False
