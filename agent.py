# agent.py
from langgraph.graph import StateGraph, START, END
from typing import List, Tuple, Optional
import state as st
from state import VideoCreationState
from lm_facade import LMFacade

lm_facade = LMFacade()
prefix = """You are the best marketer on Earth specifically specialising in video
  storytelling that helps brands get reach on social media. You are weird like Vsauce,
  thorough like Veritasium, goofy and imaginative like Tim Urban, and can write copy
  like David Ogilvy. You do this by marrying brand strategy and user passion points."""
output_format_prompt = "Give me 3 options, add `||` between the options. Do not output anything else."

def current_strategy(state: VideoCreationState) -> str:
    return state.brand_strategy_elements[state.current_brand_strategy_element_index]

def parse_text_options(lm_output: str) -> List[str]:
    return [opt.strip('\n ') for opt in lm_output.strip().split("||") if opt.strip('\n ')]

# Placeholder generation functions (replace with actual LLM/media API calls)
def generate_brand_about_options_func(brand_name: str, brand_link: str) -> List[str]:
    prompt = f"""As first step of brand strategy, in one line clearly and precisely write down
      what is the following brand about? {output_format_prompt}

      Examples:
      Brand: Adidas
      Link: https://www.adidas.com
      Option 1: Global leader in athletic wear, blending technology with fashion. ||
      Option 2: Empowering athletes worldwide with innovative sportswear. ||
      Option 3: Sustainable and high-performance sportswear, pushing boundaries in design.

      Brand: Apple
      Link: https://www.apple.com
      Option 1: Pioneering technology that changes the world, one device at a time. ||
      Option 2: Creating seamless experiences with cutting-edge tech. ||
      Option 3: Innovative products that inspire creativity and productivity.

      Now, your turn:
      Brand: {brand_name}
      Link: {brand_link}"""
    response = lm_facade.invoke_t2t(f"{prefix}\n{prompt}")
    return parse_text_options(response)

def generate_user_demographics_options_func(brand_name: str, brand_link: str, brand_about: str) -> List[str]:
    prompt = f"""As first step of brand strategy, clearly define geography, demographics, psychographics
          trying to go for a real specific sizeable audience? {output_format_prompt}
          
          Examples:
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

          Now, your turn:
          Brand: {brand_name}
          Link: {brand_link}
          About: {brand_about}"""
    response = lm_facade.invoke_t2t(f"{prefix}\n{prompt}")
    return parse_text_options(response)

def generate_user_likes_options_func(user_demographics: str) -> List[str]:
    return [
        "Short, witty skits with dry humor.",
        "Sleek, artsy montages with vibrant colors.",
        "Relatable vlogs with a warm tone."
    ]

def generate_content_vibe_options_func() -> List[str]:
    return [
        "Bold, energetic, innovate, disrupt.",
        "Calm, authentic, connect, inspire.",
        "Fun, quirky, play, surprise."
    ]

def generate_content_spaces_options_func() -> List[str]:
    return [
        "How sustainable fashion shapes our future in 20 words.",
        "Tech hacks that make life easier, shared at a party.",
        "The art of brewing coffee everyone talks about tonight."
    ]

def generate_personality_tonality_options_func() -> List[str]:
    return [
        "Like a bold explorer: 'We ventured into the wild.' 'The horizon called back.'",
        "Like a wise friend: 'I’ve seen this before.' 'Here’s what I learned.'",
        "Like a quirky artist: 'Paint splattered everywhere.' 'Chaos turned beautiful.'"
    ]

def generate_script_options_func(brand_strategy: dict) -> List[str]:
    hook = brand_strategy["user_likes"].split(" ")[0]  # Simplified hook extraction
    return [
        f"[{hook}] Scene 1: Bold visuals of nature (3s). Scene 2: People connect over ideas (4s).",
        f"[{hook}] Scene 1: Quiet moment of reflection (2s). Scene 2: Brand inspires subtly (5s).",
        f"[{hook}] Scene 1: Quirky character appears (3s). Scene 2: Fun twist unfolds (4s)."
    ]

def generate_image_func(scene_description: str) -> bytes:
    return bytes(f"Image for '{scene_description}'", "utf-8")

def create_animation_func(script: List[Tuple[str, float]], images: List[bytes], voiceover: bytes, background_music: bytes) -> bytes:
    # Simulate stitching images into an animation (e.g., using OpenCV or MoviePy)
    return b"Animation created from images"

def generate_voiceover_func(script: List[Tuple[str, float]]) -> bytes:
    # Simulate text-to-speech
    return b"Voiceover audio for script"

def generate_music_func(description: str) -> bytes:
    # Simulate music generation
    return b"Background music"

def add_music_to_video_func(video: str, music: str) -> str:
    return f"{video} with {music}"

# Node functions
def collect_initial_input(state: VideoCreationState) -> dict:
  print("Let's create a stunning brand awareness video!")
  brand_name = input("What's your brand called? ")
  brand_link = input("Got a link to your brand's website or online presence? ") # Commenting out brand_link for simplification
  output_dict = {
    "brand_name": brand_name,
    "brand_link": brand_link, # Commenting out brand_link for simplification
    "current_brand_strategy_element_index": 0, # Keep this to ensure flow continues
    "next": "generate_options"
  }
  print(f"collect_initial_input returning: {output_dict}") # Debug print
  return output_dict

def generate_options(state: VideoCreationState) -> dict:
  element = current_strategy(state)
  if element == st.BRAND_ABOUT_STRATEGY_ELEMENT:
    current_options = generate_brand_about_options_func(state.brand_name, state.brand_link)
  elif element == st.USER_DEMOGRAPHICS_STRATEGY_ELEMENT:
    current_options = generate_user_demographics_options_func(state.brand_name, state.brand_link, state.brand_about)
  elif element == st.USER_LIKES_STRATEGY_ELEMENT:
    current_options = generate_user_likes_options_func(state.user_demographics)
  elif element == st.CONTENT_VIBE_STRATEGY_ELEMENT:
    current_options = generate_content_vibe_options_func()
  elif element == st.CONTENT_SPACES_STRATEGY_ELEMENT:
    current_options = generate_content_spaces_options_func()
  elif element == st.PERSONALITY_TONALITY_STRATEGY_ELEMENT:
    current_options = generate_personality_tonality_options_func()
  output_dict = {
    "current_options": current_options,
    "next": "select_option"
  }
  return output_dict

def select_option(state: VideoCreationState) -> dict:
  print(f"\nChoose an option for '{current_strategy(state)}':")
  current_element_index = state.current_brand_strategy_element_index
  for idx, opt in enumerate(state.current_options, 1):
    print(f"{idx}. {opt}")
  print("Type the number to select, or 'more' for new options.")
  user_input = input().strip()
  if user_input == "more":
    return {"next": "generate_options"}
  else:
    try:
      selection = int(user_input) - 1
      selected = state.current_options[selection]
      current_element_index += 1
      if current_element_index < len(state.brand_strategy_elements):
        return {
          current_strategy(state): selected,
          "current_brand_strategy_element_index": current_element_index,
          "next": "generate_options"
        }
      else:
        return {
          current_strategy(state): selected,
          "current_brand_strategy_element_index": current_element_index,
          "next": "generate_script_options"
        }
    except (ValueError, IndexError):
      print("Invalid input. Try again.")
      return {"next": "select_option"}


def generate_script_options(state: VideoCreationState) -> dict:
  brand_strategy = {
    "brand_name": state.brand_name,
    "brand_about": state.brand_about,
    "user_demographics": state.user_demographics,
    "user_likes": state.user_likes,
    "content_vibe": state.content_vibe,
    "content_spaces": state.content_spaces,
    "personality_tonality": state.personality_tonality
  }
  current_options = generate_script_options_func(brand_strategy)
  return {
    "current_options": current_options,
    "next": "select_script"
  }

def select_script(state: VideoCreationState) -> dict:
  print("\nChoose a script for your video:")
  for i, opt in enumerate(state.current_options, 1):
    print(f"{i}. {opt}")
  print("Type the number to select, or 'more' for new options.")
  user_input = input().strip()
  if user_input == "more":
    return {"next": "generate_script_options"}
  else:
    try:
      selection = int(user_input) - 1
      script_text = state.current_options[selection]
      # Parse script into scenes (simplified parsing)
      scenes = script_text.split(". ")
      script = [(scene.split(" (")[0], float(scene.split("(")[1].replace("s)", ""))) for scene in scenes if "(" in scene]
      return {
        "script": script,
        "next": st.IMAGES_STEP
      }
    except (ValueError, IndexError):
      print("Invalid input. Try again.")
      return {"next": "select_script"}

def generate_image(state: VideoCreationState) -> dict:
  scene_desc, _ = state.script[state.current_scene_index]
  image = generate_image_func(scene_desc)
  print(f"\nImage for scene {state.current_scene_index + 1}: {image}")
  approval = input("Approve this image? (yes/no): ").strip().lower()
  images = state.images
  current_scene_index = state.current_scene_index
  if approval == "yes":
    images.append(image)
    current_scene_index += 1
    if current_scene_index < len(state.script):
      return {"next": st.IMAGES_STEP, "images": images, "current_scene_index": current_scene_index}
    else:
      return {"next": st.VOICEOVER_STEP, "images": images, "current_scene_index": current_scene_index}
  else:
    return {"next": st.IMAGES_STEP}  # Regenerate if not approved

def generate_voiceover(state: VideoCreationState) -> dict:
  voiceover = generate_voiceover_func(state.script)
  print(f"\nVoiceover: {voiceover}")
  approval = input("Approve the voiceover? (yes/no): ").strip().lower()
  return {
    "video_with_voiceover": voiceover,
    "next": st.BACKGROUND_MUSIC_STEP if approval == "yes" else st.VOICEOVER_STEP
  }

def generate_music(state: VideoCreationState) -> dict:
  music = generate_music_func("background music matching the brand vibe")
  print(f"\nBackground music: {music}")
  approval = input("Approve the music? (yes/no): ").strip().lower()
  return {
    "background_music": music,
    "next": st.ANIMATION_STEP if approval == "yes" else st.BACKGROUND_MUSIC_STEP
  }

def create_animation(state: VideoCreationState) -> dict:
  durations = [scene[1] for scene in state.script]
  animation = create_animation_func(state.script, state.images, state.voiceover, state.background_music)
  print(f"\nAnimation created: {animation}")
  return {
    "animation": animation,
    "next": st.FINAL_VIDEO_STEP
  }

def end(state: VideoCreationState) -> dict:
  print(f"\nVideo creation complete! Your final video: {state.animation}")
  return {"final_video": state.animation, "next": None}  # End the process

def orchestrate_graph():
    # Build the state graph
    graph = StateGraph(VideoCreationState)
    node_ids = {
      st.INITIAL_INPUT_STEP: collect_initial_input,
      st.GENERATE_OPTIONS: generate_options,
      st.SELECT_OPTION: select_option,
      st.GENERATE_SCRIPT_OPTIONS: generate_script_options,
      st.SELECT_SCRIPT: select_script,
      st.IMAGES_STEP: generate_image,  # TODO(arjun): generate media/videos in next version
      # TODO(arjun): Storyboard creation in next version
      st.VOICEOVER_STEP: generate_voiceover,
      st.BACKGROUND_MUSIC_STEP: generate_music,
      st.ANIMATION_STEP: create_animation,
      st.FINAL_VIDEO_STEP: end
    }
    for node_id, node_func in node_ids.items():
      graph.add_node(node_id, node_func)

    # Define transitions
    graph.add_edge(st.INITIAL_INPUT_STEP, st.GENERATE_OPTIONS)
    graph.add_conditional_edges(
        st.GENERATE_OPTIONS,
        lambda state: state.next
    )
    graph.add_conditional_edges(
        st.SELECT_OPTION,
        lambda state: state.next
    )
    graph.add_conditional_edges(
        st.GENERATE_SCRIPT_OPTIONS,
        lambda state: state.next
    )
    graph.add_conditional_edges(
        st.SELECT_SCRIPT,
        lambda state: state.next
    )
    graph.add_conditional_edges(
        st.IMAGES_STEP,
        lambda state: state.next
    )
    graph.add_conditional_edges(
        st.VOICEOVER_STEP,
        lambda state: state.next
    )
    graph.add_conditional_edges(
        st.BACKGROUND_MUSIC_STEP,
        lambda state: state.next
    )
    graph.add_conditional_edges(
        st.ANIMATION_STEP,
        lambda state: state.next
    )

    # Set entry point
    graph.set_entry_point(st.INITIAL_INPUT_STEP)
    return graph

def run_agent():
    graph = orchestrate_graph()
    # Compile and run the graph
    app = graph.compile()
    # # Debug options
    # print(app.get_graph().draw_ascii())
    # app.debug = True
    app.invoke(VideoCreationState(brand_name=""))

if __name__ == "__main__":
    run_agent()