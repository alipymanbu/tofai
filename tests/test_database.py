# Tests for services.storage.database.DataAccess
# NO_AI_CODE=True

import os
import unittest
from unittest.mock import AsyncMock
from datetime import datetime
import pickle

from config.settings import Settings  # Assuming your settings class is here
from services.storage.database import DataAccess
from models.job_db import JobDBModel
from models.session_db import SessionDBModel
from api.models import JobStatus, Job, Session

class AsyncMockContextManager:
    def __init__(self, mock):
        self.mock = mock

    async def __aenter__(self):
        return self.mock

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class TestDataAccess(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Set temporary environment variables for the test
        os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
        os.environ["DATABASE_NAME"] = "test_db"
        os.environ["REDIS_HOST"] = "localhost"
        os.environ["REDIS_PORT"] = "6379"

        self.settings = Settings()  # Settings() now reads the environment variables
        self.data_access = DataAccess(self.settings)
        self.data_access.session_collection = AsyncMock()
        self.data_access.job_collection = AsyncMock()
        self.data_access.redis_client = AsyncMock()

        self.session = Session(id="session1", created_at=datetime.now(), current_step_id="step1")
        self.session_db_model = SessionDBModel(session=self.session)
        self.job = Job(id="job1", session_id="session1", created_at=datetime.now(), status=JobStatus.PROCESSING)
        self.job_db_model = JobDBModel(job=self.job)

    async def asyncTearDown(self):
        # Clear the temporary environment variables after the test
        del os.environ["MONGODB_URI"]
        del os.environ["DATABASE_NAME"]
        del os.environ["REDIS_HOST"]
        del os.environ["REDIS_PORT"]

    async def test_insert_session_success(self):
        self.data_access.session_collection.find_one.return_value = None
        self.data_access.session_collection.insert_one.return_value = None
        self.data_access.redis_client.set.return_value = None

        await self.data_access.insert_session(self.session_db_model)

        self.data_access.session_collection.insert_one.assert_called_once()
        self.data_access.redis_client.set.assert_called_once()

    async def test_insert_session_duplicate_id(self):
        self.data_access.session_collection.find_one.return_value = {"session": {"id": "session1"}}

        with self.assertRaises(ValueError):
            await self.data_access.insert_session(self.session_db_model)

    async def test_update_session_success(self):
        self.data_access.session_collection.find_one.return_value = {"session": {"id": "session1"}}
        self.data_access.session_collection.replace_one.return_value = None
        self.data_access.redis_client.set.return_value = None

        await self.data_access.update_session(self.session_db_model)

        self.data_access.session_collection.replace_one.assert_called_once()
        self.data_access.redis_client.set.assert_called_once()

    async def test_update_session_not_found(self):
        self.data_access.session_collection.find_one.return_value = None

        with self.assertRaises(ValueError):
            await self.data_access.update_session(self.session_db_model)

    async def test_delete_session_success(self):
        self.data_access.session_collection.find_one.return_value = {"session": {"id": "session1"}}
        self.data_access.session_collection.delete_one.return_value = None
        self.data_access.redis_client.delete.return_value = None

        await self.data_access.delete_session("session1")

        self.data_access.session_collection.delete_one.assert_called_once()
        self.data_access.redis_client.delete.assert_called_once()

    async def test_delete_session_not_found(self):
        self.data_access.session_collection.find_one.return_value = None

        with self.assertRaises(ValueError):
            await self.data_access.delete_session("session1")

    async def test_get_session_from_cache(self):
        self.data_access.redis_client.get.return_value = pickle.dumps(self.session_db_model)

        result = await self.data_access.get_session("session1")

        self.assertEqual(result, self.session_db_model)
        self.data_access.session_collection.find_one.assert_not_called()

    async def test_get_session_from_db(self):
        self.data_access.redis_client.get.return_value = None
        self.data_access.session_collection.find_one.return_value = self.session_db_model.dict()
        self.data_access.redis_client.set.return_value = None

        result = await self.data_access.get_session("session1")

        self.assertEqual(result, self.session_db_model)
        self.data_access.redis_client.set.assert_called_once()

    async def test_get_session_not_found(self):
        self.data_access.redis_client.get.return_value = None
        self.data_access.session_collection.find_one.return_value = None

        result = await self.data_access.get_session("session1")

        self.assertIsNone(result)

    async def test_insert_job_success(self):
        self.data_access.job_collection.find_one.return_value = None
        self.data_access.job_collection.insert_one.return_value = None
        self.data_access.redis_client.set.return_value = None

        await self.data_access.insert_job(self.job_db_model)

        self.data_access.job_collection.insert_one.assert_called_once()
        self.data_access.redis_client.set.assert_called_once()

    async def test_insert_job_duplicate_id(self):
        self.data_access.job_collection.find_one.return_value = {"job": {"id": "job1"}}

        with self.assertRaises(ValueError):
            await self.data_access.insert_job(self.job_db_model)

    async def test_delete_job_success(self):
        self.data_access.job_collection.find_one.return_value = {"job": {"id": "job1"}}
        self.data_access.job_collection.delete_one.return_value = None
        self.data_access.redis_client.delete.return_value = None

        await self.data_access.delete_job("job1")

        self.data_access.job_collection.delete_one.assert_called_once()
        self.data_access.redis_client.delete.assert_called_once()

    async def test_delete_job_not_found(self):
        self.data_access.job_collection.find_one.return_value = None

        with self.assertRaises(ValueError):
            await self.data_access.delete_job("job1")

    async def test_get_job_from_cache(self):
        self.data_access.redis_client.get.return_value = pickle.dumps(self.job_db_model)

        result = await self.data_access.get_job("job1")

        self.assertEqual(result, self.job_db_model)
        self.data_access.job_collection.find_one.assert_not_called()

    async def test_get_job_from_db(self):
        self.data_access.redis_client.get.return_value = None
        self.data_access.job_collection.find_one.return_value = self.job_db_model.model_dump() #model_dump() instead of dict()
        self.data_access.redis_client.set.return_value = None
        result = await self.data_access.get_job("job1")
        self.assertEqual(result, self.job_db_model) #compare the job objects.

    async def test_get_job_not_found(self):
        self.data_access.redis_client.get.return_value = None
        self.data_access.job_collection.find_one.return_value = None

        result = await self.data_access.get_job("job1")

        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()