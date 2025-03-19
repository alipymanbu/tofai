from typing import Any, List, Union
from abc import ABC, abstractmethod
from lm_facade import LMFacade

_PROMPT_BASE = """You are the best marketer on Earth specifically specialising in video
  storytelling that helps brands get reach on social media. You are weird like Vsauce,
  thorough like Veritasium, goofy and imaginative like Tim Urban, and can write copy
  like David Ogilvy. You do this by marrying brand strategy and user passion points.
  """
_OUTPUT_INSTRUCTION = "Give me 3 options, add `||` between the options. Do not output anything else."

_PROMPT_TEMPLATE_WITH_FEW_SHOT = """{prompt_base}
    
{prompt}
{output_instruction}
    
Examples:
{few_shot_str}

Now, your turn:
{params_str}"""

class BaseGenerator:
  def __init__(self, prompt: str, few_shot: List[str], param_names: List[str], output_instruction: Union[str, None] = None, lm_facade: Union[LMFacade, None] = None, prompt_template: str = _PROMPT_TEMPLATE_WITH_FEW_SHOT):
    """Constrcutor for BaseGenerator class.
    
    Args:
      prompt (str): The prompt prefix to be used.
      few_shot (str): The few shot to be used for final prompt.
      params (List[str]): The parameter names used in final prompt.
    """
    self._prompt_base = _PROMPT_BASE
    self._output_instruction = output_instruction if output_instruction else _OUTPUT_INSTRUCTION
    self._prompt = prompt
    self._few_shot = few_shot
    self._param_names = param_names
    self._lm_facade = lm_facade if lm_facade else LMFacade()
    self._prompt_template = prompt_template

  def generate(self, param_vals: dict[str, str], multimodel: bool = False) -> Union[str, list[bytes]]:
    if multimodel:
      prompt = self.create_prompt_for_image_prompt(param_vals)
      response_prompt = self._lm_facade.invoke_t2t(prompt)
      image_prompts = self.parse_text_options(response_prompt)
      print(image_prompts)
      images = []
      for image_prompt in image_prompts:
        images.append[self._lm_facade.invoke_t2i(image_prompt)]
      return images
    prompt = self.create_prompt(param_vals)
    response = self._lm_facade.invoke_t2t(prompt)
    return self.parse_text_options(response)

  def _is_param_vals_valid(self, param_vals: dict[str, str]) -> bool:
    return all([param in param_vals for param in self._param_names])

  def create_prompt(self, param_vals) -> str:
    if not self._is_param_vals_valid(param_vals):
      raise ValueError("Invalid parameter values provided.")
    few_shot_str = "\n\n".join(self._few_shot)
    params_str = "\n".join([f"{key}: {value}" for key, value in param_vals.items()])
    return self._prompt_template.format(
      prompt_base=self._prompt_base,
      prompt=self._prompt,
      output_instruction=self._output_instruction,
      few_shot_str=few_shot_str,
      params_str=params_str
    )
  
  def create_prompt_for_image_prompt(self, param_vals: dict[str, str]) -> str:
    if not self._is_param_vals_valid(param_vals):
      raise ValueError("Invalid parameter values provided.")
    context = "\n".join([f"{key}: {value}" for key, value in param_vals.items() if key != "Script"])
    script = param_vals["Script"]
    return self._prompt_template.format(
      prompt_base=self._prompt_base,
      prompt=self._prompt,
      params_str=context,
      script=script,
      output_instruction=self._output_instruction
    )

  def parse_text_options(self, lm_output: str) -> List[str]:
    return [opt.strip('\n ') for opt in lm_output.strip().split("||") if opt.strip('\n ')]
