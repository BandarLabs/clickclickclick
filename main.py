import click
import os
from clickclickclick.config import get_config
from clickclickclick.planner.task import execute_with_timeout, execute_task
from utils import get_executor, get_finder, get_planner
from interface import run_gradio

@click.group()
def cli():
    pass


def setup_environment_variables(planner=None, finder=None):
    if planner and planner.lower() == "gemini":
        os.environ["GEMINI_API_KEY"] = click.prompt("Enter your Gemini API key", hide_input=True)
    elif planner and planner.lower() == "4o":
        setup_openai_or_azure()
    elif planner and planner.lower() == "ollama":
        os.environ["OLLAMA_MODEL_NAME"] = click.prompt(
            "Select the model name (press enter to use 'llama3.2:latest')",
            default="llama3.2:latest",
        )

    if not finder:
        finder = planner

    if finder and finder.lower() == "gemini":
        os.environ["GEMINI_API_KEY"] = click.prompt(
            "Enter your Gemini API key (press enter to use existing)",
            hide_input=True,
            default=os.getenv("GEMINI_API_KEY", ""),
        )
    elif finder and finder.lower() == "4o":
        setup_openai_or_azure(existing=True)
    elif finder and finder.lower() == "ollama":
        os.environ["OLLAMA_MODEL_NAME"] = click.prompt(
            "Select the model name (press enter to use 'llama3.2:latest')",
            default=os.getenv("OLLAMA_MODEL_NAME", "llama3.2:latest"),
        )


def setup_openai_or_azure(existing=False):
    version = click.prompt(
        (
            "Is it OpenAI or Azure version? (press enter to use existing)"
            if existing
            else "Is it OpenAI or Azure version?"
        ),
        type=str,
        default=os.getenv("OPENAI_API_TYPE", "openai"),
    )
    if version.lower() == "openai":
        os.environ["AZURE_OPENAI_API_KEY"] = click.prompt(
            (
                "Enter your OpenAI API key (press enter to use existing)"
                if existing
                else "Enter your OpenAI API key"
            ),
            hide_input=True,
            default=os.getenv("AZURE_OPENAI_API_KEY", ""),
        )
        os.environ["OPENAI_API_TYPE"] = "openai"
    elif version.lower() == "azure":
        os.environ["AZURE_OPENAI_API_KEY"] = click.prompt(
            (
                "Enter your Azure API key (press enter to use existing)"
                if existing
                else "Enter your Azure API key"
            ),
            hide_input=True,
            default=os.getenv("AZURE_OPENAI_API_KEY", ""),
        )
        os.environ["AZURE_OPENAI_MODEL_NAME"] = click.prompt(
            "Enter your Azure model name (press enter to use existing)",
            type=str,
            default=os.getenv("AZURE_OPENAI_MODEL_NAME", ""),
        )
        os.environ["AZURE_OPENAI_ENDPOINT"] = click.prompt(
            "Enter your Azure endpoint (press enter to use existing)",
            type=str,
            default=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        )
        os.environ["AZURE_OPENAI_API_VERSION"] = click.prompt(
            "Enter your Azure API version (press enter to use existing)",
            type=str,
            default=os.getenv("AZURE_OPENAI_API_VERSION", ""),
        )
        os.environ["OPENAI_API_TYPE"] = "azure"


@click.command()
@click.argument("task_prompt", nargs=-1)
@click.option("--platform", default="android", help="The platform to use, 'android' or 'osx'.")
@click.option(
    "--planner-model",
    default="openai",
    help="The planner model to use, 'openai', 'gemini', or 'ollama'.",
)
@click.option(
    "--finder-model",
    default="gemini",
    help="The finder model to use, 'openai', 'gemini', or 'ollama'.",
)
def run(task_prompt, platform, planner_model, finder_model):
    """
    Execute a task with the given TASK_PROMPT using the specified
    platform, planner model, and finder model.
    """
    task_prompt = " ".join(task_prompt)
    config = get_config(platform, planner_model, finder_model)

    executor = get_executor(platform)
    planner = get_planner(planner_model, config, executor)
    finder = get_finder(finder_model, config, executor)

    if not task_prompt:
        task_prompt = config.SAMPLE_TASK_PROMPT

    result = execute_with_timeout(
        execute_task, config.TASK_TIMEOUT_IN_SECONDS, task_prompt, executor, planner, finder, config
    )

    if result is not None:
        print(result)


@click.command()
def setup():
    """Setup command to configure planner and finder"""
    planner = click.prompt("Choose planner model ('gemini', '4o', or 'ollama')", type=str)
    finder = click.prompt(
        "Choose finder model ('gemini', '4o', or 'ollama') (press enter to use '{}')".format(
            planner
        ),
        type=str,
        default=planner,
    )

    setup_environment_variables(planner, finder)

@click.command()
def gradio():
    """Run the Gradio interface"""
    run_gradio()

cli.add_command(run)
cli.add_command(setup)
cli.add_command(gradio)

if __name__ == "__main__":
    cli()
