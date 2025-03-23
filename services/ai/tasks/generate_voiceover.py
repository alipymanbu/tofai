from services.ai.tasks.generate_base import BaseGenerator
from services.ai.lm_facade import LMFacade

# TODO: Implement VoiceoverGenerator class.
class VoiceoverGenerator(BaseGenerator):
  def __init__(self, lm_facade: LMFacade):
    super().__init__(
      prompt="""...
      """,
      few_shot=[],
      param_names=["Brand", "About", "User Demographics", "User Likes", "Content Vibe", "Content Spaces" , "Personality and Tonality", "Script"],
      lm_facade=lm_facade,
      output_instruction="Generate an audio. Don't output anything else.",
    )