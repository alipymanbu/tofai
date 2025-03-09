# agent.py
from langgraph.graph import StateGraph, START, END
from typing import List, Tuple, Optional
import state as st
from state import VideoCreationState

# Define the state class to hold all data throughout the process
# class VideoCreationState(BaseModel):
#     brand_name: Optional[str] = None
#     brand_link: Optional[str] = None
#     brand_about: Optional[str] = None
#     user_demographics: Optional[str] = None
#     user_likes: Optional[str] = None
#     content_vibe: Optional[str] = None
#     content_spaces: Optional[str] = None  # Selected story headline
#     personality_tonality: Optional[str] = None
#     script: Optional[List[Tuple[str, float]]] = None  # List of (scene description, duration in seconds)
#     images: List[str] = []  # Approved images for each scene
#     animation: Optional[str] = None
#     video_with_voiceover: Optional[str] = None
#     final_video: Optional[str] = None
#     current_element: Optional[str] = None
#     current_options: List[str] = []
#     current_scene_index: int = 0
#     brand_strategy_elements: List[str] = [
#         "brand_about",
#         "user_demographics",
#         "user_likes",
#         "content_vibe",
#         "content_spaces",
#         "personality_tonality"
#     ]
#     current_element_index: int = 0
#     next: Optional[str] = None  # For conditional transitions

def current_strategy(state: VideoCreationState) -> str:
    return state.brand_strategy_elements[state.current_brand_strategy_element_index]

# Placeholder generation functions (replace with actual LLM/media API calls)
def generate_brand_about_options_func(brand_name: str, brand_link: str) -> List[str]:
    return [
        f"{brand_name} is a leader in sustainable fashion.",
        f"{brand_name} crafts innovative tech solutions.",
        f"{brand_name} delivers premium coffee experiences."
    ]

def generate_user_demographics_options_func(brand_about: str) -> List[str]:
    return [
        "Young urban professionals, 25-35, eco-conscious, in North America.",
        "Tech-savvy teens, 13-19, global, love gaming.",
        "Coffee enthusiasts, 30-50, middle-income, in Europe."
    ]

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
    current_options = generate_user_demographics_options_func(state.brand_about)
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