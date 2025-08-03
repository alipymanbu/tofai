from enum import Enum

class AgentId(str, Enum):
  BRAND_ANALYZER = "brand_analyzer"
  VIDEO_GENERATOR = "video_generator"
  DURATION_ANALYZER = "duration_analyzer"
  VIDEO_GENERATOR_V2 = "video_generator_v2"
