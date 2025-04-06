"""
Tests for the AI orchestrator.

NO_AI_CODE=True
"""
import pytest
from unittest.mock import MagicMock, patch
import uuid

from services.ai.ai_orchestrator import AIOrchestrator
from services.ai.lm_facade import LMFacade
from services.ai.framework_model import FrameworkResult, FrameworkStepResult, ResultOptions

# Mock the database interactions
class MockDB:
    def __init__(self):
        self.sessions = MockCollection()
        self.jobs = MockCollection()


class MockCollection:
    def __init__(self):
        self.data = {}
    
    async def find_one(self, query):
        session_id = query.get("id")
        return self.data.get(session_id, {"id": session_id, "brand_framework": {"brand_name": "Test Brand", "brand_link": "https://testbrand.com"}})
    
    async def insert_one(self, document):
        self.data[document["id"]] = document
        return document
    
    async def update_one(self, filter_query, update_query):
        session_id = filter_query.get("id")
        if session_id in self.data:
            if "$set" in update_query:
                self.data[session_id].update(update_query.get("$set", {}))
            return MagicMock(modified_count=1)
        return MagicMock(modified_count=0)


@pytest.fixture
def mock_get_db():
    """Create a mock for the get_db function."""
    
    async def _get_db():
        return MockDB()
    
    return _get_db


# Tests
class TestAIOrchestrator():
    """Tests for the AIOrchestrator class."""
    
    @pytest.mark.asyncio
    @patch('services.ai.ai_orchestrator.get_db')
    @patch('builtins.input', side_effect=['adidas.com', '1'])
    async def test_run_success(self, mock_input, mock_get_db_func):
        """Test running the AI orchestration flow with successful execution."""
        # Configure mock DB
        db_instance = MockDB()
        mock_get_db_func.return_value = db_instance
      
        # Create a session ID
        session_id = str(uuid.uuid4())
        
        # Create initial session data with framework result
        initial_framework_result = FrameworkResult(
            id="test_framework",
            step_results=[]
        )
        
        # Setup mock session data
        session_data = {
            "id": session_id,
            "status": "started",
            "current_step": "initial_input",
            "framework_result": initial_framework_result
        }
        db_instance.sessions.data[session_id] = session_data
        
        # Mock LMFacade
        mock_lm = MagicMock(spec=LMFacade)
        mock_lm.invoke_t2t.return_value = "Option 1||Option 2||Option 3"
        
        # Create orchestrator with test framework
        orchestrator = AIOrchestrator(framework_id="test_framework", lm_facade=mock_lm)

        # Run the flow
        result = await orchestrator.run(session_id)
        assert mock_input.call_count == 2
        assert result["success"]
        assert not result["error"]
        assert "result" in result
        assert mock_get_db_func.called

    @pytest.mark.asyncio
    @patch('services.ai.ai_orchestrator.get_db')
    @patch('builtins.input', side_effect=['1'])
    async def test_run_success_pickup_incomplete_session(self, mock_input, mock_get_db_func):
        """Test running the AI orchestration flow with successful execution."""
        # Configure mock DB
        db_instance = MockDB()
        mock_get_db_func.return_value = db_instance
      
        # Create a session ID
        session_id = str(uuid.uuid4())
        
        # Create initial session data with framework result
        initial_framework_result = FrameworkResult(
            id="test_framework",
            step_results=[
                FrameworkStepResult(id="initial_input", result=[ResultOptions(result_options=["adidas.com"], selected_option=0)])
            ]
        )
        
        # Setup mock session data
        session_data = {
            "id": session_id,
            "status": "started",
            "current_step": "initial_input",
            "framework_result": initial_framework_result
        }
        db_instance.sessions.data[session_id] = session_data
        
        # Mock LMFacade
        mock_lm = MagicMock(spec=LMFacade)
        mock_lm.invoke_t2t.return_value = "Option 1||Option 2||Option 3"
        
        # Create orchestrator with test framework
        orchestrator = AIOrchestrator(framework_id="test_framework", lm_facade=mock_lm)

        # Run the flow
        result = await orchestrator.run(session_id)
        assert mock_input.call_count == 1
        assert result["success"]
        assert not result["error"]
        assert "result" in result
        assert mock_get_db_func.called


if __name__ == "__main__":
    pytest.main(["-xvs", "test_ai_orchestrator.py"])
