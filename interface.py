
from clickclickclick.config import get_config
from clickclickclick.planner.task import execute_with_timeout, execute_task_with_generator
from utils import get_executor, get_finder, get_planner


import gradio as gr
from typing import Generator, List
import logging

logger = logging.getLogger(__name__)

def execute_task_prompt(
    task_prompt: str, platform: str, planner_model: str, finder_model: str, state: List
) -> Generator[List, None, bool]:
    try:
        config = get_config(platform, planner_model, finder_model)
        executor = get_executor(platform)
        planner = get_planner(planner_model, config, executor)
        finder = get_finder(finder_model, config, executor)

        result = execute_with_timeout(
            execute_task_with_generator, config.TASK_TIMEOUT_IN_SECONDS, task_prompt, executor, planner, finder, config
        )
        for output in result:
            new_entries = []
            for img_path, observation in output:
                # Create a temporary file to copy the image into

                # Append as a tuple (role, content)
                new_entries.append(gr.ChatMessage(role="assistant", content=observation))
                new_entries.append(gr.ChatMessage(role="assistant", content=gr.Image(img_path)))
                # new_entries.append([None, gr.Image(img_path)])

            state.extend(new_entries)

            # Yield updated state for both chatbot display and state update
            yield state, state
    except Exception as e:
        logger.exception("An error occurred during prompting.")
        yield state, state

def run_app():
    with gr.Blocks() as demo:
        state = gr.State([gr.ChatMessage(role="assistant", content="Step by step"),])  # Initialize the state to keep track of chatbot history
        examples = [
            ["Open gmail and compose mail to someone@gmail.com ask for lunch"],
            ["Open google maps and find bus stops in Alanson"],
            ["Find my rating in uber"]
        ]
        with gr.Row():
            with gr.Column():
                task_prompt = gr.Textbox(lines=2, placeholder="Enter task prompt here...")
                platform = gr.Radio(['android', 'osx'], label="Platform", value='android')
                planner_model = gr.Radio(['openai', 'gemini', 'ollama'], label="Planner Model", value='openai')
                finder_model = gr.Radio(['openai', 'gemini', 'ollama', 'mlx'], label="Finder Model", value='gemini')
                submit_btn = gr.Button("Submit")

                gr.Examples(examples, inputs=task_prompt)

            with gr.Column():
                chatbot = gr.Chatbot(type="messages", label="Task Execution History")

        # Connect the submit button to execute_task_prompt function
        submit_btn.click(execute_task_prompt,
                         inputs=[task_prompt, platform, planner_model, finder_model, state],
                         outputs=[chatbot, state],
                         )

        demo.launch()

if __name__ == "__main__":
    run_app()