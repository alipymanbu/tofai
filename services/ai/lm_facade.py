"""NO_AI_CODE=True
"""
from enum import Enum
from typing import Any, Union, Literal
import logging
from elevenlabs.client import ElevenLabs
from config.settings import settings
from google import genai
from google.genai import types
from google.genai.types import Content, Part, GenerateContentConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from functools import lru_cache
import mimetypes
import struct


logger = logging.getLogger(__name__)

def _convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = _parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

def _parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys. Values will be
        integers if found, otherwise None.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}

def _calculate_audio_duration(accumulated_audio_data: bytes, audio_mime_type: str) -> float:
    audio_params = _parse_audio_mime_type(audio_mime_type)
    sample_rate = audio_params["rate"]
    bits_per_sample = audio_params["bits_per_sample"]
    # 2. Define number of channels (the TTS model is mono)
    num_channels = 1
    # 3. Calculate the duration using the formula
    bytes_per_sample = bits_per_sample // 8
    total_data_bytes = len(accumulated_audio_data)
    duration_seconds = total_data_bytes / (sample_rate * num_channels * bytes_per_sample)
    return duration_seconds

class LMs(Enum):
  GPT_40_MINI = 1
  OLLAMA_QWEN_2_5_7B = 2
  GEMMA_3_12B = 3
  ELEVEN = 4
  GEMINI_2_0_FLASH = 5
  GEMINI_IMAGEN_3 = 6
  GOOGLE_TEXT_TO_SPEECH = 7
  GEMINI_2_5_FLASH = 8
  GEMINI_2_5_FLASH_TTS = 9

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
        LMs.GEMINI_2_5_FLASH: genai.Client(api_key=settings.GEMINI_API_SECRET),
        LMs.GEMINI_2_5_FLASH_TTS: genai.Client(api_key=settings.GEMINI_API_SECRET),
        LMs.ELEVEN: ElevenLabs(api_key=settings.ELEVEN_TTS_SECRET),
        LMs.GEMINI_IMAGEN_3: genai.Client(api_key=settings.GEMINI_API_SECRET),
      }
    except Exception as e:
      err_msg = f"Error initializing LM clients: {e}"
      logger.error(err_msg)
      raise ValueError(err_msg)
        # Cache with reasonable size limits
    self._cached_t2t = lru_cache(maxsize=50, typed=True)(self._invoke_t2t_impl)
    self._cached_t2i = lru_cache(maxsize=10, typed=True)(self._invoke_t2i_impl)
    self._cached_t2s = lru_cache(maxsize=2, typed=True)(self._invoke_t2s_impl)
    self._cached_t2m = lru_cache(maxsize=2, typed=True)(self._invoke_t2m_impl)

  def get_langchain_llm(self) -> Any:
    """
    Returns a Langchain-compatible LLM instance based on the currently selected text-to-text model.
    """
    if self._text_to_text == LMs.GEMINI_2_0_FLASH:
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GEMINI_API_SECRET)
    if self._text_to_text == LMs.GEMINI_2_5_FLASH:
        return ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-05-06", google_api_key=settings.GEMINI_API_SECRET)
    else:
        raise ValueError(f"No Langchain LLM configured for {self._text_to_text}")

  def invoke_t2t(self, prompt: str) -> str:
      return self._cached_t2t(prompt)

  def invoke_t2i(self, prompt: str) -> Union[bytes, str]:
      return self._cached_t2i(prompt)

  def invoke_t2s(self, prompt: str) -> Union[bytes, str]:
      return self._cached_t2s(prompt)

  def invoke_t2m(self, prompt: str) -> Union[bytes, str]:
      return self._cached_t2m(prompt)

  # Invoke LLM for text to text inference.
  def _invoke_t2t_impl(self, prompt: str) -> str:
    if self._text_to_text in {LMs.GEMMA_3_12B, LMs.OLLAMA_QWEN_2_5_7B}:
      return self._call_ollama(prompt, self._text_to_text)
    elif self._text_to_text == LMs.GEMINI_2_0_FLASH:
      return self._call_gemini(prompt, modality="text")
    err_msg = f"Text to Text LLM {self._text_to_text} not supported"
    logger.error(err_msg)
    raise ValueError(err_msg)
  
  def _invoke_t2i_impl(self, prompt: str) -> Union[bytes, str]:
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
      raise ValueError(err_msg)

  def _invoke_t2m_impl(self, prompt: str) -> Union[bytes, str]:
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
      err_msg = f"Error generating music: {e}"
      logger.error(err_msg)
      raise ValueError(err_msg)

  def _invoke_t2s_impl(self, prompt: str) -> Union[bytes, str]:
    """
    Generate speech audio from a text prompt.
    
    Args:
        prompt: Text to convert to speech
        
    Returns:
        bytes: The generated audio data
    """
    try:
       return self._call_gemini(prompt, modality="speech")
    except Exception as e:
      logger.error(f"Error generating speech with Gemini: {e}")
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
      logger.error(f"Error generating speech with Eleven API: {e}")
      raise ValueError(f"Both ElevenLabs and Google TTS failed. Last error: {e}")

  def _call_ollama(self, prompt: str, model: LMs) -> Union[str, list[bytes]]:
    llm = self._lm_clients[model]
    response = llm.invoke(prompt)
    return response.content

  def _call_gemini_for_image_generation(self, prompt: str) -> bytes:
    print(f"Generating image with prompt: {prompt}")
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
        raise ValueError(f"No images generated. RAI Reason: {response}")
      image_data = response.generated_images[0].image
      return image_data.image_bytes
    except Exception as e:
      raise ValueError(f"Error generating image: {e}") 


  def _call_gemini_for_speech_generation(self, prompt: str) -> bytes:
    try:
      client = self._lm_clients[LMs.GEMINI_2_5_FLASH_TTS]
      model = "gemini-2.5-flash-preview-tts"
      contents = [
          types.Content(
              role="user",
              parts=[
                  types.Part.from_text(text=prompt),
              ],
          ),
      ]
      generate_content_config = types.GenerateContentConfig(
          temperature=1,
          response_modalities=[
              "audio",
          ],
          speech_config=types.SpeechConfig(
              voice_config=types.VoiceConfig(
                  prebuilt_voice_config=types.PrebuiltVoiceConfig(
                      voice_name="Zephyr"
                  )
              )
          ),
      )
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
            if not mimetypes.guess_extension(part.inline_data.mime_type):
               # This means the audio format is likely raw PCM or similar.
               # We need to convert it to wav.
              aggregated_data += _convert_to_wav(part.inline_data.data, part.inline_data.mime_type) 
            else:              
              aggregated_data += part.inline_data.data
      return aggregated_data
    except Exception as e:
      raise ValueError(f"Error generating speech: {e}")

  def _call_gemini(self, prompt: str, modality: Literal["text", "image", "speech"] = "text") -> Union[str, bytes]:
    if modality == "image":
        return self._call_gemini_for_image_generation(prompt)
    if modality == "speech":
        return self._call_gemini_for_speech_generation(prompt)
    # For text generation
    client = self._lm_clients[LMs.GEMINI_2_5_FLASH]
    model = "gemini-2.5-flash-preview-05-20"
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
        temperature=1,
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

  def clear_cache(self):
      """Clear all caches for this instance."""
      self._cached_t2t.cache_clear()
      self._cached_t2i.cache_clear()
      self._cached_t2s.cache_clear()
      self._cached_t2m.cache_clear()

  def get_cache_info(self) -> dict:
      """Get cache statistics for all cached methods."""
      return {
          "t2t": self._cached_t2t.cache_info()._asdict(),
          "t2i": self._cached_t2i.cache_info()._asdict(),
          "t2s": self._cached_t2s.cache_info()._asdict(),
          "t2m": self._cached_t2m.cache_info()._asdict(),
      }

# For Local Testing Only:
if __name__ == "__main__":
  lm_facade = LMFacade()
  image_bytes = lm_facade._call_gemini_for_speech_generation("In bold voice: What is the capital of france?")