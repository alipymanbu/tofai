# agent.py
from langgraph.graph import StateGraph, START, END
from typing import List, Tuple, Optional
import state as st
from state import VideoCreationState
from lm_facade import LMFacade
from tasks.generate_brand_about import BrandAboutGenerator
from tasks.generate_user_demographics import UserDemographicsGenerator
from tasks.generate_user_likes import UserLikesGenerator
from tasks.generate_content_vibe import ContentVibeGenerator
from tasks.generate_content_spaces import ContentSpacesGenerator
from tasks.generate_personality import PersonalityGenerator
from tasks.generate_script import ScriptGenerator
from tasks.generate_image import ImageGenerator

_LM_FACADE = LMFacade()

def current_strategy(state: VideoCreationState) -> str:
    return state.brand_strategy_elements[state.current_brand_strategy_element_index]

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
  return output_dict

def generate_options(state: VideoCreationState) -> dict:
  element = current_strategy(state)
  if element == st.BRAND_ABOUT_STRATEGY_ELEMENT:
    current_options = BrandAboutGenerator(_LM_FACADE).generate({"Brand": state.brand_name, "Link": state.brand_link})
  elif element == st.USER_DEMOGRAPHICS_STRATEGY_ELEMENT:
    current_options = UserDemographicsGenerator(_LM_FACADE).generate({"Brand": state.brand_name, "Link": state.brand_link, "About": state.brand_about})
  elif element == st.USER_LIKES_STRATEGY_ELEMENT:
    current_options = UserLikesGenerator(_LM_FACADE).generate({"Brand": state.brand_name, "Link": state.brand_link, "About": state.brand_about, "User Demographics": state.user_demographics})
  elif element == st.CONTENT_VIBE_STRATEGY_ELEMENT:
    current_options = ContentVibeGenerator(_LM_FACADE).generate({"Brand": state.brand_name, "About": state.brand_about, "User Demographics": state.user_demographics, "User Likes": state.user_likes})
  elif element == st.CONTENT_SPACES_STRATEGY_ELEMENT:
    current_options = ContentSpacesGenerator(_LM_FACADE).generate({"Brand": state.brand_name, "About": state.brand_about, "User Demographics": state.user_demographics, "User Likes": state.user_likes, "Content Vibe": state.content_vibe})
  elif element == st.PERSONALITY_TONALITY_STRATEGY_ELEMENT:
    current_options = PersonalityGenerator(_LM_FACADE).generate({"Brand": state.brand_name, "About": state.brand_about, "User Demographics": state.user_demographics, "User Likes": state.user_likes, "Content Vibe": state.content_vibe, "Content Spaces": state.content_spaces})
  output_dict = {
    "current_options": current_options,
    "next": "select_option"
  }
  return output_dict

def select_option(state: VideoCreationState) -> dict:
  print(f"\nChoose an option for '{current_strategy(state)}':")
  current_element_index = state.current_brand_strategy_element_index
  for idx, opt in enumerate(state.current_options, 1):
    print(f"{opt}")
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
    except (ValueError, IndexError) as e:
      print("Invalid input. Try again." + str(e))
      return {"next": "select_option"}


def generate_script_options(state: VideoCreationState) -> dict:
  brand_strategy = {
    "Brand": state.brand_name,
    "About": state.brand_about,
    "User Demographics": state.user_demographics,
    "User Likes": state.user_likes,
    "Content Vibe": state.content_vibe,
    "Content Spaces": state.content_spaces,
    "Personality and Tonality": state.personality_tonality
  }
  current_options = ScriptGenerator(_LM_FACADE).generate(brand_strategy)
  return {
    "current_options": current_options,
    "next": "select_script"
  }

def select_script(state: VideoCreationState) -> dict:
  print("\nChoose a script for your video:")
  for i, opt in enumerate(state.current_options, 1):
    print(f"{opt}")
  print("Type the number to select, or 'more' for new options.")
  user_input = input().strip()
  if user_input == "more":
    return {"next": "generate_script_options"}
  else:
    try:
      selection = int(user_input) - 1
      script_text = state.current_options[selection]
      return {
        "script": script_text,
        "next": st.IMAGES_STEP
      }
    except (ValueError, IndexError):
      print("Invalid input. Try again.")
      return {"next": "select_script"}

def generate_image(state: VideoCreationState) -> dict:
  scene_desc = state.script[state.current_scene_index]
  brand_strategy = {
    "Brand": state.brand_name,
    "About": state.brand_about,
    "User Demographics": state.user_demographics,
    "User Likes": state.user_likes,
    "Content Vibe": state.content_vibe,
    "Content Spaces": state.content_spaces,
    "Personality and Tonality": state.personality_tonality,
    "Script": state.script
  }
  images = ImageGenerator(_LM_FACADE).generate(brand_strategy, multimodel=True)
  print(images)
  approval = input("Approve these images? (yes/no): ").strip().lower()
  if approval == "yes":
    return {"next": st.VOICEOVER_STEP, "images": images.split("||")}
  else:
    return {"next": st.IMAGES_STEP}

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
    # _LM_FACADE.invoke_t2i("Generate 2 images: 1. ocean waves 2. mountain landscape.")

if __name__ == "__main__":
    run_agent()