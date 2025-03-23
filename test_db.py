#!/usr/bin/env python3
"""
Test script to verify MongoDB and Redis integration.
"""
import asyncio
import json
from datetime import datetime
from uuid import uuid4

from services.storage.database import init_db, get_db, close_db

async def test_mongodb_and_redis():
    """Test MongoDB and Redis connections and operations."""
    print("Initializing database connections...")
    await init_db()
    
    # Get DB instance
    db = await get_db()
    
    # Create a test session
    session_id = str(uuid4())
    test_session = {
        "id": session_id,
        "created_at": datetime.utcnow(),
        "status": "test",
        "current_step": "test",
        "brand_framework": {
            "brand_name": "Test Brand",
            "industry": "Technology",
            "brand_personality": "Innovative",
            "target_audience": "Developers",
            "brand_values": ["Quality", "Innovation", "Reliability"],
            "brand_description": "A test brand for developers."
        }
    }
    
    print(f"Creating test session with ID: {session_id}")
    await db.sessions.insert_one(test_session)
    
    # First retrieval (should come from MongoDB)
    print("Retrieving session (first time, from MongoDB)...")
    start_time = datetime.now()
    retrieved_session = await db.sessions.find_one({"id": session_id})
    end_time = datetime.now()
    mongodb_time = (end_time - start_time).total_seconds() * 1000
    
    print(f"MongoDB retrieval time: {mongodb_time:.2f}ms")
    print(f"Retrieved session: {retrieved_session['id']}")
    
    # Second retrieval (should come from Redis cache)
    print("Retrieving session again (should be from Redis cache)...")
    start_time = datetime.now()
    cached_session = await db.sessions.find_one({"id": session_id})
    end_time = datetime.now()
    redis_time = (end_time - start_time).total_seconds() * 1000
    
    print(f"Redis cache retrieval time: {redis_time:.2f}ms")
    print(f"Retrieved session: {cached_session['id']}")
    
    # Update the session
    print("Updating session...")
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {"status": "updated", "updated_at": datetime.utcnow()}}
    )
    
    # Retrieve updated session (should come from MongoDB again due to cache invalidation)
    print("Retrieving updated session (should be from MongoDB again)...")
    start_time = datetime.now()
    updated_session = await db.sessions.find_one({"id": session_id})
    end_time = datetime.now()
    updated_time = (end_time - start_time).total_seconds() * 1000
    
    print(f"Updated retrieval time: {updated_time:.2f}ms")
    print(f"Updated session status: {updated_session['status']}")
    
    # Create a test job
    job_id = f"test-{session_id}"
    test_job = {
        "id": job_id,
        "session_id": session_id,
        "type": "test",
        "status": "processing",
        "progress": 0,
        "created_at": datetime.utcnow()
    }
    
    print(f"Creating test job with ID: {job_id}")
    await db.jobs.insert_one(test_job)
    
    # Retrieve job
    print("Retrieving job...")
    job = await db.jobs.find_one({"id": job_id})
    print(f"Retrieved job: {job['id']}")
    
    # Update job
    print("Updating job...")
    await db.jobs.update_one(
        {"id": job_id},
        {
            "$set": {
                "status": "completed",
                "progress": 100,
                "completed_at": datetime.utcnow(),
                "result": {"message": "Test completed successfully"}
            }
        }
    )
    
    # Retrieve updated job
    print("Retrieving updated job...")
    updated_job = await db.jobs.find_one({"id": job_id})
    print(f"Updated job status: {updated_job['status']}")
    
    # List jobs for session
    print("Listing jobs for session...")
    session_jobs = await db.jobs.find_by_session(session_id)
    print(f"Found {len(session_jobs)} jobs for session")
    
    # Clean up
    print("Cleaning up test data...")
    await db.sessions.delete_one({"id": session_id})
    await db.jobs.delete_one({"id": job_id})
    
    print("Test completed successfully!")
    
    # Close connections
    await close_db()

if __name__ == "__main__":
    asyncio.run(test_mongodb_and_redis())
