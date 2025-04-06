"""
Tests for the AI orchestrator.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch
import json
from datetime import datetime
import uuid

from services.ai.ai_orchestrator import AIOrchestrator
from services.ai.state import VideoCreationState

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
            self.data[session_id].update(update_query.get("$set", {}))
            return 1
        return 0


@pytest.fixture
def mock_get_db():
    """Create a mock for the get_db function."""
    
    async def _get_db():
        return MockDB()
    
    return _get_db


# Tests
class TestAIOrchestrator:
    """Tests for the AIOrchestrator class."""
    
    @pytest.mark.asyncio
    @patch("services.ai.ai_orchestrator.get_db")
    async def test_run_flow(self, mock_get_db_func, mock_get_db):
        """Test running the full AI orchestration flow."""
        # Setup
        db_instance = await mock_get_db()
        mock_get_db_func.return_value = db_instance
        session_id = str(uuid.uuid4())
        
        # Run the flow
        result = await orchestrator.run(session_id)
        
        # Check the result
        assert result["success"] is True
        assert "result" in result
        assert result["error"] is None
        
        # Verify DB operations
        assert mock_get_db_func.called
        assert db_instance.sessions.find_one.called
        assert db_instance.jobs.insert_one.called
        assert db_instance.jobs.update_one.called
        assert db_instance.sessions.update_one.called
    
    def test_initial_input(self, orchestrator):
        """Test the initial input step."""
        # Setup
        state = VideoCreationState(
            session_id="test-session",
            framework_id="brand_awareness_video",
            current_step_id="initial_input"
        )
        
        # Test with existing brand info
        state.brand_name = "Test Brand"
        state.brand_link = "https://testbrand.com"
        
        # Run the step
        updated_state = orchestrator._initial_input(state)
        
        # Check the state
        assert updated_state.next_step_id == "user_persona"
        assert updated_state.brand_link == "https://testbrand.com"
    
    def test_generate_options(self, orchestrator):
        """Test generating options."""
        # Setup for user persona
        state = VideoCreationState(
            session_id="test-session",
            framework_id="brand_awareness_video",
            current_step_id="user_persona",
            brand_link="https://testbrand.com"
        )
        state.update_param_values()
        
        # Run the step
        updated_state = orchestrator._generate_options(state)
        
        # Check the state
        assert updated_state.next_step_id == "select_user_persona"
        assert len(updated_state.current_options) > 0
        
        # Test content spaces
        state = VideoCreationState(
            session_id="test-session",
            framework_id="brand_awareness_video",
            current_step_id="content_spaces",
            brand_link="https://testbrand.com",
            user_persona="Option 1: Sophie, The Minimalist Aesthete"
        )
        state.update_param_values()
        
        # Run the step
        updated_state = orchestrator._generate_options(state)
        
        # Check the state
        assert updated_state.next_step_id == "select_content_spaces"
        assert len(updated_state.current_options) > 0
    
    def test_select_option(self, orchestrator):
        """Test selecting an option."""
        # Setup for user persona selection
        state = VideoCreationState(
            session_id="test-session",
            framework_id="brand_awareness_video",
            current_step_id="select_user_persona",
            current_options=[
                "Option 1: Sophie, The Minimalist Aesthete",
                "Option 2: Alex, The Conscious Consumer"
            ]
        )
        # Run the step
        updated_state = orchestrator._select_option(state)
        # Check the state
        assert updated_state.next_step_id == "content_spaces"
        assert updated_state.get_user_persona() == "Option 1: Sophie, The Minimalist Aesthete"

if __name__ == "__main__":
    pytest.main(["-xvs", "test_ai_orchestrator.py"])
