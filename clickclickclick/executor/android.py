from . import Executor
from subprocess import CompletedProcess, run
import subprocess
from typing import List, Union
import io
import base64
from PIL import Image
from tempfile import NamedTemporaryFile
import shlex
from . import logger


def run_adb_command(command: List[str], text_mode: bool = True) -> CompletedProcess:
    """Runs adb command and returns the completed process."""
    result = run(
        ["adb"] + command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text_mode,
    )
    if result.returncode != 0:
        logger.error(
            f"adb command {' '.join(command)} failed: {result.stderr.decode('utf-8').strip()}"
        )
    return result


def sanitize_for_adb(text: str) -> str:
    # Replace spaces with %s
    text = text.replace(" ", "%s")
    # Use shlex.quote to handle special shell characters
    return shlex.quote(text)


class AndroidExecutor(Executor):
    def __init__(self):
        super().__init__()
        self.screenshot_as_base64 = False
        self.screenshot_as_tempfile = False

    def click_mouse(observation: str):
        raise NotImplementedError("click mouse is not available in android")

    def double_click_mouse(observation: str):
        raise NotImplementedError("double click mouse is not available in android")

    def move_mouse(self, x: int, y: int, observation: str) -> bool:
        try:
            logger.debug(f"move mouse x y {x} {y}")
            run_adb_command(["shell", "input", "tap", str(x), str(y)])
            return True
        except Exception as e:
            logger.exception("Error in move_mouse")
            return False

    def press_key(self, keys: List[str], observation: str) -> bool:
        try:
            logger.debug(f"press keys {keys}")
            for key in keys:
                run_adb_command(["shell", "input", "keyevent", key.upper()])
            return True
        except Exception as e:
            logger.exception("Error in press_key")
            return False

    def type_text(self, text: str, observation: str) -> bool:
        try:
            logger.debug(f"type text {text}")
            multiline_texts = text.split("\n")
            for text in multiline_texts:
                if text == "":  # due to newline
                    run_adb_command(["shell", "input", "keyevent", "66"])
                else:
                    sanitized_text = sanitize_for_adb(text)
                    run_adb_command(["shell", "input", "text", sanitized_text])
            # todo confirm if needed
            run_adb_command(["shell", "input", "keyevent", "66"])
            return True
        except Exception as e:
            logger.exception("Error in type_text")
            return False

    def scroll(self, clicks: int, observation: str) -> bool:
        try:
            logger.debug(f"scroll {clicks}")
            # Perform swipe to simulate scroll
            if clicks > 0:
                # Scroll up
                run_adb_command(["shell", "input", "swipe", "500", "1500", "500", "500"])
            else:
                # Scroll down
                run_adb_command(["shell", "input", "swipe", "500", "500", "500", "1500"])
            return True
        except Exception as e:
            logger.exception("Error in scroll")
            return False

    def swipe_left(self, observation: str) -> bool:
        try:
            logger.debug("swipe left")
            run_adb_command(["shell", "input", "swipe", "700", "1000", "100", "1000"])
            return True
        except Exception as e:
            logger.exception("Error in swipe_left")
            return False

    def swipe_right(self, observation: str) -> bool:
        try:
            logger.debug("swipe right")
            run_adb_command(["shell", "input", "swipe", "100", "1000", "700", "1000"])
            return True
        except Exception as e:
            logger.exception("Error in swipe_right")
            return False

    def volume_up(self, observation: str) -> bool:
        try:
            logger.debug("volume up")
            run_adb_command(["shell", "input", "keyevent", "KEYCODE_VOLUME_UP"])
            return True
        except Exception as e:
            logger.exception("Error in volume_up")
            return False

    def volume_down(self, observation: str) -> bool:
        try:
            logger.debug("volume down")
            run_adb_command(["shell", "input", "keyevent", "KEYCODE_VOLUME_DOWN"])
            return True
        except Exception as e:
            logger.exception("Error in volume_down")
            return False

    def swipe_up(self, observation: str) -> bool:
        try:
            logger.debug("swipe up")
            run_adb_command(["shell", "input", "swipe", "500", "1500", "500", "500"])
            return True
        except Exception as e:
            logger.exception("Error in swipe_up")
            return False

    def swipe_down(self, observation: str) -> bool:
        try:
            logger.debug("swipe down")
            run_adb_command(["shell", "input", "swipe", "500", "500", "500", "1500"])
            return True
        except Exception as e:
            logger.exception("Error in swipe_down")
            return False

    def navigate_back(self, observation: str) -> bool:
        try:
            logger.debug("navigate back")
            run_adb_command(["shell", "input", "keyevent", "KEYCODE_BACK"])
            return True
        except Exception as e:
            logger.exception("Error in navigate_back")
            return False

    def minimize_app(self, observation: str) -> bool:
        try:
            logger.debug("minimize app")
            run_adb_command(["shell", "input", "keyevent", "KEYCODE_HOME"])
            return True
        except Exception as e:
            logger.exception("Error in minimize_app")
            return False

    def click_at_a_point(self, x: int, y: int, observation: str) -> bool:
        try:
            logger.debug(f"click at a point x y {x} {y}")
            run_adb_command(["shell", "input", "tap", str(x), str(y)])
            return True
        except Exception as e:
            logger.exception("Error in click_at_a_point")
            return False

    def long_press_at_a_point(self, x: int, y: int, observation: str, duration: int = 1000) -> bool:
        try:
            logger.debug(f"Long press at a point x y {x} {y} for duration {duration}")
            run_adb_command(["shell", "input", "swipe", str(x), str(y), str(x), str(y), str(duration)])
            return True
        except Exception as e:
            logger.exception("Error in long_press_at_a_point")
            return False

    def screenshot(
        self, observation: str, as_base64: bool = False, use_tempfile: bool = False
    ) -> Union[Image.Image, str, tuple]:
        try:
            logger.debug(f"Take a screenshot use_tempfile={use_tempfile}")
            result = run_adb_command(["exec-out", "screencap", "-p"], text_mode=False)
            if result.returncode != 0:
                return "" if as_base64 or use_tempfile else None

            screenshot = Image.open(io.BytesIO(result.stdout))

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

    def run_shell_command(self, command: str) -> bool:
        try:
            logger.debug(f"Run shell command {command}")
            result = run_adb_command(["shell", command])
            logger.info(result)
            return True
        except Exception as e:
            logger.exception(f"Error in run_shell_command {e}")
            return False
