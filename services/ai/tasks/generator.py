"""
Config-driven generator for AI prompts.
This module provides a mechanism to generate prompts from configuration files.
"""
from typing import Dict, List, Optional, Any, Union
import json
import os
from pathlib import Path

from services.ai.framework_model import Framework, FrameworkStep, Prompt
from services.ai.lm_facade import LMFacade

class Generator:
    """
    A generator that loads prompt configurations from a JSON file and generates prompts.
    """
    
    def __init__(self, framework_id: str, lm_facade: Optional[LMFacade] = None):
        """
        Initialize the config-driven generator.
        
        Args:
            framework_id: The ID of the framework to load
            lm_facade: Language model facade for generating text
        """
        self.framework = self._load_framework(framework_id)
        self.lm_facade = lm_facade or LMFacade()
        
    def _load_framework(self, framework_id: str) -> Framework:
        """
        Load a framework configuration from a JSON file.
        
        Args:
            framework_id: The ID of the framework to load
            
        Returns:
            Framework: The loaded framework
        """
        # Find the config file in the configs directory
        config_dir = Path(__file__).parent.parent / "configs"
        
        # Try looking for a file with the framework ID
        config_path = config_dir / f"{framework_id}.json"
        if not config_path.exists():
            # Try looking for any file that contains the framework ID
            for file_path in config_dir.glob("*.json"):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if data.get("id") == framework_id:
                        config_path = file_path
                        break
        
        if not config_path.exists():
            raise ValueError(f"Framework with ID '{framework_id}' not found.")
        
        # Load the configuration file
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            
        # Create the framework
        return Framework.model_validate(config_data)
    
    def get_step_by_id(self, step_id: str) -> Optional[FrameworkStep]:
        """
        Get a step from the framework by ID.
        
        Args:
            step_id: The ID of the step to get
            
        Returns:
            Optional[FrameworkStep]: The step with the given ID, or None if not found
        """
        for step in self.framework.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_step_by_index(self, index: int) -> Optional[FrameworkStep]:
        """
        Get a step from the framework by index.
        
        Args:
            index: the index of the step to find in the framework
            
        Returns:
            Optional[FrameworkStep]: The step with the given index, or None if not found
        """
        if index >= len(self.framework) or index < 0:
            return None
        return self.framework.steps[index]
    
    def generate_prompt(self, prompt: Prompt, param_values: Dict[str, str]) -> str:
        """
        Generate a prompt from a configuration.
        
        Args:
            prompt: The prompt configuration
            param_values: The parameter values to use in the prompt
            
        Returns:
            str: The generated prompt
        """
        # Check if all required parameters are provided
        for param in prompt.parameters:
            if param not in param_values:
                raise ValueError(f"Missing required parameter '{param}'")
        
        # Build the few-shot examples
        few_shot_str = ""
        if prompt.few_shots:
            # For each few-shot example, join its options with the options_delimiter
            few_shot_examples = []
            for fs in prompt.few_shots:
                options_str = prompt.options_delimiter.join(fs.options)
                few_shot_examples.append(options_str)
            # Join all few-shot examples
            few_shot_str = "Examples:\n" + "\n\n".join(few_shot_examples)        
        # Build the parameter string
        params_str = "\n".join([f"{key}: {value}" for key, value in param_values.items()])
        output_instruction = prompt.output_instruction or self.framework.default_output_instruction
        template = f"""{{prompt_base}}
        
{{prompt_prefix}}
{{output_instruction}}
        
{{few_shot_str}}

Now, your turn:
{{params_str}}"""
        
        # Fill in the template
        return template.format(
            prompt_base=self.framework.prompt_base,
            prompt_prefix=prompt.prefix,
            output_instruction=output_instruction,
            few_shot_str=few_shot_str,
            params_str=params_str
        )
    
    def generate_options(self, step_id: str, param_values: Dict[str, str]) -> List[List[Union[str, bytes]]]:
        """
        Generate options for a step.
        
        Args:
            step_id: The ID of the step
            param_values: The parameter values to use
            
        Returns:
            List[List[Union[str, bytes]]]: LLM result from each prompt in the list. The result itself is a list of options (can be text, images, or audio data)
        """
        step = self.get_step_by_id(step_id)
        if not step:
            raise ValueError(f"Step with ID '{step_id}' not found.")
        
        if not step.prompts:
            raise ValueError(f"Step '{step_id}' has no prompts.")
        
        # Use the first prompt in the step
        prompt = step.prompts[0]
        result = []
        for prompt in step.prompts:
            # Generate the full prompt
            full_prompt = self.generate_prompt(prompt, param_values)
            if prompt.expected_output_modality == "IMAGE":
                # For image generation
                image_data = self.lm_facade.invoke_t2i(full_prompt)
                result.append(image_data)
            elif prompt.expected_output_modality == "AUDIO":
                # For audio generation
                audio_data = self.lm_facade.invoke_t2s(full_prompt)
                result.append(audio_data)
            else:  # Default to TEXT
                # Generate text options using the LM facade
                response = self.lm_facade.invoke_t2t(full_prompt)
                result.append(self._parse_options(response, prompt.options_delimiter))
        return result

    def get_selection_for_step_id(self, step_id: str) -> str:
        step = self.get_step_by_id(step_id=step_id)
        return step.require_user_input_for_step_id
    
    def _parse_options(self, response: str, delimiter: str) -> List[str]:
        """
        Parse options from a response string.
        
        Args:
            response: The response string
            delimiter: The delimiter used to separate options
            
        Returns:
            List[str]: The parsed options
        """
        return [opt.strip() for opt in response.split(delimiter) if opt.strip()]
