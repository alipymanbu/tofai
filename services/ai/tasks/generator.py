"""
Config-driven generator for AI prompts.
This module provides a mechanism to generate prompts from configuration files.
NO_AI_CODE=True
"""
from typing import Dict, List, Optional, Any, Tuple, Union, Type
from pydantic import BaseModel
import json
import os
from pathlib import Path

from services.ai.framework_model import Framework, FrameworkStep, Prompt, MediaUri, Screenplay, MultipleTextOutputSchema, FewShot
from services.ai.lm_facade import LMFacade
from services.ai.agents import agents_getter
from services.storage.object_store import S3MediaManager, MediaType
import hashlib
import magic
import re

SCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = {
    "Screenplay": Screenplay,
    "MultipleTextOutputSchema": MultipleTextOutputSchema,
}

def detect_file_type_from_bytes(byte_data):
    # Create a Magic instance
    mime_magic = magic.Magic(mime=True)
    # Use from_buffer to analyze bytes directly
    file_type = mime_magic.from_buffer(byte_data)
    return file_type

def generate_md5_hash(input_string):
    # Create an MD5 hash object
    md5_hash = hashlib.md5()
    # Update the hash object with the bytes of the input string
    md5_hash.update(input_string.encode('utf-8'))
    # Get the hexadecimal representation of the hash
    hashed_string = md5_hash.hexdigest()
    return hashed_string

def generate_context_id(content: Union[str, MediaUri]) -> str:
    """
    Generate a context ID for the given content.
    
    Args:
        content: The content to generate a context ID for (can be a string or MediaUri)
        
    Returns:
        str: The generated context ID
    """
    if isinstance(content, str):
        return generate_md5_hash(content)
    elif isinstance(content, MediaUri):
        return generate_md5_hash(content.uri)
    else:
        raise ValueError(f"Unsupported content type: {type(content)}")

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
        self.s3 = S3MediaManager(framework_id=framework_id)
        
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
    
    def get_step_by_id(self, step_id: Optional[str]) -> Optional[FrameworkStep]:
        """
        Get a step from the framework by ID.
        
        Args:
            step_id: The ID of the step to get
            
        Returns:
            Optional[FrameworkStep]: The step with the given ID, or None if not found
        """
        if not step_id:
            return None
        for step in self.framework.steps:
            if step.id == step_id:
                return step
        return None

    def get_step_version(self, step_id: str) -> int:
        """
        Get the version of a step by ID.
        
        Args:
            step_id: The ID of the step to get the version for
            
        Returns:
            int: The version of the step
        """
        step = self.get_step_by_id(step_id)
        if not step:
            raise ValueError(f"Step with ID '{step_id}' not found.")
        return step.version
    
    def get_step_by_index(self, index: int) -> Optional[FrameworkStep]:
        """
        Get a step from the framework by index.
        
        Args:
            index: the index of the step to find in the framework
            
        Returns:
            Optional[FrameworkStep]: The step with the given index, or None if not found
        """
        if index >= len(self.framework.steps) or index < 0:
            return None
        return self.framework.steps[index]

    def generate_prompt_templates(self) -> dict[str, list[str]]:
        """
        Generate prompt templates for all steps based on the framework configuration."""
        result = {}
        valid_params = set()
        for step in self.framework.steps:
            for prompt in step.prompts:
                params_dict = {}
                for param in prompt.parameters:
                    if param not in valid_params:
                        raise ValueError(f"Parameter '{param}' is not valid parameter for step '{step.id}'. Valid parameters are: {valid_params}")
                    params_dict[param] = "{" + f"{param}" + "}"
                prompt_template, _ = self.generate_prompt(prompt, params_dict)
                result[step.id] = prompt_template
            valid_params.add(step.name)
        return result

    def generate_few_shot_str(self, few_shots: List[FewShot], schema: Union[str, None], output_delimiter: str = "||", options_count: int=1) -> str:
        """
        Generate a few-shot string from a list of FewShot examples.
        
        Args:
            few_shots: List of FewShot examples
            schema: The schema to use for the examples
            output_delimiter: The delimiter to use for separating options
        Returns:
            str: The generated few-shot string
        """
        if not few_shots:
            return ""
        for fs in few_shots:
            if options_count > 0 and len(fs.options) != options_count:
                raise ValueError(f"FewShot options count {len(fs.options)} does not match expected count {options_count}.")
        # If schema is provided, use it to validate the examples
        if schema and schema in SCHEMA_REGISTRY:
            schema_class = SCHEMA_REGISTRY[schema]
            if schema_class == MultipleTextOutputSchema:
                json_strs = []
                for fs in few_shots:
                    json_str = MultipleTextOutputSchema(outputs=fs.options).model_dump_json()
                    json_strs.append(json_str)
                return "Examples:\n" + "\n\n".join(json_strs) + "\n\nNow, your turn:"
            elif schema_class == Screenplay:
                screenplay_strs = []
                for fs in few_shots:
                    for option in fs.options:
                        screenplay_instance = Screenplay.model_validate_json(option)
                        screenplay_strs.append(screenplay_instance.model_dump_json())
                return "Examples:\n" + "\n\n".join(screenplay_strs) + "\n\nNow, your turn:"
        
        # Build the few-shot string
        few_shot_examples = []
        for fs in few_shots:
            options_str = output_delimiter.join(fs.options)
            few_shot_examples.append(options_str)
        
        return "Examples:\n" + "\n\n".join(few_shot_examples) + "\n\nNow, your turn:"
    
    def generate_prompt(self, prompt: Prompt, param_values: Dict[str, str]) -> Tuple[str, Tuple[Union[str, None], str]]:
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
        few_shot_str = self.generate_few_shot_str(
            few_shots=prompt.few_shots,
            schema=prompt.expected_output_schema,
            output_delimiter=prompt.options_delimiter,
            options_count=prompt.option_count
        )     
        # Build the parameter string
        if prompt.params_format == "list":
            params_str = "\n".join([value for _, value in param_values.items()])
        elif prompt.params_format == "dict":
            params_str = "\n".join([f"{key}: {value}" for key, value in param_values.items()])
        output_instruction = prompt.output_instruction
        template = f"""{{prompt_prefix}}
{{output_instruction}}
        
{{few_shot_str}}

{{params_str}}"""
        if not prompt.ignore_prompt_base:
            template = f"""{{prompt_base}}
            """ + template
        
        # Fill in the template
        return template.format(
            prompt_base=self.framework.prompt_base,
            prompt_prefix=prompt.prefix,
            output_instruction=output_instruction,
            few_shot_str=few_shot_str,
            params_str=params_str
        ), (prompt.expected_output_schema, prompt.expected_output_modality)

    def put_media_to_s3_and_get_url(self, data: bytes, type: MediaType, session_id: str, step_id: str, index: int, input_prompt: str) -> MediaUri:
        content_type = detect_file_type_from_bytes(data)
        s3_filename = S3MediaManager.create_key(session_id=session_id, framework_step_id=step_id, index=index, unique_key=generate_md5_hash(input_prompt), content_type=content_type)
        self.s3.upload_file(
            file_data=data,
            media_type=type,
            filename=s3_filename,
            content_type=content_type,
        )
        file_url = self.s3.get_file_url(filename=s3_filename, media_type=type)
        return MediaUri(uri=file_url)

    def _generate_param_combinations(self, data: Dict[str, Union[str, List[str]]]) -> List[Dict[str, str]]:
        list_values = []
        list_keys = []
        for key, value in data.items():
            list_keys.append(key)
            if isinstance(value, list):
                list_values.append([(key, str(item)) for item in value])
            else:
                list_values.append([(key, str(value))])

        combinations: List[Dict[str, str]] = []

        def generate(index, current_combination):
            if index == len(list_keys):
                combinations.append(dict(current_combination))
                return

            for key_value_pair in list_values[index]:
                generate(index + 1, current_combination + [key_value_pair])

        generate(0, [])
        return combinations

    def get_durations_from_prompts(self, video_prompt: str, scene_idx: int) -> tuple[str, int]:
        match = re.search(r"Duration Analysis.*?SCENE_DURATIONS_END", video_prompt, re.DOTALL)
        if match:
            duration_analysis = match.group(0)
            video_prompt = video_prompt.replace(duration_analysis, "")
            scene_pattern = re.compile(rf"Scene{{{scene_idx}}}: (\d+) seconds")
            duration_match = scene_pattern.search(duration_analysis)
            if duration_match:
                duration = int(duration_match.group(1))
            else:
                duration = 0
            return video_prompt, duration
        return video_prompt, 0

    def generate_options_from_prompt(self, step: FrameworkStep, param_values: Dict[str, Union[str, List[str]]], session_id: str) -> List[List[Union[str, MediaUri]]]:
        result = []
        # print(f"Generating options from prompt: {step.prompts} {param_values}")
        full_prompts = []
        # print(f"Generating options from prompt: {len(step.prompts)} {param_values}")
        param_values_flattened = self._generate_param_combinations(param_values)
        # print(f"param_values_flattened: {param_values_flattened}")
        for idx ,prompt in enumerate(step.prompts):
            for params_value_flattened in param_values_flattened:
                full_prompts.append(self.generate_prompt(prompt, params_value_flattened))
        for idx, full_prompt in enumerate(full_prompts):
            # Generate the full prompt
            expected_modality = full_prompt[1][1]
            if expected_modality == "IMAGE":
                # For image generation
                image_data = self.lm_facade.invoke_t2i(full_prompt[0])
                result.append([self.put_media_to_s3_and_get_url(
                    data=image_data,
                    type=MediaType.IMAGE,
                    session_id=session_id,
                    step_id=step.id,
                    index=idx,
                    input_prompt=full_prompt[0]
                )])
            elif expected_modality == "SPEECH":
                # For audio generation
                audio_data = self.lm_facade.invoke_t2s(full_prompt[0])
                result.append([self.put_media_to_s3_and_get_url(
                    data=audio_data,
                    type=MediaType.SPEECH,
                    session_id=session_id,
                    step_id=step.id,
                    index=idx,
                    input_prompt=full_prompt[0]
                )])
            elif expected_modality == "MUSIC":
                # For audio generation
                audio_data = self.lm_facade.invoke_t2m(full_prompt[0])
                result.append([self.put_media_to_s3_and_get_url(
                    data=audio_data,
                    type=MediaType.MUSIC,
                    session_id=session_id,
                    step_id=step.id,
                    index=idx,
                    input_prompt=full_prompt[0]
                )])
            elif expected_modality == "VIDEO":
                full_prompt_without_durations, scene_duration = self.get_durations_from_prompts(full_prompt[0], idx)
                try:
                    video_data = self.lm_facade.invoke_p2v(full_prompt_without_durations, scene_duration_sec=scene_duration)
                    result.append([self.put_media_to_s3_and_get_url(
                        data=video_data,
                        type=MediaType.VIDEO,
                        session_id=session_id,
                        step_id=step.id,
                        index=idx,
                        input_prompt=full_prompt[0]
                    )])
                except Exception as e:
                    print(f"Error generating video for prompt '{e}'. Falling back to image.")
                    image_data = self.lm_facade.invoke_t2i(full_prompt_without_durations)
                    result.append([self.put_media_to_s3_and_get_url(
                        data=image_data,
                        type=MediaType.IMAGE,
                        session_id=session_id,
                        step_id=step.id,
                        index=idx,
                        input_prompt=full_prompt[0]
                    )])
            else:  # Default to TEXT
                # Generate text options using the LM facade
                expected_schema = full_prompt[1][0]
                if expected_schema and expected_schema in SCHEMA_REGISTRY:
                    schema = SCHEMA_REGISTRY[expected_schema]
                else:
                    schema = None
                response = self.lm_facade.invoke_t2t(full_prompt[0], schema)
                result.append(self._parse_options(response, prompt.options_delimiter, schema=expected_schema))
        return result

    def generate_options_from_agent(self, step: FrameworkStep, param_values: Dict[str, Union[str, List[str]]], session_id: str) -> List[List[Union[str, MediaUri]]]:
        result = []
        param_values_flattened = self._generate_param_combinations(param_values)
        for agent in step.agents:
            result.append(agents_getter.get_agent_call(
                id=agent.id,
                lm_facade=self.lm_facade,
                s3=self.s3,
                session_id=session_id,
                step_id=step.id,
                params_value_flattened=param_values_flattened,
                param_values=param_values
                ))
        return result

    def generate_context_ids_for_results(self, results: List[List[Union[str, MediaUri]]]) -> List[List[str]]:
        """
        Generate context IDs for the results.
        
        Args:
            results: The generated results
        Returns:
            List[str]: The context IDs for the results
        """
        context_ids_deck = []
        for result in results:
            context_ids = []
            for item in result:
                context_ids.append(generate_context_id(item))
            context_ids_deck.append(context_ids)
        return context_ids_deck
    
    def generate_options(self, step_id: str, param_values: Dict[str, Union[str, List[str]]], session_id: str) -> Tuple[List[List[Union[str, MediaUri]]], List[List[str]]]:
        """
        Generate options for a step.
        
        Args:
            step_id: The ID of the step
            param_values: The parameter values to use
            session_id: Id of user session
            
        Returns:
            List[List[Union[str, bytes]]]: LLM result from each prompt in the list. The result itself is a list of options (can be text, images, or audio data)
        """
        step = self.get_step_by_id(step_id)
        if not step:
            raise ValueError(f"Step with ID '{step_id}' not found.")
        
        if not step.prompts and not step.agents:
            raise ValueError(f"Step '{step_id}' has no prompts or agents.")
        
        result = []
        result += self.generate_options_from_prompt(step=step, param_values=param_values, session_id=session_id)
        result += self.generate_options_from_agent(step=step, param_values=param_values, session_id=session_id)
        return result, self.generate_context_ids_for_results(result)

    def get_selection_for_step_id(self, step_id: str) -> str:
        step = self.get_step_by_id(step_id=step_id)
        return step.require_user_input_for_step_id

    def get_step_id_for_selection_id(self, step_id: str) -> Optional[FrameworkStep]:
        for step in self.framework.steps:
            if step.require_user_input_for_step_id == step_id:
                return step
        return None
    
    def _parse_options(self, response: str, delimiter: str, schema: Union[str, None] = None) -> List[str]:
        """
        Parse options from a response string.
        
        Args:
            response: The response string
            delimiter: The delimiter used to separate options
            
        Returns:
            List[str]: The parsed options
        """
        if schema:
            if schema in SCHEMA_REGISTRY:
                schema_class = SCHEMA_REGISTRY[schema]
                if schema_class == MultipleTextOutputSchema:
                    output: MultipleTextOutputSchema = MultipleTextOutputSchema.model_validate_json(response)
                    return output.outputs
                if schema_class == Screenplay:
                    output: Screenplay = Screenplay.model_validate_json(response)
                    return [output.model_dump_json()]
                else:
                    raise ValueError(f"Unsupported schema '{schema}'")
        return [opt.strip() for opt in response.split(delimiter) if opt.strip()]
