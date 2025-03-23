from typing import Dict, Any
from uuid import uuid4
from datetime import datetime

class InMemoryDB:
    def __init__(self):
        self.sessions = SessionCollection()

class SessionCollection:
    def __init__(self):
        self._data = {}
    
    async def insert_one(self, session):
        self._data[session['id']] = session
        return session
    
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

# Global in-memory database instance
in_memory_db = InMemoryDB()

async def get_db():
    return in_memory_db

async def init_db():
    # No initialization needed for in-memory database
    print("In-memory database initialized")

# Optional: Add some mock data for development
async def seed_mock_data():
    first_session = {
        "id": str(uuid4()),
        "created_at": datetime.utcnow(),
        "status": "started",
        "current_step": "brand-framework"
    }
    await in_memory_db.sessions.insert_one(first_session)