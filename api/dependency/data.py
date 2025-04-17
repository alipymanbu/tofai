from services.storage.database import DataAccess
from config.settings import settings
from typing import Optional

data_access_instance: Optional[DataAccess] = None

async def initialize_data_access():
    global data_access_instance
    if not data_access_instance:
        data_access_instance = DataAccess(settings=settings)
    print(f"Arjun3: {data_access_instance}")

async def get_data_access() -> DataAccess:
    return data_access_instance