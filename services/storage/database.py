from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import motor.motor_asyncio  # For async MongoDB
import redis.asyncio as redis # For async Redis
import pickle
from config.settings import Settings
from models.job_db import JobDBModel
from models.session_db import SessionDBModel
from models.user_session_db import UserSessionDBModel
from api.models import User
from enum import Enum

class ModelType(str, Enum):
    SESSIONS = "sessions"
    JOBS = "jobs"
    USERS = "users"

class DataAccess:
    def __init__(self, settings: Settings):
        # Configure MongoDB connection
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URI)
        self.mongo_db = self.mongo_client[settings.DATABASE_NAME]
        
        # Configure Redis connection
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT,
            username=settings.REDIS_USER, 
            password=settings.REDIS_SECRET
        )
        
        self.session_collection = self.mongo_db[ModelType.SESSIONS]
        self.job_collection = self.mongo_db[ModelType.JOBS]
        self.user_collection = self.mongo_db[ModelType.USERS]

    def _cache_key(self, model_type: ModelType, model_id: str) -> str:
        return f"{model_type.value}:{model_id}"

    # Session Operations:
    async def insert_session(self, session_db_model: SessionDBModel, user: Optional[User] = None) -> None:
        session_dict = session_db_model.model_dump()
        if await self.session_collection.find_one({"session.id": session_dict["session"]["id"]}):
            raise ValueError(f"Session with id {session_db_model.session.id} already exists.")
        
        # Insert the session
        await self.session_collection.insert_one(session_dict)
        await self.redis_client.set(
            self._cache_key(ModelType.SESSIONS, session_db_model.session.id),
            pickle.dumps(session_db_model),
        )
        
        # Associate with user if provided
        if user:
            await self._associate_session_with_user(
                session_id=session_db_model.session.id, 
                user=user
            )

    async def update_session(self, session_db_model: SessionDBModel) -> None:
        session_dict = session_db_model.model_dump()
        if not await self.session_collection.find_one({"session.id": session_dict["session"]["id"]}):
            raise ValueError(f"Session with id {session_db_model.session.id} does not exist.")
        await self.session_collection.replace_one(
            {"session.id": session_dict["session"]["id"]},
            session_dict,
            upsert=True,
        )
        await self.redis_client.set(
            self._cache_key(ModelType.SESSIONS, session_db_model.session.id),
            pickle.dumps(session_db_model),
        )

    async def delete_session(self, session_id: str) -> None:
        if not await self.session_collection.find_one({"session.id": session_id}):
            raise ValueError(f"Session with id {session_id} does not exist.")
        await self.session_collection.delete_one({"session.id": session_id})
        await self.redis_client.delete(self._cache_key(ModelType.SESSIONS, session_id))

    async def get_session(self, session_id: str) -> Optional[SessionDBModel]:
        cached_data = await self.redis_client.get(self._cache_key(ModelType.SESSIONS, session_id))
        if cached_data:
            return pickle.loads(cached_data)
        print(f"Cache miss for session ID: {session_id}")
        session_data = await self.session_collection.find_one({"session.id": session_id})
        if session_data:
            session_db_model = SessionDBModel.model_validate(session_data)
            await self.redis_client.set(
                self._cache_key(ModelType.SESSIONS, session_id),
                pickle.dumps(session_db_model),
            )
            return session_db_model
        return None

    # Job Operations:
    async def insert_job(self, job_db_model: JobDBModel) -> None:
        job_dict = job_db_model.model_dump()
        if await self.job_collection.find_one({"job.id": job_dict["job"]["id"]}):
            raise ValueError(f"Job with id {job_db_model.job.id} already exists.")
        await self.job_collection.insert_one(job_dict)
        await self.redis_client.set(
            self._cache_key(ModelType.JOBS, job_db_model.job.id),
            pickle.dumps(job_db_model),
        )

    async def delete_job(self, job_id: str) -> None:
        if not await self.job_collection.find_one({"job.id": job_id}):
            raise ValueError(f"Job with id {job_id} does not exist.")
        await self.job_collection.delete_one({"job.id": job_id})
        await self.redis_client.delete(self._cache_key(ModelType.JOBS, job_id))

    async def get_job(self, job_id: str) -> Optional[JobDBModel]:
        cached_data = await self.redis_client.get(self._cache_key(ModelType.JOBS, job_id))
        if cached_data:
            return pickle.loads(cached_data)

        job_data = await self.job_collection.find_one({"job.id": job_id})
        if job_data:
            job_db_model = JobDBModel.model_validate(job_data)
            await self.redis_client.set(
                self._cache_key(ModelType.JOBS, job_id),
                pickle.dumps(job_db_model),
            )
            return job_db_model
        return None
        
    # User-Session Association Operations:
    async def _associate_session_with_user(self, session_id: str, user: User) -> None:
        """Associate a session with a user."""
        # Check if user exists
        user_data = await self.user_collection.find_one({"user.id": user.id})
        
        if user_data:
            # User exists, update their session list
            user_model = UserSessionDBModel.model_validate(user_data)
            if session_id not in user_model.session_ids:
                user_model.session_ids.append(session_id)
                user_model.updated_at = datetime.now()
                
                await self.user_collection.replace_one(
                    {"user.id": user.id},
                    user_model.model_dump(),
                    upsert=True
                )
        else:
            # Create new user record
            user_model = UserSessionDBModel(
                user=user,
                session_ids=[session_id],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            await self.user_collection.insert_one(user_model.model_dump())
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for a user."""
        user_data = await self.user_collection.find_one({"user.id": user_id})
        if user_data:
            user_model = UserSessionDBModel.model_validate(user_data)
            return user_model.session_ids
        return []
    
    async def get_sessions_for_user(self, user_id: str) -> List[SessionDBModel]:
        """Get all session data for a user."""
        session_ids = await self.get_user_sessions(user_id)
        sessions = []
        
        for session_id in session_ids:
            session = await self.get_session(session_id)
            if session:
                sessions.append(session)
        
        return sessions
        
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        user_data = await self.user_collection.find_one({"user.id": user_id})
        if user_data:
            user_model = UserSessionDBModel.model_validate(user_data)
            return user_model.user
        return None