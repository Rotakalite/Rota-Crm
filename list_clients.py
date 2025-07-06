import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import json
from bson import json_util

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"
ALT_DB_NAME = "rotacrm"

# Parse MongoDB document to JSON
def parse_json(data):
    return json.loads(json_util.dumps(data))

async def list_all_clients():
    logger.info("Listing all clients in both databases")
    
    # Connect to sustainable_tourism_crm
    client1 = AsyncIOMotorClient(MONGO_URL)
    db1 = client1[DB_NAME]
    
    # Connect to rotacrm
    client2 = AsyncIOMotorClient(MONGO_URL)
    db2 = client2[ALT_DB_NAME]
    
    # List all clients in sustainable_tourism_crm
    logger.info(f"Clients in {DB_NAME}:")
    async for doc in db1.clients.find():
        logger.info(f"Client: {parse_json(doc)}")
    
    # List all clients in rotacrm
    logger.info(f"Clients in {ALT_DB_NAME}:")
    async for doc in db2.clients.find():
        logger.info(f"Client: {parse_json(doc)}")

if __name__ == "__main__":
    asyncio.run(list_all_clients())