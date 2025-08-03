import io
import requests
import tempfile
import os
import uuid
import mimetypes
import numpy as np
from typing import List, Dict, Any
from contextlib import contextmanager
from moviepy import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips, CompositeAudioClip, concatenate_audioclips, AudioArrayClip, AudioClip
from services.ai.framework_model import MediaUri
from services.ai.lm_facade import LMFacade
from services.storage.object_store import S3MediaManager, MediaType
import math


class VideoGenerator:
  def __init__(self, lm_facade: LMFacade, object_store: S3MediaManager):
    self.lm_facade = lm_facade
    self.object_store = object_store
    
  @contextmanager
  def _temp_directory(self):
    """Create a unique temporary directory for this session."""
    # Create a unique directory name using UUID to avoid collisions
    temp_dir = os.path.join(tempfile.gettempdir(), f"videogen_{uuid.uuid4().hex}")
    os.makedirs(temp_dir, exist_ok=True)
    try:
      yield temp_dir
    finally:
      # Clean up all files in the directory
      for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
          if os.path.isfile(file_path):
            os.unlink(file_path)
        except Exception as e:
          print(f"Error deleting {file_path}: {e}")
      # Remove the directory itself
      try:
        os.rmdir(temp_dir)
      except Exception as e:
        print(f"Error removing directory {temp_dir}: {e}")
  
  def _download_from_url(self, url: str, dest_path: str) -> str:
    """Download content from URL to specified path."""
    with requests.get(url, stream=True) as response:
      response.raise_for_status()
      with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=None):
          f.write(chunk)
    return dest_path
    
  def _get_extension_from_url(self, url: str, default_ext: str = "text/html") -> str:
    """Get file extension based on content type and URL."""
    # First, check if there's a file extension in the URL
    try:
      url_path = url.split('?')[0]  # Remove query parameters
      if '.' in os.path.basename(url_path):
        ext = os.path.splitext(url_path)[1].lower()
        if ext:
          print(f"Detected extension from URL: {ext}")
          return ext
    except Exception:
      pass
      
    # If not, attempt to determine from content type
    try:
      with requests.head(url, allow_redirects=True) as response:
        if 'Content-Type' in response.headers:
          content_type = response.headers['Content-Type'].split(';')[0].strip()
          ext = mimetypes.guess_extension(content_type)
          if ext:
            return ext
    except Exception:
      raise ValueError(f"Failed to determine file extension from URL: {url}")
        
    # Fall back to the default if we couldn't determine
    return default_ext

  def _create_video_s3_filename(self, session_id: str, step_id: str) -> str:
    return self.object_store.create_key(session_id=session_id, framework_step_id=step_id, index=0, unique_key=uuid.uuid4().hex, content_type="video/mp4")

  def generate(self, scenes: List[str], speeches: List[str], music: str, session_id: str, step_id: str) -> List[MediaUri]:
    """Generate a video from images, speeches, and music.

    Args:
      images: List of image/video URLs (one per scene).
      speeches: List of speech URLs (one per scene, corresponding to images).
      music: URL of the background music.
      session_id: Session ID for S3 storage.
      step_id: Step ID for S3 storage.
    """
    if len(scenes) == 0:
      raise ValueError("No images provided for video generation.")
    
    if len(scenes) != len(speeches):
      raise ValueError(f"Number of images ({len(scenes)}) must match number of speeches ({len(speeches)})")
        
    # Use a context manager to ensure cleanup even if exceptions occur
    with self._temp_directory() as temp_dir:
      # Download all media files to our isolated temporary directory
      local_media_paths = []
      local_speech_paths = []
      
      # Download images/videos
      for i, media_url in enumerate(scenes):
        media_ext = self._get_extension_from_url(media_url)
        media_path = os.path.join(temp_dir, f"media_{i}{media_ext}")
        self._download_from_url(media_url, media_path)
        local_media_paths.append(media_path)
      
      # Download speeches
      for i, speech_url in enumerate(speeches):
        speech_ext = self._get_extension_from_url(speech_url)
        speech_path = os.path.join(temp_dir, f"speech_{i}{speech_ext}")
        self._download_from_url(speech_url, speech_path)
        local_speech_paths.append(speech_path)
      
      # Download background music
      music_ext = self._get_extension_from_url(music)
      local_music_path = os.path.join(temp_dir, f"music{music_ext}")
      self._download_from_url(music, local_music_path)
      
      # Process each scene (image/video + speech pair)
      scene_clips = []
      scene_audio_clips = []
      
      try:
        for i, (media_path, speech_path) in enumerate(zip(local_media_paths, local_speech_paths)):
          # Load speech audio to get duration
          speech_audio = AudioFileClip(speech_path)
          speech_duration = speech_audio.duration
          
          # Create video clip based on media type
          media_type = mimetypes.guess_type(media_path)[0]
          
          if media_type and media_type.startswith("image"):
            # For images, create a clip with speech duration
            video_clip = ImageClip(media_path).with_duration(speech_duration).with_fps(24)
          elif media_type and media_type.startswith("video"):
            video_clip = VideoFileClip(media_path)
            video_duration = video_clip.duration
            
            if video_duration < speech_duration:
              # Video is shorter - first try speeding up the speech by 1.2x.
              # If that still doesn't match the video then slow the video down to match speech duration
              speech_audio = speech_audio.with_speed_scaled(1.2)
              speech_duration = speech_audio.duration
              if video_duration < speech_duration:
                speed_factor = video_duration / speech_duration
                video_clip = video_clip.with_speed_scaled(speed_factor)
            if video_duration > speech_duration:  # this is not elif because it's possible that the video is longer than the speech after speech speed adjustment
              # Video is longer - add silence after speech to match video duration
              silence_duration = video_duration - speech_duration
              
              # Create silence audio using numpy array
              silence_array = np.zeros((int(silence_duration * speech_audio.fps), 2))
              silence_audio = AudioArrayClip(silence_array, fps=speech_audio.fps)
              
              # Concatenate speech + silence to match video duration
              speech_audio = concatenate_audioclips([speech_audio, silence_audio])
              
              # Use the full video duration (no trimming)
            # If durations match, use as-is
          else:
            raise ValueError(f"Unsupported media type: {media_type} for file {media_path}")
          
          scene_clips.append(video_clip)
          scene_audio_clips.append(speech_audio)
        
        # Concatenate all scene clips
        final_video = concatenate_videoclips(scene_clips, method="compose")
        
        # Concatenate all speech clips
        final_speech = concatenate_audioclips(scene_audio_clips)
        
        # Handle background music
        music_audio = AudioFileClip(local_music_path)
        total_duration = final_video.duration
        
        if music_audio.duration < total_duration:
          # Loop music if it's shorter than video
          loops_needed = int(total_duration / music_audio.duration) + 1
          music_clips = [music_audio] * loops_needed
          looped_music: AudioClip = concatenate_audioclips(music_clips)
          background_music = looped_music.subclipped(0, total_duration).with_volume_scaled(0.20)
        else:
          # Trim music if it's longer than video
          background_music = music_audio.subclipped(0, total_duration).with_volume_scaled(0.20)
        
        # Composite final audio (speech + background music)
        composite_audio = CompositeAudioClip([final_speech, background_music])
        final_video = final_video.with_audio(composite_audio)
        
        # Export video
        output_path = os.path.join(temp_dir, "output.mp4")
        final_video.write_videofile(
          output_path, 
          codec="libx264", 
          audio_codec="aac", 
          threads=2, 
          logger=None
        )
        
        # Read and upload to S3
        with open(output_path, 'rb') as f:
          video_data = f.read()
        
        video_filename = self._create_video_s3_filename(session_id=session_id, step_id=step_id)
        result = self.object_store.upload_file(
          file_data=video_data,
          media_type=MediaType.VIDEO,
          filename=video_filename,
        )
        
        if not result:
          raise ValueError("Failed to upload video to S3.")
        
        url = self.object_store.get_file_url(filename=video_filename, media_type=MediaType.VIDEO)
        print(f"Video uploaded to S3: {url}")
        return [MediaUri(uri=url)]
        
      finally:
        # Properly close all clips to prevent the MoviePy error
        for clip in scene_clips:
          if hasattr(clip, 'close'):
            clip.close()
        for clip in scene_audio_clips:
          if hasattr(clip, 'close'):
            clip.close()
        if 'music_audio' in locals() and hasattr(music_audio, 'close'):
          music_audio.close()
        if 'final_video' in locals() and hasattr(final_video, 'close'):
          final_video.close()

  def generate_with_scenes_only(self, scenes: List[str], session_id: str, step_id: str) -> List[MediaUri]:
    """Generate a video from scenes only.

    Args:
      scenes: List of image/video URLs (one per scene).
    """
    if len(scenes) == 0:
      raise ValueError("No scenes provided for video generation.")
    
    # Use a context manager to ensure cleanup even if exceptions occur
    with self._temp_directory() as temp_dir:
      # Download all media files to our isolated temporary directory
      local_media_paths = []
      local_speech_paths = []
      
      # Download images/videos
      for i, media_url in enumerate(scenes):
        media_ext = self._get_extension_from_url(media_url)
        media_path = os.path.join(temp_dir, f"media_{i}{media_ext}")
        self._download_from_url(media_url, media_path)
        local_media_paths.append(media_path)
      
      # Process each scene (image/video + speech pair)
      scene_clips = []
      default_scene_duration = 5.0  # Default duration for each scene if no motion video is provided
      
      try:
        for i, media_path in enumerate(local_media_paths):
          # Create video clip based on media type
          media_type = mimetypes.guess_type(media_path)[0]
          
          if media_type and media_type.startswith("image"):
            # For images, create a clip with speech duration
            video_clip = ImageClip(media_path).with_duration(default_scene_duration).with_fps(24)
          elif media_type and media_type.startswith("video"):
            video_clip = VideoFileClip(media_path)
            video_duration = video_clip.duration
          
          scene_clips.append(video_clip)
        
        # Concatenate all scene clips
        final_video = concatenate_videoclips(scene_clips, method="compose")
        
        # Export video
        output_path = os.path.join(temp_dir, "output.mp4")
        final_video.write_videofile(
          output_path, 
          codec="libx264", 
          audio_codec="aac", 
          threads=2, 
          logger=None
        )
        
        # Read and upload to S3
        with open(output_path, 'rb') as f:
          video_data = f.read()
        
        video_filename = self._create_video_s3_filename(session_id=session_id, step_id=step_id)
        result = self.object_store.upload_file(
          file_data=video_data,
          media_type=MediaType.VIDEO,
          filename=video_filename,
        )
        
        if not result:
          raise ValueError("Failed to upload video to S3.")
        
        url = self.object_store.get_file_url(filename=video_filename, media_type=MediaType.VIDEO)
        print(f"Video uploaded to S3: {url}")
        return [MediaUri(uri=url)]
        
      finally:
        # Properly close all clips to prevent the MoviePy error
        for clip in scene_clips:
          if hasattr(clip, 'close'):
            clip.close()
        if 'final_video' in locals() and hasattr(final_video, 'close'):
          final_video.close()

  def analyze_duration(self, speeches: list[str]) -> list[str]:
    """
    Analyze the duration of the provided speeches S3Presigned URL and return the duration of each scene in a json formatted string.
    
    Args:
      speeches (list[str]): List of speech file paths.
    
    Returns:
      str: Json formatted string for duration of each scene in seconds.
    """
    durations = []
    with self._temp_directory() as temp_dir:
      local_speech_paths = []
      for i, speech in enumerate(speeches):
        speech_ext = self._get_extension_from_url(speech)
        local_speech_path = os.path.join(temp_dir, f"speech{i}{speech_ext}")
        self._download_from_url(speech, local_speech_path)
        local_speech_paths.append(local_speech_path)
      for idx, speech in enumerate(local_speech_paths):
        with AudioFileClip(speech) as audio_clip:
          durations.append(f"Scene{idx}: {str(math.ceil(audio_clip.duration))} seconds")
    return ["SCENE_DURATIONS_BEGIN\n" + "\n".join(durations) + "\nSCENE_DURATIONS_END\n"]

if __name__ == "__main__":
  # Example usage
  lm_facade = LMFacade()  # Assuming you have an instance of LMFacade
  object_store = S3MediaManager(framework_id="brand_awareness_video")  # Assuming you have an instance of S3MediaManager
  video_gen = VideoGenerator(lm_facade=lm_facade, object_store=object_store)
  
  images = ["https://video-brand-awareness-video.s3.us-east-2.amazonaws.com/d1fa9591-252f-415e-a77b-9b22427829b6-videos-0-10b72a4b177627089e19ab75596fff82?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEBYaCXVzLWVhc3QtMiJIMEYCIQDOz9sTjT7A8Pq3eIoB8TLszTEOHbMO4O0pbtkVuCMgVQIhANa0zA474y%2FchPPrvhJ31M6poLUUKHRNDkvFbL5qK7Z7KrkDCCAQABoMNTY3MDAwOTgxNTIyIgyztpPkGAbuHC%2BycwAqlgNt9T8VKXm32dzry5QfN0TpXLV43HqiNSfkbYS4eHz5bT3TJt2CpWZuMP%2Bv0nfKwHQmvIL9BwBs%2BRBCDHQk%2FAzRbmY3Awaj%2BwFUsif3aPU9KhCvy%2Fv5srrM9p3jCjuy7guq5pBPgCqsjJy6XBLoEAlIExlVCOEsN0V72fqbkwZFfTHsrxlNe5XeJBcNJN84G4h4ZSowZes8ed3z0znx1PKUqa2114oR3ovUrajffbUNQPTqh%2BCZAC2kgJLJ942nn5%2FJqVvORyLh%2BzJYXdPY%2BkvwQtdVJi64Hkx9X23UiK5QMtEtDcmpAoU9TQ15wH6Q5mZ6qMxaMMshyQWn8vsfC6iFDy%2BT5IeZipVcop8JuzdKfZgAvJlkR9C4EqM0ZbDh5wKU0XbIA%2FUQ50PfO5hRWj1LK%2FsuvLJbuNC3H2a6XXuEAvbG3Hr1NSCBmbhG%2B9FCZoiYud2hRTn5he%2B56GSLXQRX1fUCn0QHIabX3ddRw7AczMgUk6dAANKkcgd6iEu2JzAoF6PrpQBHek3sD8SMNdl2QGaqFscjMPaGnMMGOt0CMuJso%2F8PK8P1RjnHdZdVr8dVAAq1OcpK38P2KkrsHX03aAmge0z3Nn4qM1HDVA%2FHCZwaQqDljWZPOTn3aDxP5pOJgnL190E3eN8QqdBhil0S7uEwVBXcud%2BeW4Ilj%2FxgmnAgbgYDnpoFUS9zDE3W2J0ahQSIBhxYXSwJCa7Wgzcta7BNGwEgBSJnC1Dih0%2BYLTeo0MPiZUsOKa7kCh%2BicoCnRhCujmol%2BRvufJ%2Fqnc6LjMfyuOO9A9Y1hgAt4IoLn4PMMqh%2Bz72untLCv9E%2FamA58sRx%2BWnI1f7g803EVLzfgle9rYrhOGjtLCIF1VvxjlbXhomfDzB%2BETWOn%2BKifMkF6U86A77%2Fk6b5ZIn3B%2BvWpCT8iVdZoftg2vD%2FxlNCJIXz7P%2FDQwXxSv7is32aDQCUKhREh1ioeWSKlYsF%2BDcbbJOYSFpu%2FGGsGO4XwbHcslX%2F8%2Bmvw%2FYHac8pMw%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYIA7EMAJPCRAWLAT%2F20250703%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250703T222938Z&X-Amz-Expires=600&X-Amz-SignedHeaders=host&X-Amz-Signature=f35a2b96b20b9625387336ad07ab343e93e6e4db1785bf1915a6353e2b88b07f"]
  speeches = ["https://speech-brand-awareness-video.s3.us-east-2.amazonaws.com/d1fa9591-252f-415e-a77b-9b22427829b6-voiceover-0-2447946919fc8cdc7625d619e9ee8ee6?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEBYaCXVzLWVhc3QtMiJIMEYCIQDOz9sTjT7A8Pq3eIoB8TLszTEOHbMO4O0pbtkVuCMgVQIhANa0zA474y%2FchPPrvhJ31M6poLUUKHRNDkvFbL5qK7Z7KrkDCCAQABoMNTY3MDAwOTgxNTIyIgyztpPkGAbuHC%2BycwAqlgNt9T8VKXm32dzry5QfN0TpXLV43HqiNSfkbYS4eHz5bT3TJt2CpWZuMP%2Bv0nfKwHQmvIL9BwBs%2BRBCDHQk%2FAzRbmY3Awaj%2BwFUsif3aPU9KhCvy%2Fv5srrM9p3jCjuy7guq5pBPgCqsjJy6XBLoEAlIExlVCOEsN0V72fqbkwZFfTHsrxlNe5XeJBcNJN84G4h4ZSowZes8ed3z0znx1PKUqa2114oR3ovUrajffbUNQPTqh%2BCZAC2kgJLJ942nn5%2FJqVvORyLh%2BzJYXdPY%2BkvwQtdVJi64Hkx9X23UiK5QMtEtDcmpAoU9TQ15wH6Q5mZ6qMxaMMshyQWn8vsfC6iFDy%2BT5IeZipVcop8JuzdKfZgAvJlkR9C4EqM0ZbDh5wKU0XbIA%2FUQ50PfO5hRWj1LK%2FsuvLJbuNC3H2a6XXuEAvbG3Hr1NSCBmbhG%2B9FCZoiYud2hRTn5he%2B56GSLXQRX1fUCn0QHIabX3ddRw7AczMgUk6dAANKkcgd6iEu2JzAoF6PrpQBHek3sD8SMNdl2QGaqFscjMPaGnMMGOt0CMuJso%2F8PK8P1RjnHdZdVr8dVAAq1OcpK38P2KkrsHX03aAmge0z3Nn4qM1HDVA%2FHCZwaQqDljWZPOTn3aDxP5pOJgnL190E3eN8QqdBhil0S7uEwVBXcud%2BeW4Ilj%2FxgmnAgbgYDnpoFUS9zDE3W2J0ahQSIBhxYXSwJCa7Wgzcta7BNGwEgBSJnC1Dih0%2BYLTeo0MPiZUsOKa7kCh%2BicoCnRhCujmol%2BRvufJ%2Fqnc6LjMfyuOO9A9Y1hgAt4IoLn4PMMqh%2Bz72untLCv9E%2FamA58sRx%2BWnI1f7g803EVLzfgle9rYrhOGjtLCIF1VvxjlbXhomfDzB%2BETWOn%2BKifMkF6U86A77%2Fk6b5ZIn3B%2BvWpCT8iVdZoftg2vD%2FxlNCJIXz7P%2FDQwXxSv7is32aDQCUKhREh1ioeWSKlYsF%2BDcbbJOYSFpu%2FGGsGO4XwbHcslX%2F8%2Bmvw%2FYHac8pMw%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYIA7EMAJPCRAWLAT%2F20250703%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250703T223015Z&X-Amz-Expires=600&X-Amz-SignedHeaders=host&X-Amz-Signature=f7f31ca5dec07f7a74791723bc380106df598444d96c08a3139953c0d9dd257e"]
  music = "https://music-brand-awareness-video.s3.us-east-2.amazonaws.com/d1fa9591-252f-415e-a77b-9b22427829b6-background_music-0-9a0812fc7b36d7475529a4c2fa434274?response-content-disposition=inline&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEBYaCXVzLWVhc3QtMiJIMEYCIQDOz9sTjT7A8Pq3eIoB8TLszTEOHbMO4O0pbtkVuCMgVQIhANa0zA474y%2FchPPrvhJ31M6poLUUKHRNDkvFbL5qK7Z7KrkDCCAQABoMNTY3MDAwOTgxNTIyIgyztpPkGAbuHC%2BycwAqlgNt9T8VKXm32dzry5QfN0TpXLV43HqiNSfkbYS4eHz5bT3TJt2CpWZuMP%2Bv0nfKwHQmvIL9BwBs%2BRBCDHQk%2FAzRbmY3Awaj%2BwFUsif3aPU9KhCvy%2Fv5srrM9p3jCjuy7guq5pBPgCqsjJy6XBLoEAlIExlVCOEsN0V72fqbkwZFfTHsrxlNe5XeJBcNJN84G4h4ZSowZes8ed3z0znx1PKUqa2114oR3ovUrajffbUNQPTqh%2BCZAC2kgJLJ942nn5%2FJqVvORyLh%2BzJYXdPY%2BkvwQtdVJi64Hkx9X23UiK5QMtEtDcmpAoU9TQ15wH6Q5mZ6qMxaMMshyQWn8vsfC6iFDy%2BT5IeZipVcop8JuzdKfZgAvJlkR9C4EqM0ZbDh5wKU0XbIA%2FUQ50PfO5hRWj1LK%2FsuvLJbuNC3H2a6XXuEAvbG3Hr1NSCBmbhG%2B9FCZoiYud2hRTn5he%2B56GSLXQRX1fUCn0QHIabX3ddRw7AczMgUk6dAANKkcgd6iEu2JzAoF6PrpQBHek3sD8SMNdl2QGaqFscjMPaGnMMGOt0CMuJso%2F8PK8P1RjnHdZdVr8dVAAq1OcpK38P2KkrsHX03aAmge0z3Nn4qM1HDVA%2FHCZwaQqDljWZPOTn3aDxP5pOJgnL190E3eN8QqdBhil0S7uEwVBXcud%2BeW4Ilj%2FxgmnAgbgYDnpoFUS9zDE3W2J0ahQSIBhxYXSwJCa7Wgzcta7BNGwEgBSJnC1Dih0%2BYLTeo0MPiZUsOKa7kCh%2BicoCnRhCujmol%2BRvufJ%2Fqnc6LjMfyuOO9A9Y1hgAt4IoLn4PMMqh%2Bz72untLCv9E%2FamA58sRx%2BWnI1f7g803EVLzfgle9rYrhOGjtLCIF1VvxjlbXhomfDzB%2BETWOn%2BKifMkF6U86A77%2Fk6b5ZIn3B%2BvWpCT8iVdZoftg2vD%2FxlNCJIXz7P%2FDQwXxSv7is32aDQCUKhREh1ioeWSKlYsF%2BDcbbJOYSFpu%2FGGsGO4XwbHcslX%2F8%2Bmvw%2FYHac8pMw%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAYIA7EMAJPCRAWLAT%2F20250703%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250703T223040Z&X-Amz-Expires=240&X-Amz-SignedHeaders=host&X-Amz-Signature=bcb0f4817959669497c493862c76ade386449a8e152589a0a002c47d69275420"
  
  session_id = "session_test_12352354"
  step_id = "step_456"
  
  result = video_gen.generate(images, speeches, music, session_id, step_id)
  print(result)
