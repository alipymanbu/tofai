"""
Tests for the framework API routes.

This module provides unit tests for the API routes in api/routes/framework.py.
"""
import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
import uuid
from fastapi.testclient import TestClient
from fastapi import Depends

from main import app, lifespan
from api.dependencies import get_data_access
from services.storage.database import DataAccess
from api.models import GenerateOptionsRequest, InitInputRequest, Session, JobStatus, SessionStatus as DBSessionStatus
from models.session_db import SessionDBModel
from models.job_db import JobDBModel, Job
from services.ai.framework_model import FrameworkResult, FrameworkStepResult, ResultOptions

class TestFrameworkAPI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        async with lifespan(app):  # Use the lifespan context manager
            self.client = TestClient(app)
            self.mock_db = AsyncMock(spec=DataAccess)
            self.mock_aio = AsyncMock()

            self.session_id = str(uuid.uuid4())
            self.framework_id = "test_framework"
            self.step_id = "test_step"
            self.session = Session(id=self.session_id, created_at=datetime.now(timezone.utc), current_step_id=self.step_id, framework_id=self.framework_id)
            self.session_db_model = SessionDBModel(session=self.session)
            self.framework_result = FrameworkResult(
                id=self.framework_id,
                step_results=[FrameworkStepResult(id=self.step_id, result=[ResultOptions(result_options=["option1"], selected_option=0)])],
            )
            self.job = Job(
                id=str(uuid.uuid4()),
                session_id=self.session_id,
                created_at=datetime.now(timezone.utc),
                status=JobStatus.COMPLETED,
                progress=100,
                tasks_completed=[self.step_id],
                result={}
            )
            self.job_db_model = JobDBModel(job=self.job)

            async def override_get_data_access():
                return self.mock_db

            app.dependency_overrides[get_data_access] = override_get_data_access
            print(f"Arjun2: {app.dependency_overrides.get(get_data_access)}")
            print(f"Arjun4: {await override_get_data_access()}")

    async def asyncTearDown(self):
        app.dependency_overrides.clear()

    async def test_generate_step_options_success(self):
        print(f"Arjun: {app.dependency_overrides}")
        self.mock_db.get_session.return_value = self.session_db_model
        self.mock_aio.run.return_value = {"framework_result": self.framework_result, "current_step_id": "next_step"}
        self.mock_db.insert_job.return_value = None
        self.mock_db.update_session.return_value = None

        with patch("services.ai.ai_orchestrator.AIOrchestrator", return_value=self.mock_aio):
            response = self.client.post(
                f"/framework/steps/{self.step_id}/generate?session_id={self.session_id}",
                json=GenerateOptionsRequest(framework_id=self.framework_id, step_id=self.step_id).model_dump(),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "generation success")
        self.assertEqual(response.json()["status"], "completed")
        self.assertEqual(response.json()["progress"], 100)
        self.mock_db.update_session.assert_called_once()
        self.mock_db.insert_job.assert_called_once()

    async def test_generate_step_options_session_not_found(self):
        self.mock_db.get_session.return_value = None

        response = self.client.post(
            f"/framework/steps/{self.step_id}/generate?session_id={self.session_id}",
            json=GenerateOptionsRequest(framework_id=self.framework_id, step_id=self.step_id).model_dump(),
        )

        self.assertEqual(response.status_code, 404)

    async def test_generate_step_options_ai_error(self):
        self.mock_db.get_session.return_value = self.session_db_model
        self.mock_aio.run.side_effect = Exception("AI Error")
        self.mock_db.insert_job.return_value = None

        with patch("services.ai.ai_orchestrator.AIOrchestrator", return_value=self.mock_aio):
            response = self.client.post(
                f"/framework/steps/{self.step_id}/generate?session_id={self.session_id}",
                json=GenerateOptionsRequest(framework_id=self.framework_id, step_id=self.step_id).model_dump(),
            )

        self.assertEqual(response.status_code, 500)
        self.mock_db.insert_job.assert_called()

    async def test_select_step_option_success(self):
        self.mock_db.get_session.return_value = self.session_db_model
        self.mock_db.update_session.return_value = None
        self.mock_db.insert_job.return_value = None

        response = self.client.post(
            f"/framework/steps/{self.step_id}/select?session_id={self.session_id}&option_index=0&result_index=0",
            json={"framework_id": self.framework_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue("job_id" in response.json())
        self.assertTrue("created_at" in response.json())
        self.assertEqual(response.json()["framework_id"], self.framework_id)
        self.mock_db.update_session.assert_called_once()
        self.mock_db.insert_job.assert_called_once()

    async def test_select_step_option_session_not_found(self):
        self.mock_db.get_session.return_value = None

        response = self.client.post(
            f"/framework/steps/{self.step_id}/select?session_id={self.session_id}&option_index=0&result_index=0",
            json={"framework_id": self.framework_id},
        )

        self.assertEqual(response.status_code, 404)

    async def test_select_step_option_no_generations(self):
        self.session_db_model.session.result = None
        self.mock_db.get_session.return_value = self.session_db_model

        response = self.client.post(
            f"/framework/steps/{self.step_id}/select?session_id={self.session_id}&option_index=0&result_index=0",
            json={"framework_id": self.framework_id},
        )

        self.assertEqual(response.status_code, 400)

    async def test_initial_input_success(self):
        self.mock_db.get_session.return_value = self.session_db_model
        self.mock_db.update_session.return_value = None
        self.mock_db.insert_job.return_value = None

        response = self.client.post(
            f"/framework/steps/initial_input?session_id={self.session_id}",
            json=InitInputRequest(framework_id=self.framework_id, brand_link="http://test.com").model_dump(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue("job_id" in response.json())
        self.assertTrue("created_at" in response.json())
        self.assertEqual(response.json()["framework_id"], self.framework_id)
        self.mock_db.update_session.assert_called_once()
        self.mock_db.insert_job.assert_called_once()

    async def test_initial_input_session_not_found(self):
        self.mock_db.get_session.return_value = None

        response = self.client.post(
            f"/framework/steps/initial_input?session_id={self.session_id}",
            json=InitInputRequest(framework_id=self.framework_id, brand_link="http://test.com").model_dump(),
        )

        self.assertEqual(response.status_code, 404)