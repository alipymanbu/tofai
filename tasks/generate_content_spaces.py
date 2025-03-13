from tasks.generate_base import BaseGenerator
from lm_facade import LMFacade

class ContentSpacesGenerator(BaseGenerator):
  def __init__(self, lm_facade: LMFacade):
    super().__init__(
      prompt="""What are the actual topics that we can create content upon, doesn’t have to be salesy.
      If this was a person hanging out in a close knit circle at a house party what would they
      talk about? """,
      few_shot=[
        """
        Brand: Planterie
        About: Planterie is a plant studio and café that sells air-purifying plants, terrariums,
        and planters while designing green balconies and gardens for urban homes and offices.
        User Demographics: Urban Plant-Curious Millennials
        Geography: South Delhi (primary), expandable to NCR and other metro cities via social media.
        Demographics: 25-35 years old, mixed gender (60% female, 40% male), single or young couples, mid-to-high income (₹8-20 LPA), renters or new homeowners.
        Psychographics: Tech-savvy, Instagram scrollers, care about aesthetics and wellness but are new to plants—think “I want a green vibe but don’t know where to start.” Overworked, seeking calm, follow trends like minimalism and self-care, love coffee shop hangs.
        User Likes: Relatable, Self-Deprecating Humor
        Style: Quick, quirky skits with a “millennial fail” vibe—think awkward plant-parenting mishaps or caffeine-fueled chaos.
        Why They Love It: They’re stressed and laugh at their own messes (e.g., forgetting to water plants or over-ordering oat milk lattes).
        Hook Examples:
        “Day 1: Me and my plant are besties. Day 3: Why is it brown?” (Cut to panicked googling.)
        “Me buying a plant to ‘fix my life’—now I’m broke and it’s dying.” (Zoom on sad plant.)
        Tone: Goofy, exaggerated, Tim Urban-esque absurdity meets Ogilvy’s punchy relatability.
        Content Vibe: Serene Urban Oasis
        Nouns: Greenery, sanctuary, breath, light, calm, coffee, home, escape, growth, stillness.
        Verbs: Bloom, unwind, sip, nurture, breathe, transform, curate, recharge, glow, root.
        Vibe: Planterie’s the quiet corner of your loud city life—where plants and coffee stitch your soul back together.
        Option 1: How Plants Turned My Balcony Into a Breathing Space ||
        Option 2: Coffee and Leaves: My Morning Ritual Just Got Greener ||
        Option 3: Why My Apartment Feels Like a Forest Now ||
        Option 4: The Secret to Calming Chaos with One Terrarium ||
        Option 5: Air-Purifying Plants That Saved My Work-from-Home Sanity ||
        Option 6: Sipping Lattes in South Delhi’s Leafiest Hideout ||
        Option 7: How I Grew a Garden in a Shoebox Flat ||
        Option 8: Plants That Make You Feel Less Alone in the City ||
        Option 9: The Zen of Watering: My 5-Minute Escape ||
        Option 10: Transforming My Desk with a Single Succulent ||
        Option 11: Why Greenery Is My New Self-Care Obsession ||
        Option 12: Coffee Shop Vibes You Can Bring Home with Plants ||
        Option 13: How a Planter Changed My Tiny Rental Forever ||
        Option 14: Breathing Easier: Plants That Fight Delhi’s Dust ||
        Option 15: Curating Calm: My Journey with a Mini Jungle ||
        Option 16: The Plant That Bloomed When I Couldn’t ||
        Option 17: Unwinding with Leaves After a 12-Hour Day ||
        Option 18: South Delhi’s Best-Kept Secret: A Café with Roots ||
        Option 19: How I Nurtured Peace in a Concrete Jungle ||
        Option 20: Glow Up Your Space with One Simple Pot
        """
      ],
      param_names=["Brand", "About", "User Demographics", "User Likes", "Content Vibe"],
      output_instruction="Give me 20 word headlines for these stories, add `||` between the options. Do not output anything else.",
      lm_facade=lm_facade
    )