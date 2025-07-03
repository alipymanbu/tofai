from typing import Any, Dict, List, Optional, Union
from services.ai.framework_model import MediaUri
from services.ai.agents.brand_analyzer import BrandAnalyzer
from services.ai.agents.video_generator import VideoGenerator
from services.ai.agents.agents_list import AgentId

def get_agent_call(id: AgentId, **kwargs) -> Optional[List[Union[str, MediaUri]]]:
    if id == AgentId.BRAND_ANALYZER:
        return BrandAnalyzer(lm_facade=kwargs["lm_facade"]).analyze_brand(kwargs["param_values"]["Link"])
    if id == AgentId.VIDEO_GENERATOR:
        return VideoGenerator(
            lm_facade=kwargs["lm_facade"], 
            object_store=kwargs["s3"]
          ).generate(
              images=kwargs["param_values"]["Videos"],
              speeches=kwargs["param_values"]["Voiceover"],
              music=kwargs["param_values"]["Background Music"],
              session_id=kwargs["session_id"],
              step_id=kwargs["step_id"])
    if id == AgentId.DURATION_ANALYZER:
        return VideoGenerator(
            lm_facade=kwargs["lm_facade"], 
            object_store=kwargs["s3"]
          ).analyze_duration(speeches=kwargs["param_values"]["Voiceover"])
    return None