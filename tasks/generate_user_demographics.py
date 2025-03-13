from tasks.generate_base import BaseGenerator
from lm_facade import LMFacade

class UserDemographicsGenerator(BaseGenerator):
  def __init__(self, lm_facade: LMFacade):
    super().__init__(
      prompt="""As first step of brand strategy, clearly define geography, demographics, psychographics
      trying to go for a real specific sizeable audience? """,
      few_shot=[
        """
        Brand: Planterie
        Link: https://www.planterie.in/
        About: Planterie is a plant studio and café that sells air-purifying plants, terrariums,
        and planters while designing green balconies and gardens for urban homes and offices.
        Option 1: Urban Plant-Curious Millennials
        Geography: South Delhi (primary), expandable to NCR and other metro cities via social media.
        Demographics: 25-35 years old, mixed gender (60% female, 40% male), single or young couples, mid-to-high income (₹8-20 LPA), renters or new homeowners.
        Psychographics: Tech-savvy, Instagram scrollers, care about aesthetics and wellness but are new to plants—think “I want a green vibe but don’t know where to start.” Overworked, seeking calm, follow trends like minimalism and self-care, love coffee shop hangs. ||
        Option 2: Eco-Conscious Gen Z Creatives
        Geography: South Delhi (core), with reach to urban youth across India (Mumbai, Bangalore, etc.) via reels and TikTok.
        Demographics: 18-25 years old, mostly female (70%), students or early-career hustlers, moderate income (₹3-10 LPA or parental support), renting shared flats.
        Psychographics: Passionate about sustainability, artsy, glued to short-form video platforms, DIY enthusiasts, love quirky cafés, reject corporate monotony, adore plants as “pets” and self-expression, follow influencers like PlantKween or Summer Rayne Oakes. ||
        Option 3: Affluent Urban Wellness Seekers
        Geography: South Delhi (focus), NCR elites, and aspirational upper-middle-class in Tier-1 cities.
        Demographics: 30-45 years old, 50/50 gender split, married or single professionals, high income (₹20 LPA+), own homes or luxe apartments.
        Psychographics: Health nuts, yoga buffs, into air quality and mental peace, shop premium brands, value experiences over stuff, frequent cafés for “me time” or meetings, follow design trends (think Kinfolk magazine), see plants as status and serenity.
        """
      ],
      param_names=["Brand", "Link", "About"],
      lm_facade=lm_facade
    )