from pydantic import BaseModel
from typing import List, Tuple, Optional, Union

# ======== Define constants ========

# Node keys
INITIAL_INPUT_STEP = "initial_step"
STRATEGY_STEP = "strategy_step"
SCRIPT_STEP = "script_step"
IMAGES_STEP = "images_step"
ANIMATION_STEP = "animation_step"
VOICEOVER_STEP = "voiceover_step"
BACKGROUND_MUSIC_STEP = "background_music_step"
FINAL_VIDEO_STEP = "final_video_step"

# Options handling keys
GENERATE_OPTIONS = "generate_options"
SELECT_OPTION = "select_option"
GENERATE_SCRIPT_OPTIONS = "generate_script_options"
SELECT_SCRIPT = "select_script"

# Strategy elements
BRAND_ABOUT_STRATEGY_ELEMENT = "brand_about"
USER_DEMOGRAPHICS_STRATEGY_ELEMENT = "user_demographics"
USER_LIKES_STRATEGY_ELEMENT = "user_likes"
CONTENT_VIBE_STRATEGY_ELEMENT = "content_vibe"
CONTENT_SPACES_STRATEGY_ELEMENT = "content_spaces"
PERSONALITY_TONALITY_STRATEGY_ELEMENT = "personality_tonality"

# ======== Define state class ========
# Define the state class to hold all data throughout the process
class VideoCreationState(BaseModel):
    brand_name: Optional[str] = None  # Brand name
    brand_link: Optional[str] = None  # Brand website
    brand_about: Optional[str] = None  # Select Brand about
    user_demographics: Optional[str] = None  # Selected User demographics
    user_likes: Optional[str] = None  # Selected User likes
    content_vibe: Optional[str] = None  # Selected content vibe
    content_spaces: Optional[str] = None  # Selected story headline
    personality_tonality: Optional[str] = None  # Selected personality tonality
    script: Optional[List[Tuple[str, float]]] = None  # Selected List of (scene description, duration in seconds)
    images: List[bytes] = []  # Approved images for each scene
    animation: Optional[bytes] = None  # Animation for the video
    voiceover: Optional[bytes] = None  # voiceover (audio) for the video
    background_music: Optional[bytes] = None  # Background music for the video
    final_video: Optional[bytes] = None  # Final video
    current_options: List[Union[str, bytes]] = []
    current_scene_index: int = 0
    brand_strategy_elements: List[str] = [
        BRAND_ABOUT_STRATEGY_ELEMENT,
        USER_DEMOGRAPHICS_STRATEGY_ELEMENT,
        USER_LIKES_STRATEGY_ELEMENT,
        CONTENT_VIBE_STRATEGY_ELEMENT,
        CONTENT_SPACES_STRATEGY_ELEMENT,
        PERSONALITY_TONALITY_STRATEGY_ELEMENT
    ]
    current_brand_strategy_element_index: int = 0
    next: Optional[str] = None  # For conditional transitions