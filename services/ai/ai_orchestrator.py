"""
AI Orchestrator for brand awareness video creation.
This module orchestrates the AI workflow using LangGraph and the config-driven framework.

NO_AI_CODE=True
"""
from langgraph.graph import StateGraph, END
from typing import Any, Dict, List, Tuple, Optional, Union
import asyncio
from datetime import datetime
import logging
import json

from api.models import Session
from services.ai.framework_model import FrameworkStep, FrameworkResult, ResultOptions
import services.ai.state as st
from services.ai.state import VideoCreationState
from services.ai.lm_facade import LMFacade
from services.ai.tasks.generator import Generator

logger = logging.getLogger(__name__)

class AIOrchestrator:
  """
  AI Orchestrator for brand awareness video creation using a config-driven framework.
  """

  def __init__(self, framework_id: str = "brand_awareness_video", lm_facade: Union[LMFacade, None] = None, is_local_test: bool = False):
    """
    Initialize the AI orchestrator.
    
    Args:
        framework_id: The ID of the framework to use
    """
    self.framework_id = framework_id
    self.lm_facade = lm_facade or LMFacade()
    self.generator = Generator(framework_id, self.lm_facade)
    self.graph = self._orchestrate_graph()
    self.is_local_test = is_local_test

  async def run(self, session: Session, current_step_id: str = None) -> Dict[str, Any]:
    """
    Run the AI orchestration flow with MongoDB and Redis integration.
    Args:
        session: The session of current conversation
        current_step_id: Optional current step to start from
    Returns:
        Result dictionary
    """
    try:
        # Initialize state with data from the session
        initial_state = VideoCreationState(
            session_id=session.id,
            framework_id=self.framework_id,
            current_step_id=self.generator.framework.initial_step
        )
        
        # Add existing framework result if available
        if session.result:
            # Convert from dict to FrameworkResult
            try:
                initial_state.framework_result = session.result
            except Exception as e:
                logger.error(f"Error loading framework result: {e}")

        # Run the graph
        app = self.graph.compile()
        # config = {"recursion_limit": 5}
        result = await app.ainvoke(initial_state)
        return result
    except Exception as e:
        logger.exception(f"Error in AI orchestration: {str(e)}")
        return None

  def _orchestrate_graph(self) -> StateGraph:
    """
    Build the state graph dynamically based on the framework configuration.
    
    Returns:
        StateGraph: The orchestration graph
    """
    # Build the state graph
    graph = StateGraph(VideoCreationState)
    # Get all steps from the framework
    steps = []
    initial_step_id = None

    # Callable to get the next node or end.
    def next_node_or_end(state: VideoCreationState) -> str:
        print(f"next_node_or_end: {state.current_step_id}")
        if state.current_step_id:
           return state.current_step_id
        return END

    try:
        # Get the framework
        framework = self.generator.framework
        steps = framework.steps
        initial_step_id = framework.initial_step
        # Add nodes for each step
        for step in steps:
            # Determine the appropriate handler for this step
            handler = None
            if step.id == self.generator.framework.initial_step:
                handler = self._initial_input
            elif step.requires_user_input:
                handler = self._select_option
            else:
                handler = self._generate_options
            graph.add_node(step.id, handler)
        # Add conditional edges for each node
        for step in steps:
            graph.add_conditional_edges(step.id, next_node_or_end)
        graph.set_entry_point(initial_step_id)
        graph.set_finish_point(framework.final_step)
    except Exception as e:
        raise ValueError(f"Error building graph from framework: {e}")
    return graph

  def _initial_input(self, state: VideoCreationState) -> dict[str, Union[str, FrameworkResult]]:
    """
    Handle initial input step.
    
    Args:
        state: The current state
        
    Returns:
        VideoCreationState: The updated state
    """
    # Check if we already have brand info
    step_result = state.get_step_result(step_id=state.current_step_id, framework_result=state.framework_result)
    next_step = self.generator.get_step_by_id(state.current_step_id).next_step
    if step_result:
        return {"current_step_id": next_step}
    if not self.is_local_test:
        return {"current_step_id": END}
    print("Let's create a stunning brand awareness video!")
    brand_link = input("Got a link to your brand's website or online presence? ")
    result_options = ResultOptions(result_options=[brand_link], selected_option=0)
    framework_result = state.set_step_result(step_id=state.current_step_id, result_options=result_options)
    return {"framework_result": framework_result, "current_step_id": next_step}

  def _get_latest_param_values(self, step: FrameworkStep, state:VideoCreationState) -> dict[str, Union[str, List[str]]]:
    params = set()
    for prompt in step.prompts:
        params = params.union(set(prompt.parameters))
    for agent in step.agents:
        params = params.union(set(agent.parameters))
    print(f"params: {params}")
    return state.get_param_values(params=params, framework_steps=self.generator.framework.steps)

  def _generate_options(self, state: VideoCreationState) -> dict[str, Union[str, FrameworkResult]]:
    """
    Generate options for the current step.
    
    Args:
        state: The current state
        
    Returns:
        VideoCreationState: The updated state
    """
    step_result = state.get_step_result(step_id=state.current_step_id, framework_result=state.framework_result)
    next_step = self.generator.get_step_by_id(state.current_step_id).next_step
    if step_result:
        return {"current_step_id": next_step}
    try:
        # Get the current step configuration
        step = self.generator.get_step_by_id(state.current_step_id)
        param_values = self._get_latest_param_values(step=step, state=state)
        # Generate options
        results = self.generator.generate_options(state.current_step_id, param_values, session_id=state.session_id)
        framework_result = None
        for result in results:
            options = ResultOptions(result_options=result)
            if len(result) == 1:
                options.selected_option = 0  # Select the first option by default, if only one is available.
            framework_result = state.set_step_result(state.current_step_id, result_options=options, intermediate_framework_result=framework_result)
        return {"current_step_id": next_step, "framework_result": framework_result}
    except Exception as e:
        state.error = str(e)
        logger.error(f"Error generating options: {e}")
        return {"current_step_id": state.current_step_id}

  def _select_option(self, state: VideoCreationState) -> dict[str, Union[str, FrameworkResult]]:
    """
    Handle user selection of an option.
    
    Args:
        state: The current state
        
    Returns:
        VideoCreationState: The updated state
    """
    selection_for = self.generator.get_selection_for_step_id(step_id=state.current_step_id)
    selection_step_result = state.get_step_result(step_id=selection_for, framework_result=state.framework_result)
    next_step = self.generator.get_step_by_id(state.current_step_id).next_step
    # print(f"next_step: {next_step} selection_step_result: {selection_step_result}")
    if selection_step_result and all([opt.selected_option >= 0 for opt in selection_step_result.result]):
        return {"current_step_id": next_step}
    if not self.is_local_test:
        return {"current_step_id": END}
    try:
      print(f"\nChoose an option for '{state.current_step_id}':")
      step_result = state.get_step_result(step_id=selection_for, framework_result=state.framework_result)
      for idx, opt in enumerate(state.get_options_for_result(step_result=step_result, result_index=0), 1):
          print(f"{idx}. {opt}")
      
      print("Type the number to select.")
      user_input = int(input().strip())
      framework_result = state.set_step_result_option_selection(step_id=state.current_step_id, result_index=0, selected_option=user_input)
      return {"current_step_id": next_step, "framework_result": framework_result}
    except Exception as e:
      logger.error(f"Error in select_option: {e}. Retrying.")
      return {"current_step_id": state.current_step_id}