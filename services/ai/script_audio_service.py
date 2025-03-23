"""
Service for handling script-to-audio conversion.
"""
from typing import Dict, Any, List, Optional
import logging
from services.ai.tts_service import TTSService

logger = logging.getLogger(__name__)

class ScriptAudioService:
    """Service for generating audio from script content."""
    
    def __init__(self):
        """Initialize the script audio service."""
        self.tts_service = TTSService()
        logger.info("Initialized ScriptAudioService")
    
    async def generate_audio_for_script(
        self,
        script: Dict[str, Any],
        voice_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Generate audio files for each scene in a script.
        
        Args:
            script: Script data with scenes
            voice_id: Voice ID to use for TTS
            
        Returns:
            Dict with audio data for each scene
        """
        if not script or "scenes" not in script:
            return {
                "success": False,
                "error": "Invalid script format. Expected script with 'scenes' array."
            }
        
        scenes = script.get("scenes", [])
        if not scenes:
            return {
                "success": False,
                "error": "Script has no scenes."
            }
        
        audio_results = []
        
        for scene in scenes:
            scene_number = scene.get("sceneNumber", 0)
            narration = scene.get("narration", "")
            
            if not narration:
                logger.warning(f"Scene {scene_number} has no narration text")
                continue
            
            try:
                audio_result = await self.tts_service.generate_speech(
                    text=narration,
                    voice_id=voice_id
                )
                
                # Add scene info to the result
                audio_result["scene_number"] = scene_number
                audio_result["text"] = narration
                
                audio_results.append(audio_result)
                
            except Exception as e:
                logger.exception(f"Error generating audio for scene {scene_number}: {str(e)}")
                return {
                    "success": False,
                    "error": f"Failed to generate audio for scene {scene_number}: {str(e)}"
                }
        
        return {
            "success": True,
            "audio_data": audio_results,
            "total_scenes": len(scenes),
            "scenes_with_audio": len(audio_results)
        }
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get a list of available voices.
        
        Returns:
            List of voice data
        """
        return await self.tts_service.get_available_voices()
