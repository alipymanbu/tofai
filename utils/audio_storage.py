"""
Audio storage utilities for saving and retrieving audio files.
"""
import os
import logging
import base64
from typing import Optional, BinaryIO, Dict, Any
from abc import ABC, abstractmethod
import aiofiles
import aiofiles.os
from uuid import uuid4

logger = logging.getLogger(__name__)

class AudioStorage(ABC):
    """Base class for audio storage."""
    
    @abstractmethod
    async def save_audio(self, audio_data: bytes, file_name: Optional[str] = None) -> str:
        """
        Save audio data and return a URL to access it.
        
        Args:
            audio_data: The audio data to save
            file_name: Optional file name
            
        Returns:
            URL for accessing the saved audio
        """
        pass
    
    @abstractmethod
    async def get_audio(self, audio_id: str) -> Optional[bytes]:
        """
        Get audio data by ID.
        
        Args:
            audio_id: The audio ID
            
        Returns:
            Audio data if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete_audio(self, audio_id: str) -> bool:
        """
        Delete audio by ID.
        
        Args:
            audio_id: The audio ID
            
        Returns:
            True if deleted, False otherwise
        """
        pass


class LocalAudioStorage(AudioStorage):
    """Local file-based audio storage."""
    
    def __init__(self, base_dir: str = "./storage/audio"):
        """
        Initialize local audio storage.
        
        Args:
            base_dir: Directory where audio will be stored
        """
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"Initialized LocalAudioStorage at {base_dir}")
    
    async def save_audio(self, audio_data: bytes, file_name: Optional[str] = None) -> str:
        """
        Save audio data to a local file.
        
        Args:
            audio_data: Audio data to save
            file_name: Optional file name
            
        Returns:
            URL for accessing the saved audio
        """
        if not file_name:
            file_name = f"{uuid4()}.mp3"
        
        file_path = os.path.join(self.base_dir, file_name)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(audio_data)
        
        # For local development, return a simple file path
        return f"/audio/{file_name}"
    
    async def get_audio(self, audio_id: str) -> Optional[bytes]:
        """
        Get audio data by ID/path.
        
        Args:
            audio_id: File name or path
            
        Returns:
            Audio data if found
        """
        # Strip any leading path components
        file_name = os.path.basename(audio_id)
        file_path = os.path.join(self.base_dir, file_name)
        
        if not await aiofiles.os.path.exists(file_path):
            return None
        
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()
    
    async def delete_audio(self, audio_id: str) -> bool:
        """
        Delete audio file.
        
        Args:
            audio_id: File name or path
            
        Returns:
            True if deleted
        """
        # Strip any leading path components
        file_name = os.path.basename(audio_id)
        file_path = os.path.join(self.base_dir, file_name)
        
        if not await aiofiles.os.path.exists(file_path):
            return False
        
        await aiofiles.os.remove(file_path)
        return True
