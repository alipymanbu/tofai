from tasks.generate_base import BaseGenerator
from services.ai.lm_facade import LMFacade

class ContentVibeGenerator(BaseGenerator):
  def __init__(self, lm_facade: LMFacade):
    super().__init__(
      prompt="""Put down nouns and verbs that capture very wide spaces that this brand
      should want to be about in the user’s mind. """,
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
        Option 1: Serene Urban Oasis
        Nouns: Greenery, sanctuary, breath, light, calm, coffee, home, escape, growth, stillness.
        Verbs: Bloom, unwind, sip, nurture, breathe, transform, curate, recharge, glow, root.
        Vibe: Planterie’s the quiet corner of your loud city life—where plants and coffee stitch your soul back together. ||
        Option 2: Playful Green Living
        Nouns: Jungle, vibe, pot, leaf, joy, latte, corner, energy, quirk, nature.
        Verbs: Sprout, dance, sip, plant, laugh, grow, mix, perk, splash, thrive.
        Vibe: Planterie’s your cheeky sidekick—turning drab apartments into leafy playgrounds with a caffeine kick. ||
        Option 3: Mindful Modern Nature
        Nouns: Balance, air, space, stem, cup, wellness, design, peace, rhythm, earth.
        Verbs: Purify, reflect, brew, tend, harmonize, cultivate, soften, renew, connect, ground.
        Vibe: Planterie’s the bridge between urban hustle and natural zen—sleek, soulful, and effortlessly cool.
        """
      ],
      param_names=["Brand", "About", "User Demographics", "User Likes"],
      lm_facade=lm_facade
    )