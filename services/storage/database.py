from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
import pytz
import motor.motor_asyncio
import redis.asyncio as aioredis
import json
from config.settings import settings

# Redis client for caching
redis_client = None

# MongoDB client
mongo_client = None
mongo_db = None

class MongoDB:
    """MongoDB database client."""
    def __init__(self, db):
        self.db = db
        self.sessions = SessionCollection(db.sessions)
        self.jobs = JobsCollection(db.jobs)


class BaseCollection:
    """Base collection with common MongoDB operations."""
    def __init__(self, collection):
        self.collection = collection
    
    async def insert_one(self, document):
        """Insert one document into the collection."""
        result = await self.collection.insert_one(document)
        return document
    
    async def find_one(self, query):
        """Find one document in the collection."""
        # Try to get from cache first
        if redis_client:
            cache_key = f"{self.collection.name}:{query.get('id')}"
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Not found in cache, get from MongoDB
        document = await self.collection.find_one(query)
        
        # Save to cache if found
        if document and redis_client:
            cache_key = f"{self.collection.name}:{document['id']}"
            await redis_client.set(
                cache_key, 
                json.dumps(self._convert_for_json(document)),
                ex=3600  # Cache for 1 hour
            )
        
        return document
    
    async def update_one(self, filter_query, update_query):
        """Update one document in the collection."""
        result = await self.collection.update_one(filter_query, update_query)
        
        # Invalidate cache
        if result.modified_count > 0 and redis_client:
            doc_id = filter_query.get('id')
            if doc_id:
                cache_key = f"{self.collection.name}:{doc_id}"
                await redis_client.delete(cache_key)
        
        return result.modified_count > 0
    
    async def delete_one(self, query):
        """Delete one document from the collection."""
        result = await self.collection.delete_one(query)
        
        # Invalidate cache
        if result.deleted_count > 0 and redis_client:
            doc_id = query.get('id')
            if doc_id:
                cache_key = f"{self.collection.name}:{doc_id}"
                await redis_client.delete(cache_key)
        
        return result.deleted_count > 0
    
    async def delete_many(self, query):
        """Delete multiple documents from the collection."""
        result = await self.collection.delete_many(query)
        
        # TODO: Implement more granular cache invalidation
        # For now, we'll just note that delete_many operations may leave stale cache entries
        
        return result.deleted_count
    
    def _convert_for_json(self, document):
        """Convert MongoDB document for JSON serialization."""
        if document:
            # Convert MongoDB ObjectId to string if present
            if "_id" in document:
                document["_id"] = str(document["_id"])
            
            # Convert datetime objects to ISO format
            for key, value in document.items():
                if isinstance(value, datetime):
                    document[key] = value.isoformat()
        
        return document


class SessionCollection(BaseCollection):
    """Collection for session documents."""
    async def find_active_sessions(self, limit=10, skip=0):
        """Find active sessions."""
        cursor = self.collection.find(
            {"status": {"$ne": "completed"}}
        ).sort("created_at", -1).skip(skip).limit(limit)
        
        return await cursor.to_list(length=limit)


class JobsCollection(BaseCollection):
    """Collection for job documents."""
    async def find_by_session(self, session_id):
        """Find jobs by session ID."""
        cursor = self.collection.find({"session_id": session_id}).sort("created_at", -1)
        return await cursor.to_list(length=100)


# Global in-memory data store (used when MongoDB is not available)
_in_memory_data = {
    "sessions": {},
    "jobs": {}
}

async def get_db():
    """Get database instance."""
    global mongo_db
    if mongo_db is None:
        # If MongoDB isn't available, use in-memory database
        class InMemoryCollection:
            def __init__(self, name):
                self.name = name
                # Use the global data store
                if name not in _in_memory_data:
                    _in_memory_data[name] = {}
                self._data = _in_memory_data[name]
            
            async def insert_one(self, document):
                self._data[document['id']] = document
                return document
            
            async def find_one(self, query):
                session_id = query.get('id')
                return self._data.get(session_id)
            
            async def update_one(self, filter_query, update_query):
                session_id = filter_query.get('id')
                session = self._data.get(session_id)
                
                if session:
                    update_data = update_query.get('$set', {})
                    session.update(update_data)
                    return True
                return False
            
            async def delete_one(self, query):
                session_id = query.get('id')
                if session_id in self._data:
                    del self._data[session_id]
                    return True
                return False
            
            async def delete_many(self, query):
                session_id = query.get('session_id')
                deleted = 0
                for key in list(self._data.keys()):
                    if self._data[key].get('session_id') == session_id:
                        del self._data[key]
                        deleted += 1
                return deleted
            
            async def find(self, query=None):
                # Return a simple cursor-like object
                class Cursor:
                    def __init__(self, data, query):
                        self.data = data
                        self.query = query
                        
                    async def to_list(self, length=None):
                        result = []
                        for doc in self.data.values():
                            if self.query is None or all(doc.get(k) == v for k, v in self.query.items()):
                                result.append(doc)
                        return result
                    
                    def sort(self, field, direction=-1):
                        # Simplified sort that doesn't actually sort
                        return self
                    
                    def limit(self, count):
                        # Simplified limit that doesn't actually limit
                        return self
                    
                    def skip(self, count):
                        # Simplified skip that doesn't actually skip
                        return self
                
                return Cursor(self._data, query)
        
        class InMemoryDB:
            def __init__(self):
                self.sessions = InMemoryCollection("sessions")
                self.jobs = InMemoryJobsCollection("jobs")
        
        class InMemoryJobsCollection(InMemoryCollection):
            async def find_by_session(self, session_id):
                result = []
                for doc in self._data.values():
                    if doc.get('session_id') == session_id:
                        result.append(doc)
                return result
        
        print("Using in-memory database")
        return InMemoryDB()
    else:
        return MongoDB(mongo_db)


async def init_db():
    """Initialize database connection."""
    global mongo_client, mongo_db, redis_client
    
    try:
        # Initialize MongoDB connection
        mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.MONGODB_URI, 
            serverSelectionTimeoutMS=5000  # Shorter timeout for quicker failure
        )
        # Force a connection to verify it works
        await mongo_client.admin.command('ping')
        mongo_db = mongo_client[settings.DATABASE_NAME]
        print(f"Connected to MongoDB: {settings.MONGODB_URI}")
    except Exception as e:
        print(f"Warning: Could not connect to MongoDB: {e}")
        print("Falling back to in-memory database for MongoDB")
        # Fall back to in-memory implementation
        mongo_client = None
        mongo_db = None
        # We'll handle this in get_db()
    
    try:
        # Initialize Redis connection
        redis_client = aioredis.from_url(
            settings.REDIS_URI,
            socket_connect_timeout=5.0  # Shorter timeout
        )
        # Test connection
        await redis_client.ping()
        print(f"Connected to Redis: {settings.REDIS_URI}")
    except Exception as e:
        print(f"Warning: Could not connect to Redis: {e}")
        print("Redis caching will be disabled")
        redis_client = None


async def close_db():
    """Close database connections."""
    if mongo_client:
        mongo_client.close()
    
    if redis_client:
        await redis_client.close()


async def seed_mock_data():
    """Seed mock data for development."""
    db = await get_db()
    
    # Check if data already exists
    existing = await db.sessions.find_one({"status": "started"})
    if existing:
        print("Mock data already exists")
        return
    
    first_session = {
        "id": str(uuid4()),
        "created_at": datetime.now(pytz.UTC),
        "status": "started",
        "current_step": "brand-framework"
    }
    
    await db.sessions.insert_one(first_session)
    print(f"Seeded mock session with ID: {first_session['id']}")
