import io
import requests
import tempfile
import os
import uuid
import mimetypes
from typing import List, Dict, Any
from contextlib import contextmanager
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip, concatenate_audioclips
from services.ai.framework_model import MediaUri
from services.ai.lm_facade import LMFacade
from services.storage.object_store import S3MediaManager, MediaType


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
      pass
        
    # Fall back to the default if we couldn't determine
    return default_ext

  def _create_video_s3_filename(self, session_id: str, step_id: str) -> str:
    return self.object_store.create_key(session_id=session_id, framework_step_id=step_id, index=0, unique_key=uuid.uuid4().hex)

  def generate(self, images: List[str], speech: str, music: str, session_id: str, step_id: str) -> List[MediaUri]:
    """Generate a video from images, speech, and music.

    Args:
      images: List of image URLs.
      speech: URL of the speech audio.
      music: URL of the background music.
      video_filename: Name of the output video file to be written to S3.
    """
    # print(f"Generating video with {images} images, speech: {speech}, music: {music}")
    if len(images) == 0:
      raise ValueError("No images provided for video generation.")
        
    # Use a context manager to ensure cleanup even if exceptions occur
    with self._temp_directory() as temp_dir:
      # Download all media files to our isolated temporary directory
      local_image_paths = []
      for i, image in enumerate(images):
        # Get appropriate extension for the image
        img_ext = self._get_extension_from_url(image)
        img_path = os.path.join(temp_dir, f"img_{i}{img_ext}")
        self._download_from_url(image, img_path)
        local_image_paths.append(img_path)
      
      # Get appropriate extensions for audio files
      speech_ext = self._get_extension_from_url(speech)
      local_speech_path = os.path.join(temp_dir, f"speech{speech_ext}")
      self._download_from_url(speech, local_speech_path)
      
      music_ext = self._get_extension_from_url(music)
      local_music_path = os.path.join(temp_dir, f"music{music_ext}")
      self._download_from_url(music, local_music_path)
      
      # Process with MoviePy
      with AudioFileClip(local_speech_path) as speech_audio:
        with AudioFileClip(local_music_path) as music_audio:
          speech_duration = speech_audio.duration
          music_duration = music_audio.duration
          duration = speech_duration
          
          # Calculate duration per image
          image_duration = float(duration / len(images))
          
          # Create video clips
          image_clips = []
          try:
            for img_path in local_image_paths:
              clip = ImageClip(img_path).with_duration(image_duration).with_fps(24)
              image_clips.append(clip)
            
            # Combine clips
            video = concatenate_videoclips(image_clips, method="compose")
            
            # # Add audio
            # with AudioFileClip(local_music_path) as music_audio:
            if music_duration < duration:
              loops_needed = int(duration / music_duration) + 1
              music_clips = [music_audio] * loops_needed
              looped_music = concatenate_audioclips(music_clips)
              music_clip = looped_music.subclipped(0, duration).with_volume_scaled(0.25)
            else:
              music_clip = music_audio.subclipped(0, duration).with_volume_scaled(0.25)
            speech_clip = speech_audio.subclipped(0, duration)
            composite_audio = CompositeAudioClip([speech_clip, music_clip])
            video = video.with_audio(composite_audio)
            
            # Output file path
            output_path = os.path.join(temp_dir, "output.mp4")
            
            # Write the video file
            video.write_videofile(output_path, codec="libx264", audio_codec="aac", 
                                 threads=2, logger=None)
                                 
            # Read the output file
            with open(output_path, 'rb') as f:
              video_data = f.read()
              
            # Upload to S3
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
            # Make sure to close all image clips
            for clip in image_clips:
              clip.close()
            
            # Close the final video if it exists
            if 'video' in locals():
              video.close()


if __name__ == "__main__":
  # Example usage
  lm_facade = LMFacade()  # Assuming you have an instance of LMFacade
  object_store = S3MediaManager(framework_id="brand_awareness_video")  # Assuming you have an instance of S3MediaManager
  video_gen = VideoGenerator(lm_facade=lm_facade, object_store=object_store)
  
  images = ["https://image-brand-awareness-video.s3.amazonaws.com/0f970027-8568-412f-a53b-2430d75f4078-images-0-1ebcc52c9a5b4b062a6e822a006d543c?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAYIA7EMAJPYDMQYG4%2F20250426%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250426T231133Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=523dc2b873d1bfdafb3fa277ccdabce45e8d47fc6f83b2375c8506044b6f3222", "https://image-brand-awareness-video.s3.amazonaws.com/0f970027-8568-412f-a53b-2430d75f4078-images-1-1ebcc52c9a5b4b062a6e822a006d543c?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAYIA7EMAJPYDMQYG4%2F20250426%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250426T231157Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=cbbe066817c5c4e9bb779cd291122f54f542691a5e717bbe11c3cb7a52e6b18d", "https://image-brand-awareness-video.s3.amazonaws.com/0f970027-8568-412f-a53b-2430d75f4078-images-2-1ebcc52c9a5b4b062a6e822a006d543c?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAYIA7EMAJPYDMQYG4%2F20250426%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250426T231220Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=47bedaa576dbe4ac2b64ebd13ed50c87af4abe650da29429ea1ed908da2c4881"]
  speech = "https://speech-brand-awareness-video.s3.amazonaws.com/0f970027-8568-412f-a53b-2430d75f4078-voiceover-0-8228a87d2e93546332569742d52aa632?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAYIA7EMAJPYDMQYG4%2F20250426%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250426T231540Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=380f58d082edde1aafe9e111e33a2a40e7c5e677376c4eff27499102e42750e7"
  music = "https://speech-brand-awareness-video.s3.amazonaws.com/0f970027-8568-412f-a53b-2430d75f4078-background_music-0-6cba5c64dffca8060034e3c38d5209fe?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAYIA7EMAJPYDMQYG4%2F20250426%2Fus-east-2%2Fs3%2Faws4_request&X-Amz-Date=20250426T231607Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=687035fc2f4995d1cbb1ed11ea636ca5de02f7c849e5a07b5ca4d55964743332"
  
  session_id = "session_test_12352354"
  step_id = "step_456"
  
  result = video_gen.generate(images, speech, music, session_id, step_id)
  print(result)