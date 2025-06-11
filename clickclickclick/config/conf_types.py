import os
from dataclasses import dataclass
from google.ai.generativelanguage_v1beta.types import content
from .yaml_loader import load_yaml


# Get the absolute path to the directory containing this script
base_dir = os.path.dirname(os.path.abspath(__file__))


@dataclass
class BaseConfig:
    prompts = {}
    models = {}
    function_declarations = []
    models_config = load_yaml(os.path.join(base_dir, "models.yaml"))
    GEMINI_API_KEY = models_config["gemini"].get("api_key")
    SAMPLE_TASK_PROMPT = "open google.com in safari and search for sharukh khan and click the first link in the result. Take a screenshot and save the screenshot."
    TASK_TIMEOUT_IN_SECONDS = 330
    TASK_DELAY = 1
    DEBUG = True

    def get_config_for_platform(self, model_name, section, platform=""):
        """
        Retrieves configuration for a specific model, section, and platform.
        Fallbacks to section-specific or general configuration if platform-specific is not available.
        """
        model_configs = self.models_config[model_name]
        base_config = {k: v for k, v in model_configs.items() if k not in ["planner", "finder"]}
        section_config = model_configs.get(section, {})
        if section == "finder" and model_name == "gemini":
            section_config["generation_config"]["response_schema"] = content.Schema(
                type=content.Type.OBJECT,
                required=["ymin", "xmin", "ymax", "xmax"],
                properties={
                    "ymin": content.Schema(
                        type=content.Type.INTEGER,
                    ),
                    "xmin": content.Schema(
                        type=content.Type.INTEGER,
                    ),
                    "ymax": content.Schema(
                        type=content.Type.INTEGER,
                    ),
                    "xmax": content.Schema(
                        type=content.Type.INTEGER,
                    ),
                },
            )
        platform_config = section_config.get(platform, {})

        # Combine configurations with priority: platform > section > base
        combined_config = {**base_config, **section_config, **platform_config}
        return combined_config

    def get_function_declarations(self, platform: str) -> list:
        common_yaml_path = os.path.join(base_dir, "function_declarations", "common.yaml")
        common_declarations = load_yaml(common_yaml_path).get("function_declarations", [])

        platform_yaml_path = os.path.join(base_dir, "function_declarations", f"{platform}.yaml")
        platform_declarations = load_yaml(platform_yaml_path).get("function_declarations", [])

        return common_declarations + platform_declarations

    def get_functions_list_as_prompt(self, function_declarations) -> str:
        return "\n".join(f"{i + 1}. {fn['name']}" for i, fn in enumerate(function_declarations))

    def element_finder_prompt(self, element_name):
        return f'If "{element_name}" is present then Return bounding box for the same, else 0 0 0 0 for all xmax xmin ymax ymin. Check again.'

        # return f'Find if any bounding box of {element_name} in this format ymin,xmin,ymax,xmax. Really thats a "{element_name}"?'

    def get_prompts(self, platform, planner_model, finder_model):
        # Load the YAML file
        yaml_path = os.path.join(base_dir, "prompts.yaml")
        data = load_yaml(yaml_path)
        result = {}

        # Process platform-specific prompts and override with model-specific ones if available
        for model_key in [None, planner_model]:
            if model_key is None:
                platform_data = data.get(platform, {})
            else:
                platform_data = data.get(platform, {}).get(model_key, {})

            for key, value in platform_data.items():
                if key not in result or model_key is not None:
                    result[key] = value

        # Add finder model specific prompts
        finder_data = data.get(finder_model, {})
        for key, value in finder_data.items():
            if key not in result:
                result[key] = value

        return result


class ProductionConfig(BaseConfig):
    """Only add incremetal changes to BaseConfig here"""

    DEBUG = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    pass


class TestingConfig(BaseConfig):
    TESTING = True
    pass
