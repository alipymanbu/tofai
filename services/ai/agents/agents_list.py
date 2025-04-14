from enum import Enum
from typing import Any
from services.ai.agents.brand_analyzer import BrandAnalyzer

class AgentId(str, Enum):
  BRAND_ANALYZER = "brand_analyzer"

def get_agent_call(id: AgentId, **kwargs) -> Any:
    if id == AgentId.BRAND_ANALYZER:
        return BrandAnalyzer(lm_facade=kwargs["lm_facade"]).analyze_brand(kwargs["param_values"]["Link"])
    return None