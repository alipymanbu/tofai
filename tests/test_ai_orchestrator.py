"""
Tests for the AI orchestrator.

NO_AI_CODE=True
"""
import pytest
from unittest.mock import MagicMock, patch
import uuid
import datetime

from services.ai.ai_orchestrator import AIOrchestrator
from services.ai.lm_facade import LMFacade
from services.ai.framework_model import FrameworkResult, FrameworkStepResult, ResultOptions
from api.models import Session, SessionStatus

# Tests
class TestAIOrchestrator():
    """Tests for the AIOrchestrator class."""
    
    @pytest.mark.asyncio
    @patch('builtins.input', side_effect=['adidas.com', '1'])
    async def test_run_success(self, mock_input):
        """Test running the AI orchestration flow with successful execution."""
      
        # Create a session ID
        session_id = str(uuid.uuid4())
        initial_framework_result = FrameworkResult(
            id="test_framework",
            step_results=[]
        )
        # Setup mock session data
        session_data = Session(id=session_id, created_at=datetime.datetime.now(), status=SessionStatus.STARTED, current_step_id="initial_input", result=initial_framework_result)
        mock_lm = MagicMock(spec=LMFacade)
        mock_lm.invoke_t2t.return_value = "Option 1||Option 2||Option 3"
        orchestrator = AIOrchestrator(framework_id="test_framework", lm_facade=mock_lm)
        result = await orchestrator.run(session_data)
        assert mock_input.call_count == 2
        assert result

    @pytest.mark.asyncio
    # @patch('services.ai.ai_orchestrator.get_db')
    @patch('builtins.input', side_effect=['1'])
    async def test_run_success_pickup_incomplete_session(self, mock_input):
        """Test running the AI orchestration flow with successful execution."""
      
        session_id = str(uuid.uuid4())
        initial_framework_result = FrameworkResult(
            id="test_framework",
            step_results=[
                FrameworkStepResult(id="initial_input", result=[ResultOptions(result_options=["adidas.com"], selected_option=0)])
            ]
        )
        session_data = Session(id=session_id, created_at=datetime.datetime.now(), status=SessionStatus.STARTED, current_step_id="initial_input", result=initial_framework_result)
        mock_lm = MagicMock(spec=LMFacade)
        mock_lm.invoke_t2t.return_value = "Option 1||Option 2||Option 3"
        orchestrator = AIOrchestrator(framework_id="test_framework", lm_facade=mock_lm)
        result = await orchestrator.run(session_data)
        assert mock_input.call_count == 1
        assert result


if __name__ == "__main__":
    pytest.main(["-xvs", "test_ai_orchestrator.py"])
