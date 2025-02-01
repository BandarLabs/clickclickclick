import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Callable, Any, Generator, List

from . import logger
from clickclickclick.config import BaseConfig
from clickclickclick.executor import Executor
from clickclickclick.finder import BaseFinder
from . import Planner
import tempfile
import base64

def create_tempfile_from_base64(base64_string):
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(base64.b64decode(base64_string))
    tmp.close()
    return tmp.name

def save_screenshot(screenshot, is_base64):
    if is_base64:
        path = create_tempfile_from_base64(screenshot)
        return path
    return screenshot

def execute_task(
    prompt: str, executor: Executor, planner: Planner, finder: BaseFinder, c: BaseConfig
) -> bool:
    try:

        while True:
            screenshot = executor.screenshot(
                "Planner took screenshot",
                executor.screenshot_as_base64,
                executor.screenshot_as_tempfile,
            )
            logger.info("Generated screenshot")
            time.sleep(c.TASK_DELAY)

            llm_responses = planner.llm_response(prompt, screenshot)
            for func_name, func_args in llm_responses:
                finder_output = None
                logger.debug(f"Executing {func_name} with {func_args}")
                (execution_output, executed_fn_name) = parse_and_execute(
                    func_name, func_args, executor, planner, finder
                )
                if executed_fn_name == "task_finished":
                    return True

                if executed_fn_name == "find_element_and_click":
                    logger.info(f"Executed Finder with output: {execution_output}")
                    ui_element = func_args.get("prompt", "")
                    finder_output = execution_output

                if executed_fn_name == "find_element_and_long_press":
                    logger.info(f"Executed Finder with output: {execution_output}")
                    ui_element = func_args.get("prompt", "")
                    finder_output = execution_output

                if finder_output is not None:

                    coordinates = list(map(int, finder_output.split(",")))
                    scaled_coordinates = finder.scale_coordinates(coordinates)

                    if executed_fn_name == "find_element_and_click":
                        executor.click_at_a_point(
                            (coordinates[0] + coordinates[2]) // 2,
                            (coordinates[1] + coordinates[3]) // 2,
                            "Clicking center right away",
                        )
                        message_text = "and it has been clicked"
                    elif executed_fn_name == "find_element_and_long_press":

                        executor.long_press_at_a_point(
                            (coordinates[0] + coordinates[2]) // 2,
                            (coordinates[1] + coordinates[3]) // 2,
                            "Clicking center right away",
                        )
                        message_text = "and it has been long pressed"

                    finder_output = ",".join(map(str, scaled_coordinates))
                    message = f"The UI bounds of the {ui_element} is {finder_output} {message_text}"
                    planner.add_finder_message(message)

                observation = func_args.get("observation", "")

    except Exception as e:
        logger.exception("An error occurred during task execution.")
        return False
        # raise e

def execute_task_with_generator(
    prompt: str, executor: Executor, planner: Planner, finder: BaseFinder, c: BaseConfig
) -> Generator[List[str], None, bool]:
    try:
        observation = ""
        while True:
            screenshot = executor.screenshot(
                "Planner took screenshot",
                executor.screenshot_as_base64,
                executor.screenshot_as_tempfile,
            )
            logger.info("Generated screenshot")
            time.sleep(c.TASK_DELAY)

            if executor.screenshot_as_base64:
                yield [(create_tempfile_from_base64(screenshot), observation)]
            else:
                yield [(screenshot, observation)]
            llm_responses = planner.llm_response(prompt, screenshot)
            for func_name, func_args in llm_responses:
                finder_output = None
                logger.debug(f"Executing {func_name} with {func_args}")
                (execution_output, executed_fn_name) = parse_and_execute(
                    func_name, func_args, executor, planner, finder
                )
                if executed_fn_name == "task_finished":
                    return True

                if executed_fn_name == "find_element_and_click":
                    logger.info(f"Executed Finder with output: {execution_output}")
                    ui_element = func_args.get("prompt", "")
                    finder_output = execution_output

                if executed_fn_name == "find_element_and_long_press":
                    logger.info(f"Executed Finder with output: {execution_output}")
                    ui_element = func_args.get("prompt", "")
                    finder_output = execution_output

                if finder_output is not None:
                    coordinates = list(map(int, finder_output.split(",")))
                    scaled_coordinates = finder.scale_coordinates(coordinates)

                    if executed_fn_name == "find_element_and_click":
                        executor.click_at_a_point(
                            (coordinates[0] + coordinates[2]) // 2,
                            (coordinates[1] + coordinates[3]) // 2,
                            "Clicking center right away",
                        )
                        message_text = "and it has been clicked"
                    elif executed_fn_name == "find_element_and_long_press":
                        executor.long_press_at_a_point(
                            (coordinates[0] + coordinates[2]) // 2,
                            (coordinates[1] + coordinates[3]) // 2,
                            "Clicking center right away",
                        )
                        message_text = "and it has been long pressed"

                    finder_output = ",".join(map(str, scaled_coordinates))
                    message = f"The UI bounds of the {ui_element} is {finder_output} {message_text}"
                    planner.add_finder_message(message)

                observation = func_args.get("observation", "")

    except Exception as e:
        logger.exception("An error occurred during task execution.")
        raise e


# TODO: move to utils
def execute_with_timeout(task, timeout, *args, **kwargs):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(task, *args, **kwargs)
        try:
            result = future.result(timeout=timeout)
            return result
        except TimeoutError:
            logger.exception("Task did not complete within the timeout period.")
            return None


def parse_and_execute(
    function_name: str, function_args: dict, executor: object, planner: object, finder: object
) -> Any:
    func_name = function_name
    args = function_args if function_args is not None else []

    func = get_function(func_name, executor, planner, finder)
    return (func(**args), func_name)


def get_function(
    name: str, executor: Executor, planner: Planner, finder: BaseFinder
) -> Callable[..., Any]:
    funcs = {
        "screenshot": executor.screenshot,
        "find_element_and_click": finder.find_element,
        "find_element_and_long_press": finder.find_element,
        "move_mouse": executor.move_mouse,
        "click_mouse": executor.click_mouse,
        "type_text": executor.type_text,
        "double_click_mouse": executor.double_click_mouse,
        "right_click_mouse": lambda: executor.click_mouse(button="right"),
        "scroll_mouse": executor.scroll,
        "press_key": executor.press_key,
        "click_at_a_point": executor.click_at_a_point,
        "long_press_at_a_point": executor.long_press_at_a_point,
        # "apple_script": executor.apple_script,
        "task_finished": planner.task_finished,
        "swipe_right": executor.swipe_right,
        "swipe_left": executor.swipe_left,
        "swipe_up": executor.swipe_up,
        "swipe_down": executor.swipe_down,
        "navigate_back": executor.navigate_back,
        "minimize_app": executor.minimize_app,
        "volume_up": executor.volume_up,
        "volume_down": executor.volume_down,
    }
    func = funcs.get(name)
    if func is None:
        raise ValueError(f"No such function: {name}")
    return func
