from tasks.generate_base import BaseGenerator
from services.ai.lm_facade import LMFacade

class BrandAboutGenerator(BaseGenerator):
  def __init__(self, lm_facade: LMFacade):
    super().__init__(
      prompt="""As first step of brand strategy, in one line clearly and precisely write down
      what is the following brand about? """,
      few_shot=[
        """
        Brand: Adidas
        Link: https://www.adidas.com
        Option 1: Global leader in athletic wear, blending technology with fashion. ||
        Option 2: Empowering athletes worldwide with innovative sportswear. ||
        Option 3: Sustainable and high-performance sportswear, pushing boundaries in design.""",
        """
        Brand: Apple
        Link: https://www.apple.com
        Option 1: Pioneering technology that changes the world, one device at a time. ||
        Option 2: Creating seamless experiences with cutting-edge tech. ||
        Option 3: Innovative products that inspire creativity and productivity."""
      ],
      param_names=["Brand", "Link"],
      lm_facade=lm_facade
    )