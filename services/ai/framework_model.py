"""
Config-driven framework for AI orchestration.
This module defines Pydantic models for the workflow steps and prompt generation.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Any, Literal
from enum import Enum

class OutputModality(str, Enum):
    """
    Enum for supported output modalities of prompts.
    """
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"


class FewShot(BaseModel):
    """
    Model for few-shot examples used in prompts.
    Each few-shot example contains a list of options that serve as examples
    for language models to better understand the expected response format.
    
    Args:
        options (List[str]): A list of example options that demonstrate the 
            expected format and content for responses. Defaults to an empty list.
    """
    options: List[str] = Field(default_factory=list)


class Prompt(BaseModel):
    """
    Model for prompt configuration used to generate structured prompts for language models.
    Defines all components needed to create a complete prompt with proper formatting.
    
    Args:
        id (str): Unique identifier for the prompt configuration.
        prefix (str): The main text content of the prompt that comes before examples.
        few_shots (List[FewShot]): List of few-shot examples to include in the prompt.
            Defaults to an empty list.
        options_delimiter (str): The string used to separate multiple options in the 
            language model's response. Defaults to "||".
        option_count (int): The number of options to request from the language model.
            Defaults to 3.
        parameters (List[str]): List of parameter names that need to be included in the 
            prompt template. Defaults to an empty list.
        output_instruction (Optional[str]): Explicit instructions for the expected 
            output format. If not provided, uses a default instruction based on 
            option_count and options_delimiter.
        expected_output_modality (OutputModality): The expected output modality of the prompt
            (TEXT, IMAGE, or AUDIO). Defaults to TEXT.
    """
    id: str
    prefix: str
    few_shots: List[FewShot] = Field(default_factory=list)
    options_delimiter: str = "||"
    option_count: int = 3
    parameters: List[str] = Field(default_factory=list)
    output_instruction: Optional[str] = f"Give me {option_count} options, add `{options_delimiter}` between the options. Do not output anything else."
    expected_output_modality: OutputModality = OutputModality.TEXT


class FrameworkStep(BaseModel):
    """
    Model for a step in the AI workflow framework. Represents a single stage in
    a multi-step process where each step can contain multiple prompts and defines
    transition logic to subsequent steps.
    
    Args:
        id (str): Unique identifier for the step.
        name (str): Human-readable name for the step.
        description (str): Detailed explanation of what this step accomplishes.
        prompts (List[Prompt]): List of prompt configurations to be used in this step.
        next_step (Optional[str]): Identifier of the step to transition to after 
            this one completes. If None, this is a terminal step. Defaults to None.
        requires_user_input (bool): Flag indicating whether this step requires 
            input from the user before proceeding. Defaults to False.
    """
    id: str
    name: str
    description: str
    prompts: List[Prompt]
    next_step: Optional[str] = None
    requires_user_input: bool = False
    require_user_input_for_step_id: str = ""
    

class Framework(BaseModel):
    """
    Model for the overall framework configuration. Defines a complete workflow with
    multiple steps, including starting and ending points, and global configuration
    that applies across all steps.
    
    Args:
        id (str): Unique identifier for the framework.
        name (str): Human-readable name for the framework.
        description (str): Detailed explanation of the framework's purpose and functionality.
        steps (List[FrameworkStep]): List of all steps in the framework workflow.
        initial_step (str): Identifier of the first step to execute in the workflow.
        final_step (str): Identifier of the step that marks the completion of the workflow.
        prompt_base (str): Common prefix text to be included in all prompts across
            the framework. Defines the overall persona and context for the language model.
            Defaults to a marketing/storytelling expert persona.
        default_output_instruction (str): Default instruction for expected output format
            to be used if not overridden at the prompt level. Defaults to requesting
            3 options with "||" as the delimiter.
    """
    id: str
    name: str
    description: str
    steps: List[FrameworkStep]
    initial_step: str
    final_step: str
    prompt_base: str = """You are the best marketer on Earth specifically specialising in video storytelling that helps brands get reach on social media. You are weird like Vsauce, thorough like Veritasium, goofy and imaginative like Tim Urban, and can write copy like David Ogilvy. You do this by understanding what kind of content the brands want by taking them through a series of steps mentioned below, providing them a few options at each step, and then on the basis of the user's reply, proceeding to the next step. Your scripts are written in such a way to have some stimulation every 3-5 seconds."""
    default_output_instruction: str = "Give me 3 options, add `||` between the options. Do not output anything else."

class MediaUri(BaseModel):
    uri: str

class ResultOptions(BaseModel):
    """Model for the resulting options given by one prompt.
    Args:
        result_options (List[Union[str, bytes]]): the one or more options given as a result of a single prompt.
        selected_option (int): the option selected by user, or 0 if len(result_options)=1
    """
    result_options: List[Union[str, MediaUri]]
    selected_option: int = -1

class FrameworkStepResult(BaseModel):
    """Model for the result of a step.
    Args:
        id (str): Id of the step.
        result (List[ResultOptions]): result of each prompt in the step, in that order.
    """
    id: str
    result: List[ResultOptions]

class FrameworkResult(BaseModel):
    """Model for the results of executing the framework.
    Args:
        id (str): Id of the framework.
        step_results (List[FrameworkStepResult]): result of each step.
    """
    id: str
    step_results: List[FrameworkStepResult]