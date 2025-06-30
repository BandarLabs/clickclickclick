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


def _process_finder_output(
    executed_fn_name: str,
    execution_output: str,
    func_args: dict,
    executor: Executor,
    finder: BaseFinder,
    planner: Planner,
) -> None:
    """Process finder output and execute appropriate action."""
    if executed_fn_name not in ["find_element_and_click", "find_element_and_long_press"]:
        return

    logger.info(f"Executed Finder with output: {execution_output}")
    ui_element = func_args.get("prompt", "")

    try:
        coordinates = list(map(int, execution_output.split(",")))
        scaled_coordinates = finder.scale_coordinates(coordinates)

        center_x = (coordinates[0] + coordinates[2]) // 2
        center_y = (coordinates[1] + coordinates[3]) // 2

        if executed_fn_name == "find_element_and_click":
            executor.click_at_a_point(center_x, center_y, "Clicking center right away")
            message_text = "and it has been clicked"
        elif executed_fn_name == "find_element_and_long_press":
            executor.long_press_at_a_point(center_x, center_y, "Long pressing center")
            message_text = "and it has been long pressed"

        scaled_output = ",".join(map(str, scaled_coordinates))
        message = f"The UI bounds of the {ui_element} is {scaled_output} {message_text}"
        planner.add_finder_message(message)

    except (ValueError, IndexError) as e:
        logger.error(f"Invalid finder output format: {execution_output}, error: {e}")


def _execute_task_step(
    prompt: str, executor: Executor, planner: Planner, finder: BaseFinder, c: BaseConfig
) -> bool:
    """Execute a single step of the task."""
    screenshot = executor.screenshot(
        "Planner took screenshot",
        executor.screenshot_as_base64,
        executor.screenshot_as_tempfile,
    )
    logger.info("Generated screenshot")
    time.sleep(c.TASK_DELAY)

    llm_responses = planner.llm_response(prompt, screenshot)
    for func_name, func_args in llm_responses:
        logger.debug(f"Executing {func_name} with {func_args}")

        try:
            execution_output, executed_fn_name = parse_and_execute(
                func_name, func_args, executor, planner, finder
            )

            if executed_fn_name == "task_finished":
                return True

            if executed_fn_name in ["find_element_and_click", "find_element_and_long_press"]:
                _process_finder_output(
                    executed_fn_name, execution_output, func_args, executor, finder, planner
                )

        except Exception as e:
            logger.error(f"Error executing function {func_name}: {e}")
            continue

    return False


def execute_task(
    prompt: str, executor: Executor, planner: Planner, finder: BaseFinder, c: BaseConfig
) -> bool:
    """Execute a task with proper error handling and logging."""
    try:
        while True:
            if _execute_task_step(prompt, executor, planner, finder, c):
                return True

    except KeyboardInterrupt:
        logger.info("Task execution interrupted by user")
        return False
    except Exception as e:
        logger.exception(f"An error occurred during task execution: {e}")
        return False


def execute_task_with_generator(
    prompt: str, executor: Executor, planner: Planner, finder: BaseFinder, c: BaseConfig
) -> Generator[List[str], None, bool]:
    """Execute a task with generator for streaming results."""
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

            # Yield screenshot for streaming
            if executor.screenshot_as_base64:
                yield [(create_tempfile_from_base64(screenshot), observation)]
            else:
                yield [(screenshot, observation)]

            # Execute task step
            llm_responses = planner.llm_response(prompt, screenshot)
            for func_name, func_args in llm_responses:
                logger.debug(f"Executing {func_name} with {func_args}")

                try:
                    execution_output, executed_fn_name = parse_and_execute(
                        func_name, func_args, executor, planner, finder
                    )

                    if executed_fn_name == "task_finished":
                        return True

                    if executed_fn_name in [
                        "find_element_and_click",
                        "find_element_and_long_press",
                    ]:
                        _process_finder_output(
                            executed_fn_name, execution_output, func_args, executor, finder, planner
                        )

                except Exception as e:
                    logger.error(f"Error executing function {func_name}: {e}")
                    continue

                observation = func_args.get("observation", "")

    except KeyboardInterrupt:
        logger.info("Task execution interrupted by user")
        return False
    except Exception as e:
        logger.exception(f"An error occurred during task execution: {e}")
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
