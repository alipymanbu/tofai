"""NO_AI_CODE=True
"""
from enum import Enum
from typing import Tuple, Any, Union, Literal
from langchain_ollama import ChatOllama
import os
import base64
from PIL import Image
import io
import logging
from elevenlabs.client import ElevenLabs
from config.settings import settings
from google import genai
from google.genai import types
from google.genai.types import Content, Part, GenerateContentConfig
from langchain_google_genai import ChatGoogleGenerativeAI


logger = logging.getLogger(__name__)

class LMs(Enum):
  GPT_40_MINI = 1
  OLLAMA_QWEN_2_5_7B = 2
  GEMMA_3_12B = 3
  ELEVEN = 4
  GEMINI_2_0_FLASH = 5
  GEMINI_IMAGEN_3 = 6
  GOOGLE_TEXT_TO_SPEECH = 7

class LMFacade:
  def __init__(self, max_tokens: int = 1000, temperature: float = 0.7):
    self._text_to_text = LMs.GEMINI_2_0_FLASH
    self._text_to_image = LMs.GEMINI_IMAGEN_3
    self._text_to_speech = LMs.ELEVEN
    self._text_to_music = LMs.ELEVEN
    
    # Initialize clients
    try:
      self._lm_clients = {
        # LMs.GEMMA_3_12B: ChatOllama(model="gemma3:12b", num_predict=max_tokens, temperature=temperature),
        LMs.GEMINI_2_0_FLASH: genai.Client(api_key=settings.GEMINI_API_SECRET),
        LMs.ELEVEN: ElevenLabs(api_key=settings.ELEVEN_TTS_SECRET),
        LMs.GEMINI_IMAGEN_3: genai.Client(api_key=settings.GEMINI_API_SECRET),
      }
    except Exception as e:
      err_msg = f"Error initializing LM clients: {e}"
      logger.error(err_msg)
      raise ValueError(err_msg)

  def get_langchain_llm(self) -> Any:
    """
    Returns a Langchain-compatible LLM instance based on the currently selected text-to-text model.
    """
    if self._text_to_text == LMs.GEMINI_2_0_FLASH:
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GEMINI_API_SECRET)
    else:
        raise ValueError(f"No Langchain LLM configured for {self._text_to_text}")


  # Invoke LLM for text to text inference.
  def invoke_t2t(self, prompt: str) -> str:
    if self._text_to_text in {LMs.GEMMA_3_12B, LMs.OLLAMA_QWEN_2_5_7B}:
      return self._call_ollama(prompt, self._text_to_text)
    elif self._text_to_text == LMs.GEMINI_2_0_FLASH:
      return self._call_gemini(prompt, modality="text")
    return "Unsupported usecase."
  
  def invoke_t2i(self, prompt: str) -> Union[bytes, str]:
    """
    Generate an image from a text prompt.
    
    Args:
        prompt: Text description of the image to generate
        
    Returns:
        bytes: The generated image data
    """
    try:
      if not self._text_to_image or not self._lm_clients[self._text_to_image]:
        raise ValueError("Text to Image LLM not setup")
      return self._call_gemini(prompt, modality="image")
    except Exception as e:
      err_msg = f"Error generating image: {e}"
      logger.error(err_msg)
      return err_msg

  def invoke_t2m(self, prompt: str) -> Union[bytes, str]:
    """
    Generate music audio from a text prompt.
    
    Args:
        prompt: Text to convert to music
        
    Returns:
        bytes: The generated audio data
    """
    try:
      if self._text_to_music and self._lm_clients.get(self._text_to_music):
        logger.info(f"Generating music.")
        client = self._lm_clients[self._text_to_music]
        audio_stream = client.text_to_sound_effects.convert(
          text=prompt,
        )
        audio = b""
        for chunk in audio_stream:
          audio += chunk
        return audio
    except Exception as e:
      err_msg = f"Error generating speech: {e}"
      logger.error(err_msg)
      return err_msg

  def invoke_t2s(self, prompt: str) -> Union[bytes, str]:
    """
    Generate speech audio from a text prompt.
    
    Args:
        prompt: Text to convert to speech
        
    Returns:
        bytes: The generated audio data
    """
    try:
      if self._text_to_speech and self._lm_clients.get(self._text_to_speech):
        logger.info(f"Generating speech.")
        client = self._lm_clients[self._text_to_speech]
        audio_stream = client.text_to_speech.convert(
          # TODO(arjun): Get voices list to pick the best voice based on tonality.
          voice_id="JBFqnCBsd6RMkjVDRZzb",
          output_format="mp3_44100_128",
          text=prompt,
          model_id="eleven_multilingual_v2",
        )
        audio = b""
        for chunk in audio_stream:
          audio += chunk
        return audio
    except Exception as e:
      err_msg = f"Error generating speech: {e}"
      logger.error(err_msg)
      return err_msg

  def _call_ollama(self, prompt: str, model: LMs) -> Union[str, list[bytes]]:
    llm = self._lm_clients[model]
    response = llm.invoke(prompt)
    return response.content

  def _call_gemini_for_image_generation(self, prompt: str) -> bytes:
    try:
      client = self._lm_clients[LMs.GEMINI_IMAGEN_3]
      model = "imagen-3.0-generate-002"
      response: types.GenerateImagesResponse = client.models.generate_images(
        model=model,
        prompt=prompt,
        # Optional parameters
        config=types.GenerateImagesConfig(
          # Optional parameters
          number_of_images=1,
          aspect_ratio="9:16",
          safety_filter_level=types.SafetyFilterLevel.BLOCK_LOW_AND_ABOVE,
          person_generation=types.PersonGeneration.ALLOW_ADULT,
        )
      )
      if not response or not response.generated_images or not response.generated_images[0].image:
        rai_reason = ""
        if response and response.generated_images and response.generated_images[0].rai_reason:
           rai_reason = response.generated_images[0].rai_reason
        raise ValueError(f"No images generated. RAI Reason: {rai_reason}")
      image_data = response.generated_images[0].image
      return image_data.image_bytes
    except Exception as e:
      err_msg = bytes(f"Error generating image: {e}", encoding="utf-8")
      return err_msg 

  def _call_gemini(self, prompt: str, modality: Literal["text", "image"] = "text") -> Union[str, bytes]:
    if modality == "image":
        return self._call_gemini_for_image_generation(prompt)
    # For text generation
    client = self._lm_clients[LMs.GEMINI_2_0_FLASH]
    model = "gemini-2.0-flash-exp-image-generation"
    contents = [
        Content(
            role="user",
            parts=[
                Part.from_text(text=prompt),
            ],
        ),
    ]
    modalities = ["text"]
    if modality == "image":
        modalities.append("image")
    generate_content_config = GenerateContentConfig(
        response_modalities=modalities,
        response_mime_type="text/plain",
    )

    aggregated_text = ""
    aggregated_data = b""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
            continue
        part = chunk.candidates[0].content.parts[0]
        if part.inline_data:
            aggregated_data += part.inline_data.data
        elif part.text:
            aggregated_text += part.text

    if modality == "image":
        return aggregated_data
    else:
        return aggregated_text

# For Local Testing Only:
# if __name__ == "__main__":
#    lm_facade = LMFacade()
#    image_bytes = lm_facade.invoke_t2m("Create upbeat, curious music with clean electronic and warm acoustic elements. Playful rhythm, surprising moments. Think tech discovery excitement with a wink.")
#    print(f"Audio bytes: {image_bytes}")