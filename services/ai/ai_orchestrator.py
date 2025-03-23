from langgraph.graph import StateGraph, START, END
from typing import Any, Dict, List, Tuple, Optional
import asyncio
from datetime import datetime
import logging

import services.ai.state as st
from services.ai.state import VideoCreationState
from services.ai.lm_facade import LMFacade
from services.storage.database import get_db

logger = logging.getLogger(__name__)

# Import task generators
from services.ai.tasks.generate_brand_about import BrandAboutGenerator
from services.ai.tasks.generate_user_demographics import UserDemographicsGenerator
from services.ai.tasks.generate_user_likes import UserLikesGenerator
from services.ai.tasks.generate_content_vibe import ContentVibeGenerator
from services.ai.tasks.generate_content_spaces import ContentSpacesGenerator
from services.ai.tasks.generate_personality import PersonalityGenerator
from services.ai.tasks.generate_script import ScriptGenerator
from services.ai.tasks.generate_image import ImageGenerator

# ====== Mock functions for generating media START ======
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
# ====== Mock functions for generating media END ======

class AIOrchestrator:
    def __init__(self):
        self.graph = self._orchestrate_graph()
        self.lm_facade = LMFacade()

    async def run(self, session_id: str, current_step: str = None) -> Dict[str, Any]:
        """
        Run the AI orchestration flow with MongoDB and Redis integration.
        
        Args:
            session_id: The session ID
            current_step: Optional current step to start from
            
        Returns:
            Result dictionary
        """
        try:
            # Get database connection
            db = await get_db()
            
            # Get session data from database
            session = await db.sessions.find_one({"id": session_id})
            if not session:
                logger.error(f"Session {session_id} not found")
                return {
                    "success": False,
                    "result": None,
                    "error": f"Session {session_id} not found"
                }
            
            # Create job record
            job_id = f"ai-flow-{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            await db.jobs.insert_one({
                "id": job_id,
                "session_id": session_id,
                "type": "ai_flow",
                "status": "processing",
                "progress": 0,
                "created_at": datetime.utcnow()
            })
            
            # Initialize state with data from the session
            initial_state = VideoCreationState(
                session_id=session_id,
                brand_name=session.get("brand_framework", {}).get("brand_name", ""),
                brand_link=session.get("brand_framework", {}).get("brand_link", ""),
                next=st.INITIAL_INPUT_STEP if not current_step else current_step
            )
            
            # Copy any existing data from the session to the state
            if "brand_about" in session:
                initial_state.brand_about = session["brand_about"]
            if "user_demographics" in session:
                initial_state.user_demographics = session["user_demographics"]
            if "user_likes" in session:
                initial_state.user_likes = session["user_likes"]
            if "content_vibe" in session:
                initial_state.content_vibe = session["content_vibe"]
            if "content_spaces" in session:
                initial_state.content_spaces = session["content_spaces"]
            if "personality_tonality" in session:
                initial_state.personality_tonality = session["personality_tonality"]
            if "script" in session:
                initial_state.script = session["script"]

            # Run the graph
            app = self.graph.compile()
            result = await app.ainvoke(initial_state)
            
            # Update job status
            await db.jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": "completed",
                        "progress": 100,
                        "completed_at": datetime.utcnow(),
                        "result": result
                    }
                }
            )
            
            # Update session with results and compose strategy
            strategy_update = {}
            
            # Only update fields that have values from the result
            if result.get("brand_about"):
                strategy_update["brand_about"] = result.get("brand_about")
            
            if result.get("user_demographics"):
                strategy_update["user_demographics"] = result.get("user_demographics")
            
            if result.get("user_likes"):
                strategy_update["user_likes"] = result.get("user_likes")
            
            if result.get("content_vibe"):
                strategy_update["content_vibe"] = result.get("content_vibe")
            
            if result.get("content_spaces"):
                strategy_update["content_spaces"] = result.get("content_spaces")
            
            if result.get("personality_tonality"):
                strategy_update["personality_tonality"] = result.get("personality_tonality")
            
            if result.get("script"):
                strategy_update["script"] = result.get("script")
            
            # Only compose a strategy if we have the components
            if "content_vibe" in strategy_update and "content_spaces" in strategy_update and "personality_tonality" in strategy_update:
                content_vibe = strategy_update["content_vibe"]
                content_spaces = strategy_update["content_spaces"]
                personality_tonality = strategy_update["personality_tonality"]
                
                strategy_update["strategy"] = {
                    "content_theme": content_vibe.split('\n')[0] if '\n' in content_vibe else content_vibe,
                    "key_messages": content_spaces.split('||') if '||' in content_spaces else [content_spaces],
                    "recommended_length": "30 seconds",
                    "call_to_action": "Contact us today" if not personality_tonality else personality_tonality.split('\n')[-1] if '\n' in personality_tonality else personality_tonality
                }
            
            strategy_update["updated_at"] = datetime.utcnow()
            if result.get("next"):
                strategy_update["current_step"] = result.get("next")
            
            # Update the session
            await db.sessions.update_one(
                {"id": session_id},
                {"$set": strategy_update}
            )
            
            return {
                "success": True,
                "result": result,
                "error": None
            }
        except Exception as e:
            logger.exception(f"Error in AI orchestration: {str(e)}")
            
            # Update job status if it exists
            if 'job_id' in locals():
                try:
                    await db.jobs.update_one(
                        {"id": job_id},
                        {
                            "$set": {
                                "status": "failed",
                                "progress": 100,
                                "completed_at": datetime.utcnow(),
                                "error": str(e)
                            }
                        }
                    )
                except Exception as update_error:
                    logger.error(f"Failed to update job status: {str(update_error)}")
            
            return {
                "success": False,
                "result": None,
                "error": str(e)
            }

    def _orchestrate_graph(self) -> StateGraph:
        # Build the state graph
        graph = StateGraph(VideoCreationState)
        node_ids = {
            st.INITIAL_INPUT_STEP: self._collect_initial_input,
            st.GENERATE_OPTIONS: self._generate_options,
            st.SELECT_OPTION: self._select_option,
            st.GENERATE_SCRIPT_OPTIONS: self._generate_script_options,
            st.SELECT_SCRIPT: self._select_script,
            st.IMAGES_STEP: self._generate_image,
            st.VOICEOVER_STEP: self._generate_voiceover,
            st.BACKGROUND_MUSIC_STEP: self._generate_music,
            st.ANIMATION_STEP: self._create_animation,
            st.FINAL_VIDEO_STEP: self._end
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

    # The following methods are preserved from the original implementation
    def _collect_initial_input(self, state: VideoCreationState) -> dict:
        # In MongoDB integration, this data would come from the session
        if state.brand_name and state.brand_link:
            # If we already have brand info from the session, skip the input
            return {
                "brand_name": state.brand_name,
                "brand_link": state.brand_link,
                "current_brand_strategy_element_index": 0,
                "next": st.GENERATE_OPTIONS
            }
        
        # Otherwise, prompt the user (interactive mode)
        print("Let's create a stunning brand awareness video!")
        brand_name = input("What's your brand called? ")
        brand_link = input("Got a link to your brand's website or online presence? ")
        output_dict = {
          "brand_name": brand_name,
          "brand_link": brand_link,
          "current_brand_strategy_element_index": 0,
          "next": st.GENERATE_OPTIONS
        }
        return output_dict

    def _generate_options(self, state: VideoCreationState) -> dict:
        element = self._current_strategy(state)
        if element == st.BRAND_ABOUT_STRATEGY_ELEMENT:
          current_options = BrandAboutGenerator(self.lm_facade).generate({"Brand": state.brand_name, "Link": state.brand_link})
        elif element == st.USER_DEMOGRAPHICS_STRATEGY_ELEMENT:
          current_options = UserDemographicsGenerator(self.lm_facade).generate({"Brand": state.brand_name, "Link": state.brand_link, "About": state.brand_about})
        elif element == st.USER_LIKES_STRATEGY_ELEMENT:
          current_options = UserLikesGenerator(self.lm_facade).generate({"Brand": state.brand_name, "Link": state.brand_link, "About": state.brand_about, "User Demographics": state.user_demographics})
        elif element == st.CONTENT_VIBE_STRATEGY_ELEMENT:
          current_options = ContentVibeGenerator(self.lm_facade).generate({"Brand": state.brand_name, "About": state.brand_about, "User Demographics": state.user_demographics, "User Likes": state.user_likes})
        elif element == st.CONTENT_SPACES_STRATEGY_ELEMENT:
          current_options = ContentSpacesGenerator(self.lm_facade).generate({"Brand": state.brand_name, "About": state.brand_about, "User Demographics": state.user_demographics, "User Likes": state.user_likes, "Content Vibe": state.content_vibe})
        elif element == st.PERSONALITY_TONALITY_STRATEGY_ELEMENT:
          current_options = PersonalityGenerator(self.lm_facade).generate({"Brand": state.brand_name, "About": state.brand_about, "User Demographics": state.user_demographics, "User Likes": state.user_likes, "Content Vibe": state.content_vibe, "Content Spaces": state.content_spaces})
        output_dict = {
          "current_options": current_options,
          "next": st.SELECT_OPTION
        }
        return output_dict

    def _select_option(self, state: VideoCreationState) -> dict:
        # In automated mode with MongoDB, we could automatically select an option
        # For now, preserving the interactive mode
        print(f"\nChoose an option for '{self._current_strategy(state)}':")
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
                self._current_strategy(state): selected,
                "current_brand_strategy_element_index": current_element_index,
                "next": st.GENERATE_OPTIONS
              }
            else:
              return {
                self._current_strategy(state): selected,
                "current_brand_strategy_element_index": current_element_index,
                "next": st.GENERATE_SCRIPT_OPTIONS
              }
          except (ValueError, IndexError) as e:
            print("Invalid input. Try again." + str(e))
            return {"next": st.SELECT_OPTION}

    def _generate_script_options(self, state: VideoCreationState) -> dict:
        brand_strategy = {
          "Brand": state.brand_name,
          "About": state.brand_about,
          "User Demographics": state.user_demographics,
          "User Likes": state.user_likes,
          "Content Vibe": state.content_vibe,
          "Content Spaces": state.content_spaces,
          "Personality and Tonality": state.personality_tonality
        }
        current_options = ScriptGenerator(self.lm_facade).generate(brand_strategy)
        return {
          "current_options": current_options,
          "next": "select_script"
        }

    def _select_script(self, state: VideoCreationState) -> dict:
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
            return {"next": st.SELECT_SCRIPT}

    def _generate_image(self, state: VideoCreationState) -> dict:
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
        images = ImageGenerator(self.lm_facade).generate(brand_strategy, multimodel=True)
        print(images)
        approval = input("Approve these images? (yes/no): ").strip().lower()
        if approval == "yes":
          return {"next": st.VOICEOVER_STEP, "images": images.split("||")}
        else:
          return {"next": st.IMAGES_STEP}

    def _generate_voiceover(self, state: VideoCreationState) -> dict:
        voiceover = generate_voiceover_func(state.script)
        print(f"\nVoiceover: {voiceover}")
        approval = input("Approve the voiceover? (yes/no): ").strip().lower()
        return {
          "video_with_voiceover": voiceover,
          "next": st.BACKGROUND_MUSIC_STEP if approval == "yes" else st.VOICEOVER_STEP
        }

    def _generate_music(self, state: VideoCreationState) -> dict:
        music = generate_music_func("background music matching the brand vibe")
        print(f"\nBackground music: {music}")
        approval = input("Approve the music? (yes/no): ").strip().lower()
        return {
          "background_music": music,
          "next": st.ANIMATION_STEP if approval == "yes" else st.BACKGROUND_MUSIC_STEP
        }

    def _create_animation(self, state: VideoCreationState) -> dict:
        durations = [scene[1] for scene in state.script]
        animation = create_animation_func(state.script, state.images, state.voiceover, state.background_music)
        print(f"\nAnimation created: {animation}")
        return {
          "animation": animation,
          "next": st.FINAL_VIDEO_STEP
        }

    def _end(self, state: VideoCreationState) -> dict:
        print(f"\nVideo creation complete! Your final video: {state.animation}")
        return {"final_video": state.animation, "next": None}  # End the process

    def _current_strategy(self, state: VideoCreationState) -> str:
        return state.brand_strategy_elements[state.current_brand_strategy_element_index]
