from enum import Enum

class AgentId(str, Enum):
  BRAND_ANALYZER = "brand_analyzer"
  VIDEO_GENERATOR = "video_generator"
  DURATION_ANALYZER = "duration_analyzer"
  SCENE_GENERATOR = "scene_generator"
