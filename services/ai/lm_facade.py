from enum import Enum
from openai import OpenAI
from typing import Tuple, Any, Union
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
import os
import base64
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class LMs(Enum):
  GPT_40_MINI = 1
  OLLAMA_QWEN_2_5_7B = 2
  GEMMA_3_12B = 3
  TTS_SERVICE = 4

class LMFacade:
  def __init__(self, max_tokens: int = 1000, temperature: float = 0.7):
    self._text_to_text = LMs.OLLAMA_QWEN_2_5_7B
    self._text_to_image = LMs.GEMMA_3_12B
    self._text_to_speech = LMs.TTS_SERVICE
    
    # Initialize clients
    try:
      self._lm_clients = {
        # LMs.GPT_40_MINI: ChatOpenAI(model="gpt-4o-mini", max_tokens=max_tokens, temperature=temperature),
        LMs.OLLAMA_QWEN_2_5_7B: ChatOllama(model="qwen2.5:7b", num_predict=max_tokens, temperature=temperature),
        LMs.GEMMA_3_12B: ChatOllama(model="gemma3:12b", num_predict=max_tokens, temperature=temperature),
        LMs.TTS_SERVICE: OpenAI() if os.environ.get("OPENAI_API_KEY") else None
      }
    except Exception as e:
      err_msg = f"Error initializing LM clients: {e}"
      logger.error(err_msg)
      raise ValueError(err_msg)

  # Invoke LLM for text to text inference.
  def invoke_t2t(self, prompt: str) -> str:
    if self._text_to_text == LMs.GPT_40_MINI:
      return self._call_openai(prompt)
    elif self._text_to_text == LMs.OLLAMA_QWEN_2_5_7B:
      return self._call_ollama(prompt, LMs.OLLAMA_QWEN_2_5_7B)
    return "Unsupported usecase."
  
  def invoke_t2i(self, prompt: str) -> bytes:
    """
    Generate an image from a text prompt.
    
    Args:
        prompt: Text description of the image to generate
        
    Returns:
        bytes: The generated image data
    """
    try:
      if self._text_to_image == LMs.GEMMA_3_12B:
        # Mock implementation for now - this would be replaced with actual generation logic
        # In a real implementation, this would use a service like OpenAI's DALL-E or Stable Diffusion
        logger.info(f"Generating image for prompt: {prompt[:50]}...")
        
        # Return a placeholder image for now
        # This would be replaced with actual image generation
        return bytes(f"Image generated for: {prompt[:50]}...", "utf-8")
      return bytes("Unsupported image generation model.", "utf-8")
    except Exception as e:
      logger.error(f"Error generating image: {e}")
      return bytes(f"Error generating image: {str(e)}", "utf-8")
      
  def invoke_t2s(self, prompt: str) -> bytes:
    """
    Generate speech audio from a text prompt.
    
    Args:
        prompt: Text to convert to speech
        
    Returns:
        bytes: The generated audio data
    """
    try:
      if self._text_to_speech == LMs.TTS_SERVICE and self._lm_clients.get(LMs.TTS_SERVICE):
        logger.info(f"Generating speech for: {prompt[:50]}...")
        
        # Use OpenAI's TTS service if available
        client = self._lm_clients[LMs.TTS_SERVICE]
        
        # This is where you would make the actual TTS API call
        # For now, return a placeholder
        return bytes(f"Audio generated for: {prompt[:50]}...", "utf-8")
      
      # Fallback: return a placeholder for mock implementation
      logger.warning("Using mock TTS implementation")
      return bytes(f"Audio generated for: {prompt[:50]}...", "utf-8")
    except Exception as e:
      logger.error(f"Error generating speech: {e}")
      return bytes(f"Error generating speech: {str(e)}", "utf-8")

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
    return images