from tasks.generate_base import BaseGenerator
from lm_facade import LMFacade

class UserLikesGenerator(BaseGenerator):
  def __init__(self, lm_facade: LMFacade):
    super().__init__(
      prompt="""What kind of videos does the user enjoy right now: humor- what kind of
      humor, artsy what kind of? This will help define the hooks (the first 5 seconds
      of the video). """,
      few_shot=[
        """
        Brand: Planterie
        Link: https://www.planterie.in/
        About: Planterie is a plant studio and café that sells air-purifying plants, terrariums,
        and planters while designing green balconies and gardens for urban homes and offices.
        User Demographics: Urban Plant-Curious Millennials
        Geography: South Delhi (primary), expandable to NCR and other metro cities via social media.
        Demographics: 25-35 years old, mixed gender (60% female, 40% male), single or young couples, mid-to-high income (₹8-20 LPA), renters or new homeowners.
        Psychographics: Tech-savvy, Instagram scrollers, care about aesthetics and wellness but are new to plants—think “I want a green vibe but don’t know where to start.” Overworked, seeking calm, follow trends like minimalism and self-care, love coffee shop hangs.
        Option 1: Relatable, Self-Deprecating Humor
        Style: Quick, quirky skits with a “millennial fail” vibe—think awkward plant-parenting mishaps or caffeine-fueled chaos.
        Why They Love It: They’re stressed and laugh at their own messes (e.g., forgetting to water plants or over-ordering oat milk lattes).
        Hook Examples:
        “Day 1: Me and my plant are besties. Day 3: Why is it brown?” (Cut to panicked googling.)
        “Me buying a plant to ‘fix my life’—now I’m broke and it’s dying.” (Zoom on sad plant.)
        Tone: Goofy, exaggerated, Tim Urban-esque absurdity meets Ogilvy’s punchy relatability. ||
        Option 2: Aesthetic, Minimalist Eye-Candy
        Style: Visually stunning, artsy shots—slow pans of lush plants, soft lo-fi beats, cozy café corners, ASMR vibes.
        Why They Love It: They’re suckers for #AestheticGoals, crave calm amidst chaos, and double-tap anything that screams “Pinterest-worthy.”
        Hook Examples:
        (Close-up of dew on a leaf) “This plant’s living better than me.” (Pan to a chic terrarium.)
        (Pouring coffee in slow-mo) “Caffeine and chlorophyll—my therapy.” (Reveal a green balcony.)
        Tone: Veritasium’s polish with a Vsauce twist of unexpected wonder. ||
        Option 3: Playful, Trend-Driven Challenges
        Style: Fast-paced, meme-y, riding TikTok/Insta trends—think plant-care hacks or “rate my setup” challenges.
        Why They Love It: They’re trend-chasers, love interactive vibes, and share stuff that makes them look “in the know.”
        Hook Examples:
        “Plant people, rate my vibe: 1-10!” (Quick cut to a quirky terrarium.)
        “Turning my balcony into a jungle—send help!” (Timelapse of chaos.)
        Tone: High-energy, Tim Urban’s playful curiosity with Ogilvy’s clever hooks."""
      ],
      param_names=["Brand", "Link", "About", "User Demographics"],
      lm_facade=lm_facade
    )