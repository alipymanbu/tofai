from services.ai.tasks.generate_base import BaseGenerator
from services.ai.lm_facade import LMFacade

class PersonalityGenerator(BaseGenerator):
  def __init__(self, lm_facade: LMFacade):
    super().__init__(
      prompt="""who is the brand like if it was a person, what is the voice of the brand like,
      give us two lines of a story to help us envision it? """,
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
        Content Spaces:
        How Plants Turned My Balcony Into a Breathing Space.
        The Secret to Calming Chaos with One Terrarium.
        The Zen of Watering: My 5-Minute Escape.
        Breathing Easier: Plants That Fight Delhi’s Dust.
        Option 1: The Gentle Plant Whisperer
        Personality: Planterie’s that friend who’s always calm under pressure, a soft-spoken soul with a knack for making chaos feel manageable—like a yoga instructor who moonlights as a barista. Warm, wise, and a little dreamy.
        Tonality: Soothing, poetic, inviting—like a deep breath in word form. Think gentle nudges over loud shouts.
        Story Lines:
        “She leans over my wilting fern, whispering, ‘You’ve got this,’ and somehow, it perks up by morning.”
        “Over coffee, she tells me Delhi’s smog isn’t the boss of us—then hands me a plant to prove it.” ||
        Option 2: The Quirky Green Guru
        Personality: Planterie’s the eccentric pal who’s obsessed with plants and coffee, a bit nerdy but endlessly charming—like a botanist crossed with a stand-up comedian. Curious, playful, and quietly confident.
        Tonality: Witty, lighthearted, oddly profound—like Vsauce with a caffeine buzz.
        Story Lines:
        “He plops a terrarium on my table and says, ‘This is your new therapist—cheaper than the last one.’”
        “Grinning, he claims plants are just slow pets, then dares me to name my pothos ‘Sir Leafington.’” ||
        Option 3: The Chic Urban Sage
        Personality: Planterie’s the stylish friend who’s got it all together—think a design-savvy minimalist with a secret soft spot for nature. Cool, collected, and effortlessly inspiring.
        Tonality: Sleek, aspirational, warm—like a Kinfolk article with a Delhi twist.
        Story Lines:
        “She sips her latte and says, ‘One plant can rewrite your whole space,’ then proves it with a single pot.”
        “With a smirk, she tells me my balcony’s begging for green—and suddenly, it’s the chicest spot in town.”
        """
      ],
      param_names=["Brand", "About", "User Demographics", "User Likes", "Content Vibe", "Content Spaces"],
      lm_facade=lm_facade
    )