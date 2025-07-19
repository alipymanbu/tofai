from pydantic import BaseModel, Field
from typing import List, Tuple, Optional, Union, Dict, Any, Set
from services.ai.framework_model import FrameworkResult, FrameworkStepResult, ResultOptions, FrameworkStep, MediaUri
from services.ai.tasks.generator import generate_context_id

# ======== Define constants ========

# Node keys
INITIAL_INPUT_STEP = "initial_input"
USER_PERSONA_STEP = "user_persona"
SELECT_USER_PERSONA_STEP = "select_user_persona"
CONTENT_SPACES_STEP = "content_spaces"
SELECT_CONTENT_SPACES_STEP = "select_content_spaces"
PERSONALITY_TONALITY_STEP = "personality_tonality"
SELECT_PERSONALITY_TONALITY_STEP = "select_personality_tonality"
SCRIPT_STEP = "script"
SELECT_SCRIPT_STEP = "select_script"
IMAGES_STEP = "images"
VOICEOVER_STEP = "voiceover"
BACKGROUND_MUSIC_STEP = "background_music"
ANIMATION_STEP = "animation"
FINAL_VIDEO_STEP = "final_video"

# Generation and selection steps
GENERATE_OPTIONS = "generate_options"
SELECT_OPTION = "select_option"

# ======== Define state class ========
class VideoCreationState(BaseModel):
    """Represents the state of the video creation process in a config-driven approach."""
    
    # Session and Framework info
    session_id: str  # Session ID
    framework_id: str = "brand_awareness_video"  # Framework ID
    current_step_id: Optional[str] = None  # Current step ID   
    # Framework results
    framework_result: Optional[FrameworkResult] = None
    error: Optional[str] = None

    def initialize_framework_result(self) -> None:
        """Initialize the framework result structure if it doesn't exist yet."""
        if self.framework_result is None:
            self.framework_result = FrameworkResult(
                id=self.framework_id,
                step_results=[]
            )

    def get_step_result(self, step_id: str, framework_result: FrameworkResult) -> Optional[FrameworkStepResult]:
        """Gets the step result given the step Id. Returns None if no result for the step yet, or invalid step Id.
        Args:
            step_id (str): Id of the framework step.
        """
        for step_result in framework_result.step_results:
            if step_result.id == step_id:
                return step_result

    def get_options_for_result(self, step_result: FrameworkStepResult, result_index: int) -> List[Union[str, bytes]]:
        if result_index < 0 or result_index >= len(step_result.result):
            return []
        return step_result.result[result_index].result_options
    
    def get_user_selection_for_step(self, step_result: FrameworkStepResult, result_index: int, expected_selection_count: Union[int, str]) -> Optional[List[Union[str, MediaUri]]]:
        # print(f"get_user_selection_for_step: {step_result.id} {result_index} {step_result}")
        if result_index < 0 or result_index >= len(step_result.result):
            return None
        result_options = step_result.result[result_index]
        if isinstance(expected_selection_count, str) and expected_selection_count == "ALL":
            # If the expected selection count is "ALL", return all options
            return result_options.result_options
        # print(f"result_options: {result_options.selected_option} {len(result_options.result_options)}")
        if result_options.selected_option < 0 or result_options.selected_option >= len(result_options.result_options):
            return None
        # print(f"result_options: {result_options.result_options[result_options.selected_option]}")
        return [result_options.result_options[result_options.selected_option]]
    
    def set_step_result(self, step_id: str, result_options: ResultOptions, intermediate_framework_result: FrameworkResult = None, display_to_user: bool = True) -> FrameworkResult:
        framework_result = intermediate_framework_result or self.framework_result.model_copy()
        step_result = self.get_step_result(step_id=step_id, framework_result=framework_result)
        if not step_result:
            step_result = FrameworkStepResult(id=step_id, result=[])
            framework_result.step_results.append(step_result)
        step_result.result.append(result_options)
        step_result.display_to_user = display_to_user
        return framework_result
    
    def flatten_step_result(self, step_result: FrameworkStepResult, intermediate_framework_result: FrameworkResult = None) -> List[ResultOptions]:
        """Flatten the step result which have selected_option == 'ALL'"""
        flattened_result = []
        for result in step_result.result:
            if result.selected_option == "ALL":
                for option in result.result_options:
                    option = ResultOptions(result_options=[option], context_ids=[generate_context_id(option)], selected_option=0)
                    flattened_result.append(option)
            else:
                flattened_result.append(result.result_options)
        framework_result = intermediate_framework_result or self.framework_result.model_copy()
        step_result = self.get_step_result(step_id=step_result.id, framework_result=framework_result)
        step_result.result = flattened_result
        return framework_result
    
    def set_step_result_option_selection(self, step_id: str, result_index: int, selected_option: int, intermediate_framework_result: FrameworkResult = None) -> FrameworkResult:
        if result_index < 0 or selected_option < 0:
            return
        framework_result = intermediate_framework_result or self.framework_result.model_copy()
        step_result = self.get_step_result(step_id=step_id, framework_result=framework_result)
        if step_result and result_index < len(step_result.result):
            step_result.result[result_index].selected_option = selected_option
        return framework_result

    def get_param_values(self, params: Set[str], framework_steps: List[FrameworkStep]) -> dict[str, Union[str, List[str]]]:
        result = {}
        step_id_name = {}
        expected_user_selected_count = {}
        for step in framework_steps:
            if step.name in params:
                step_id_name[step.id] = step.name
                expected_user_selected_count[step.id] = step.expected_selection_count
        # print(f"step_id_name: {step_id_name}")
        # print(f"framework_result: {self.framework_result}")
        for step_result in self.framework_result.step_results:
            if step_result.id in step_id_name:
                # print(f"step_result.id found: {step_result.id}")
                result_values = []
                for result_index in range(len(step_result.result)):
                    user_selection_for_step = self.get_user_selection_for_step(step_result, result_index, expected_user_selected_count[step_result.id])
                    for user_selection in user_selection_for_step:
                        if isinstance(user_selection, MediaUri):
                            result_values.append(user_selection.uri)
                        else:
                            result_values.append(user_selection)
                # print(f"result length: {len(result_values)}")
                if result_values:
                    result[step_id_name[step_result.id]] = result_values[0] if len(result_values) == 1 else result_values
        # print(f"get_param_values: {result}")
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a dictionary for database storage."""
        result = {
            "session_id": self.session_id,
            "framework_id": self.framework_id,
            "current_step_id": self.current_step_id,
            "error": self.error,
        }
        # Add framework result data
        if self.framework_result:
            result["framework_result"] = self.framework_result.model_dump()
        
        return result