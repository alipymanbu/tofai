from enum import Enum
from openai import OpenAI
from typing import Tuple, Any, Union
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
import os
import base64
from PIL import Image
import io

class LMs(Enum):
  GPT_40_MINI = 1
  OLLAMA_QWEN_2_5_7B = 2
  GEMMA_3_12B = 3

class LMFacade:
  def __init__(self, max_tokens: int = 1000, temperature: float = 0.7):
    self._text_to_text = LMs.OLLAMA_QWEN_2_5_7B
    self._text_to_image = LMs.GEMMA_3_12B
    self._lm_clients = {
      # LMs.GPT_40_MINI: ChatOpenAI(model="gpt-4o-mini", max_tokens=max_tokens, temperature=temperature),
      LMs.OLLAMA_QWEN_2_5_7B: ChatOllama(model="qwen2.5:7b", num_predict=max_tokens, temperature=temperature),
      LMs.GEMMA_3_12B: ChatOllama(model="gemma3:12b", num_predict=max_tokens, temperature=temperature)
    }

  # Invoke LLM for text to text inference.
  def invoke_t2t(self, prompt: str) -> str:
    if self._text_to_text == LMs.GPT_40_MINI:
      return self._call_openai(prompt)
    elif self._text_to_text == LMs.OLLAMA_QWEN_2_5_7B:
      return self._call_ollama(prompt, LMs.OLLAMA_QWEN_2_5_7B)
    return "Unsupported usecase."
  
  def invoke_t2i(self, prompt: str) -> list[bytes]:
    return []

  def get_t2t_llm(self) -> Tuple[LMs, Any]:
    return self._text_to_text, self._lm_clients[self._text_to_text]

  def _call_openai(self, prompt: str) -> str:
    llm = self._lm_clients[LMs.GPT_40_MINI]
    response = llm.invoke(prompt)
    return response.content

  def _call_ollama(self, prompt: str, model: LMs) -> Union[str, list[bytes]]:
    llm = self._lm_clients[model]
    response = llm.invoke(prompt)
    return response.content

  def _parse_image_response(self, content: list[Union[str, dict]]) -> list[bytes]:
    print(content)
    images = []
    for item in content:
      if isinstance(item, dict) and item.get("type") == "image_url":
          image_url = item["image_url"]["url"]
          if image_url.startswith("data:image/"):
              image_data = image_url.split(",")[1]
              decoded_image = base64.b64decode(image_data)
              images.append(decoded_image)