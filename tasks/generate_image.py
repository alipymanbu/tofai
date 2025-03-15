from tasks.generate_base import BaseGenerator
from lm_facade import LMFacade

class ImageGenerator(BaseGenerator):
  def __init__(self, lm_facade: LMFacade):
    super().__init__(
      prompt="""Taking into account the brand strategy above, let's generate a few
      visuals for the Script below. Imagine the script is playing as a video in
      front of you, for each scene generate the most important moment of the video,
      and create an image that could literally be screengrab of the video. This will
      help us identify what is the visual vibe of the video. 

      Script:
      """,
      few_shot=[],
      param_names=["Brand", "About", "User Demographics", "User Likes", "Content Vibe", "Content Spaces" , "Personality and Tonality", "Script"],
      lm_facade=lm_facade,
      output_instruction="Generate an image for each scene for the script. Don't output anything else. Seperate the images with `||`."
    )