"""
Tests for the framework API routes.

This module provides unit tests for the API routes in api/routes/framework.py.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock
import uuid
import json
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

# Import get_db directly from the services.storage.database
from services.storage.database import get_db

# Add the mock modules to sys.path so they can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mocks'))

# Create mock classes for testing

class MockCollection:
    """Mock database collection for testing."""
    
    def __init__(self):
        self.data = {}
    
    async def find_one(self, query):
        """Find one item matching the query."""
        session_id = query.get("id")
        if session_id not in self.data:
            return None
        return self.data.get(session_id)
    
    async def insert_one(self, document):
        """Insert one document into the collection."""
        doc_id = document.get("id")
        if doc_id:
            self.data[doc_id] = document
        return document
    
    async def update_one(self, filter_query, update_query):
        """Update one document in the collection."""
        session_id = filter_query.get("id")
        if session_id in self.data and "$set" in update_query:
            self.data[session_id].update(update_query.get("$set", {}))
            return MagicMock(modified_count=1)
        return MagicMock(modified_count=0)
    
    def find(self, query=None):
        """Mock find that returns a cursor-like object."""
        filtered_data = []
        if query:
            for item in self.data.values():
                match = True
                for k, v in query.items():
                    if k not in item or item[k] != v:
                        match = False
                        break
                if match:
                    filtered_data.append(item)
        else:
            filtered_data = list(self.data.values())
        
        cursor = MagicMock()
        cursor.to_list = AsyncMock(return_value=filtered_data)
        cursor.sort = MagicMock(return_value=cursor)
        cursor.limit = MagicMock(return_value=cursor)
        return cursor


class MockDB:
    """Mock database for testing."""
    
    def __init__(self):
        self.sessions = MockCollection()
        self.jobs = MockCollection()


class MockAIOrchestrator:
    """Mock AIOrchestrator for testing."""
    
    async def run(self, session=None, current_step_id=None):
        """Mock implementation of run method."""
        framework_result = {
            "id": "brand_awareness_video",
            "step_results": [
                {
                    "id": current_step_id or "user_persona",
                    "result": [
                        {
                            "result_options": [
                                "Option 1: User Persona 1",
                                "Option 2: User Persona 2",
                                "Option 3: User Persona 3"
                            ],
                            "selected_option": -1
                        }
                    ]
                }
            ]
        }
        return {"framework_result": framework_result}


class MockGenerator:
    """Mock Generator for testing."""
    
    def __init__(self, framework_id=None, *args, **kwargs):
        self.framework_id = framework_id or "brand_awareness_video"
        self.framework = MagicMock()
        self.framework.id = self.framework_id
        self.framework.name = "Brand Awareness Video Framework"
        self.framework.description = "A framework for creating brand awareness videos"
        self.framework.initial_step = "initial_input"
        self.framework.final_step = "final_video"
    
    def get_step_by_id(self, step_id):
        """Mock get_step_by_id method."""
        step = MagicMock()
        step.id = step_id
        step.name = f"{step_id.replace('_', ' ').title()}"
        step.description = f"Description for {step_id}"
        step.requires_user_input = step_id.startswith("select_")
        step.next_step = "final_step" if step_id == "select_script" else f"{step_id}_next"
        return step
    
    def get_step_by_index(self, index):
        """Mock get_step_by_index method."""
        step = MagicMock()
        step.id = "initial_input"
        step.name = "Initial Input"
        step.description = "Initial input description"
        step.requires_user_input = True
        step.next_step = "user_persona"
        return step
    
    def get_selection_for_step_id(self, step_id):
        """Mock get_selection_for_step_id method."""
        if step_id.startswith("select_"):
            return step_id.replace("select_", "")
        return None


@pytest.fixture
def mock_db():
    """Create a mock database."""
    return MockDB()


@pytest.fixture
def session_id():
    """Generate a random session ID."""
    return str(uuid.uuid4())


@pytest.fixture
def app_client(monkeypatch):
    """Create an app with the actual framework router but with mocked dependencies."""
    # Add the mocks directory to the front of sys.path
    mocks_dir = os.path.join(os.path.dirname(__file__), 'mocks')
    if mocks_dir not in sys.path:
        sys.path.insert(0, mocks_dir)
    
    # Import the actual framework router
    from api.routes.framework import router
    
    # Create a FastAPI app
    app = FastAPI()
    app.include_router(router, prefix="/api")
    
    # Mock database
    mock_db = MockDB()
    app.dependency_overrides[get_db] = lambda: mock_db
    
    # Store mock_db in app.state for test access
    app.state.mock_db = mock_db
    
    client = TestClient(app)
    return client


class TestFrameworkAPIs:
    """Tests for the framework API routes."""
    
    def test_generate_step_options(self, app_client, session_id):
        """Test the generate_step_options endpoint."""
        # Set up test session
        mock_db = app_client.app.state.mock_db
        session_data = {
            "id": session_id,
            "status": "started",
            "current_step": "initial_input",
            "framework_result": {
                "id": "brand_awareness_video",
                "step_results": [
                    {
                        "id": "initial_input",
                        "result": [
                            {
                                "result_options": ["https://example.com"],
                                "selected_option": 0
                            }
                        ]
                    }
                ]
            }
        }
        mock_db.sessions.data[session_id] = session_data
        
        # Call the API endpoint
        response = app_client.post(
            f"/api/framework/steps/{session_id}/generate",
            json={
                "framework_id": "brand_awareness_video",
                "step_id": "user_persona"
            }
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "completed"
        assert data["progress"] == 100
        
        # Verify job creation
        jobs = list(mock_db.jobs.data.values())
        assert len(jobs) > 0
        assert jobs[-1]["session_id"] == session_id
        assert jobs[-1]["status"] == "completed"
    
    def test_select_step_option(self, app_client, session_id):
        """Test the select_step_option endpoint."""
        # Set up test session
        mock_db = app_client.app.state.mock_db
        framework_result = {
            "id": "brand_awareness_video",
            "step_results": [
                {
                    "id": "user_persona",
                    "result": [
                        {
                            "result_options": [
                                "Option 1: Sophie, The Minimalist Aesthete",
                                "Option 2: Alex, The Conscious Consumer", 
                                "Option 3: Marcus, The Quality Connoisseur"
                            ],
                            "selected_option": -1
                        }
                    ]
                }
            ]
        }
        
        session_data = {
            "id": session_id,
            "status": "in_progress",
            "current_step": "select_user_persona",
            "framework_result": json.dumps(framework_result)
        }
        mock_db.sessions.data[session_id] = session_data
        
        # Call the API endpoint
        response = app_client.post(
            f"/api/framework/steps/select_user_persona/select?session_id={session_id}&option_index=1&result_index=0&framework_id=brand_awareness_video"
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "completed"
        
        # Verify job creation
        jobs = list(mock_db.jobs.data.values())
        assert len(jobs) > 0
        assert jobs[-1]["session_id"] == session_id
        assert jobs[-1]["status"] == "completed"
    
    def test_initial_input(self, app_client, session_id):
        """Test the initial_input endpoint."""
        # Set up test session
        mock_db = app_client.app.state.mock_db
        session_data = {
            "id": session_id,
            "status": "started",
            "current_step": "initial_input"
        }
        mock_db.sessions.data[session_id] = session_data
        
        # Call the API endpoint
        response = app_client.post(
            f"/api/framework/steps/initial_input?session_id={session_id}",
            json={
                "framework_id": "brand_awareness_video",
                "brand_link": "https://example.com"
            }
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "completed"
        
        # Verify job creation
        jobs = list(mock_db.jobs.data.values())
        assert len(jobs) > 0
        assert jobs[-1]["session_id"] == session_id
        assert jobs[-1]["status"] == "completed"
    
    def test_session_not_found(self, app_client):
        """Test handling of non-existent sessions."""
        # Call the API endpoint with a non-existent session
        response = app_client.post(
            "/api/framework/steps/initial_input?session_id=non-existent-session",
            json={
                "framework_id": "brand_awareness_video",
                "brand_link": "https://example.com"
            }
        )
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]