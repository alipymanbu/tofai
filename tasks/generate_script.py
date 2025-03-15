from tasks.generate_base import BaseGenerator
from lm_facade import LMFacade

class ScriptGenerator(BaseGenerator):
  def __init__(self, lm_facade: LMFacade):
    super().__init__(
      prompt="""Write the scripts for the ideas shortlisted. Please ensure that you
        start with a hook that we had shortlisted earlier. Dont make the script salsey.
        The main point is to capture attention, get the user to reach the end of the
        video and remember/feel something about the brand.""",
      few_shot=[
        """
        Brand: Planterie
        About: Planterie is a plant studio and café that sells air-purifying plants, terrariums,
        and planters while designing green balconies and gardens for urban homes and offices.
        User Demographics: Urban Plant-Curious Millennials
        Geography: South Delhi (primary), expandable to NCR and other metro cities via social media.
        Demographics: 25-35 years old, mixed gender (60% female, 40% male), single or young couples, mid-to-high income (₹8-20 LPA), renters or new homeowners.
        Psychographics: Tech-savvy, Instagram scrollers, care about aesthetics and wellness but are new to plants—think “I want a green vibe but don’t know where to start.” Overworked, seeking calm, follow trends like minimalism and self-care, love coffee shop hangs.
        User Likes: Aesthetic, Minimalist Eye-Candy
        Style: Visually stunning, artsy shots—slow pans of lush plants, soft lo-fi beats, cozy café corners, ASMR vibes.
        Why They Love It: They’re suckers for #AestheticGoals, crave calm amidst chaos, and double-tap anything that screams “Pinterest-worthy.”
        Hook Examples:
        (Close-up of dew on a leaf) “This plant’s living better than me.” (Pan to a chic terrarium.)
        (Pouring coffee in slow-mo) “Caffeine and chlorophyll—my therapy.” (Reveal a green balcony.)
        Tone: Veritasium’s polish with a Vsauce twist of unexpected wonder.
        Content Vibe: Serene Urban Oasis
        Nouns: Greenery, sanctuary, breath, light, calm, coffee, home, escape, growth, stillness.
        Verbs: Bloom, unwind, sip, nurture, breathe, transform, curate, recharge, glow, root.
        Vibe: Planterie’s the quiet corner of your loud city life—where plants and coffee stitch your soul back together.
        Content Spaces:
        How Plants Turned My Balcony Into a Breathing Space.
        The Secret to Calming Chaos with One Terrarium.
        The Zen of Watering: My 5-Minute Escape.
        Breathing Easier: Plants That Fight Delhi’s Dust.
        Personality and Tonality: The Quirky Green Guru
        Personality: Planterie’s the eccentric pal who’s obsessed with plants and coffee, a bit nerdy but endlessly charming—like a botanist crossed with a stand-up comedian. Curious, playful, and quietly confident.
        Tonality: Witty, lighthearted, oddly profound—like Vsauce with a caffeine buzz.
        Story Lines:
        “He plops a terrarium on my table and says, ‘This is your new therapist—cheaper than the last one.’”
        “Grinning, he claims plants are just slow pets, then dares me to name my pothos ‘Sir Leafington.’”
        Script 1: How Plants Turned My Balcony Into a Breathing Space
        Hook (0:00-0:05): (Slow pan of dew on a leaf) “This plant’s living better than me.” (Cut to a cluttered balcony.)

        Body (0:06-0:35):
        (Voiceover, quirky tone) “Meet my balcony: a sad little slab of concrete begging for love. So, I got a plant—okay, five. Look at this guy!” (Zoom on a lush fern swaying.)
        “Suddenly, it’s not just a balcony—it’s where I breathe. Like, actual oxygen, not just Delhi dust!” (Cut to a goofy grin, sipping coffee.)
        “Who knew a few leaves could outsmart my Wi-Fi at calming me down?” (Pan to a serene green corner, lo-fi beat swells.)
        End (0:36-0:40): (Text on screen: “Breathe better. One leaf at a time.”) (Voiceover) “Call it my slow rebellion against city chaos.”
        Feel: Playful wonder—Planterie’s the quirky friend who turns mundane spaces magical. ||
        Script 2: The Secret to Calming Chaos with One Terrarium
        Hook (0:00-0:05): (Pouring coffee in slow-mo) “Caffeine and chlorophyll—my therapy.” (Reveal a tiny terrarium.)

        Body (0:06-0:35):
        (Voiceover, lighthearted) “Life’s a mess—emails, traffic, that one sock I can’t find. Then I met this little guy.” (Zoom on terrarium, moss glistening.)
        “It’s like a therapist in a jar. Five minutes staring at it, and I forget my boss exists.” (Cut to a sly wink.)
        “Chaos? Still there. Me? Weirdly chill—like this moss knows something I don’t.” (Soft giggle, pan to coffee steam curling.)
        End (0:36-0:40): (Text on screen: “Chaos, meet calm.”) (Voiceover) “Proof tiny things fix big problems.”
        Feel: Oddly profound—Planterie’s the guru who sneaks peace into your hectic day. ||

        Script 3: The Zen of Watering: My 5-Minute Escape
        Hook (0:00-0:05): (Close-up of dew on a leaf) “This plant’s living better than me.” (Cut to a hand with a watering can.)

        Body (0:06-0:35):
        (Voiceover, witty) “Work’s a dumpster fire, my inbox is screaming—then I grab this.” (Slow pour of water on a plant, ASMR drip.)
        “Five minutes watering, and I’m basically a monk. Look at these leaves vibing harder than my Spotify playlist!” (Zoom on a perky plant.)
        “It’s not just hydration—it’s a getaway. No passport, just a can.” (Cut to a dramatic sip of coffee.)
        End (0:36-0:40): (Text on screen: “Escape’s a pour away.”) (Voiceover) “Who needs a vacation when you’ve got leaves?”
        Feel: Lighthearted calm—Planterie’s the quirky escape hatch in a frantic life.
        """
      ],
      param_names=["Brand", "About", "User Demographics", "User Likes", "Content Vibe", "Content Spaces" , "Personality and Tonality"],
      lm_facade=lm_facade
    )