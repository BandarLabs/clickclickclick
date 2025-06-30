from clickclickclick.executor.osx import MacExecutor
from clickclickclick.executor.android import AndroidExecutor
from clickclickclick.planner.gemini import GeminiPlanner
from clickclickclick.finder.gemini import GeminiFinder
from clickclickclick.planner.openai import ChatGPTPlanner
from clickclickclick.finder.local_ollama import OllamaFinder
from clickclickclick.finder.openai import OpenAIFinder
from clickclickclick.planner.local_ollama import OllamaPlanner
from clickclickclick.finder.mlx import MLXFinder
from clickclickclick.planner.anthropic import AnthropicPlanner
from clickclickclick.finder.anthropic import AnthropicFinder


def get_executor(platform):
    if platform.lower() == "osx":
        return MacExecutor()
    return AndroidExecutor()


def get_planner(planner_model, config, executor):
    if planner_model.lower() == "openai":
        executor.screenshot_as_base64 = True
        return ChatGPTPlanner(config)
    elif planner_model.lower() == "gemini":
        executor.screenshot_as_tempfile = True
        return GeminiPlanner(config)
    elif planner_model.lower() == "ollama":
        executor.screenshot_as_tempfile = True
        return OllamaPlanner(config, executor)
    elif planner_model.lower() == "anthropic":
        executor.screenshot_as_base64 = True
        return AnthropicPlanner(config)
    raise ValueError(f"Unsupported planner model: {planner_model}")


def get_finder(finder_model, config, executor):
    if finder_model.lower() == "openai":
        return OpenAIFinder(config, executor)
    elif finder_model.lower() == "gemini":
        return GeminiFinder(config, executor)
    elif finder_model.lower() == "ollama":
        return OllamaFinder(config, executor)
    elif finder_model.lower() == "mlx":
        return MLXFinder(config, executor)
    elif finder_model.lower() == "anthropic":
        return AnthropicFinder(config, executor)
    raise ValueError(f"Unsupported finder model: {finder_model}")
