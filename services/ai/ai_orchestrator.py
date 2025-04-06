"""
AI Orchestrator for brand awareness video creation.
This module orchestrates the AI workflow using LangGraph and the config-driven framework.
"""
from langgraph.graph import StateGraph
from typing import Any, Dict, List, Tuple, Optional, Union
import asyncio
from datetime import datetime
import logging
import json

from services.ai.framework_model import FrameworkStep, FrameworkResult, ResultOptions
import services.ai.state as st
from services.ai.state import VideoCreationState
from services.ai.lm_facade import LMFacade
from services.storage.database import get_db
from services.ai.tasks.generator import Generator

logger = logging.getLogger(__name__)

class AIOrchestrator:
  """
  AI Orchestrator for brand awareness video creation using a config-driven framework.
  """

  def __init__(self, framework_id: str = "brand_awareness_video", lm_facade: Union[LMFacade, None] = None):
    """
    Initialize the AI orchestrator.
    
    Args:
        framework_id: The ID of the framework to use
    """
    self.framework_id = framework_id
    self.lm_facade = lm_facade or LMFacade()
    self.generator = Generator(framework_id, self.lm_facade)
    self.graph = self._orchestrate_graph()

  async def run(self, session_id: str, current_step_id: str = None) -> Dict[str, Any]:
    """
    Run the AI orchestration flow with MongoDB and Redis integration.
    Args:
        session_id: The session ID
        current_step_id: Optional current step to start from
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
            framework_id=self.framework_id,
            current_step_id=current_step_id or self.generator.framework.initial_step
        )
        
        # Add existing framework result if available
        if "framework_result" in session and session["framework_result"]:
            # Convert from dict to FrameworkResult
            try:
                initial_state.framework_result = FrameworkResult.model_validate(session["framework_result"])
            except Exception as e:
                logger.error(f"Error loading framework result: {e}")

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
                    "result": result.to_dict()
                }
            }
        )
        
        # Update session with results
        session_update = result.to_dict()
        session_update["updated_at"] = datetime.utcnow()
        
        # Update the session
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": session_update}
        )
        
        return {
            "success": True,
            "result": result.to_dict(),
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
            graph.add_conditional_edges(
                step.id,
                step.next_step
            )
        graph.set_entry_point(initial_step_id)
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
    step_result = state.get_step_result(state.current_step_id)
    next_step = self.generator.get_step_by_id(state.current_step_id).next_step
    if step_result:
        return {"current_step_id": next_step}
    print("Let's create a stunning brand awareness video!")
    brand_link = input("Got a link to your brand's website or online presence? ")
    result_options = ResultOptions()
    result_options.result_options = [brand_link]
    result_options.selected_option = 0
    framework_result = state.set_step_result(step_id=state.current_step_id, result_options=result_options)
    return {"framework_result": framework_result, "current_step_id": next_step}

  def _get_latest_param_values(self, step: FrameworkStep, state:VideoCreationState):
    params = set()
    for prompt in step.prompts:
        params.add(prompt.parameters)
    return state.get_param_values(params=params, framework_steps=self.generator.framework.steps)

  def _generate_options(self, state: VideoCreationState) -> dict[str, Union[str, FrameworkResult]]:
    """
    Generate options for the current step.
    
    Args:
        state: The current state
        
    Returns:
        VideoCreationState: The updated state
    """
    next_step = self.generator.get_step_by_id(state.current_step_id).next_step
    try:
        # Get the current step configuration
        step = self.generator.get_step_by_id(state.current_step_id)
        param_values = self._get_latest_param_values(step=step, state=state)
        # Generate options
        results = self.generator.generate_options(state.current_step_id, param_values)
        framework_result = None
        for result in results:
            options = ResultOptions()
            options.result_options = result
            framework_result = state.set_step_result(state.current_step_id, result_options=options, intermediate_framework_result=framework_result)
    except Exception as e:
        state.error = str(e)
        logger.error(f"Error generating options: {e}")
    return {"current_step_id": next_step, "framework_result": framework_result}

  def _select_option(self, state: VideoCreationState) -> dict[str, Union[str, FrameworkResult]]:
    """
    Handle user selection of an option.
    
    Args:
        state: The current state
        
    Returns:
        VideoCreationState: The updated state
    """
    next_step = self.generator.get_step_by_id(state.current_step_id).next_step
    try:
      print(f"\nChoose an option for '{state.current_step_id}':")
      step_result = state.get_step_result(step_id=state.current_step_id, framework_result=state.framework_result)
      for idx, opt in enumerate(state.get_options_for_result(step_result=step_result, result_index=0), 1):
          print(f"{idx}. {opt}")
      
      print("Type the number to select.")
      user_input = input().strip()
      framework_result = state.set_step_result_option_selection(step_id=state.current_step_id, result_index=0, selected_option=user_input)
      return {"current_step_id": next_step, "framework_result": framework_result}
    except Exception as e:
      logger.error(f"Error in select_option: {e}. Retrying.")
      # Stay on current step in case of error
      return {"current_step_id": state.current_step_id}