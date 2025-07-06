import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import json
from bson import json_util
from datetime import datetime

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

async def create_test_data():
    """Create test data for email management endpoints"""
    logger.info("Creating test data for email management endpoints")
    
    # Connect to rotacrm database
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[ALT_DB_NAME]
    
    # Get existing clients
    clients = await db.clients.find().to_list(length=None)
    client_ids = [client["id"] for client in clients]
    
    # Check if we have the clients we're looking for
    target_clients = ["DENEME OTEL", "TEST OTEL", "SES123", "Can", "ALP OTEL"]
    found_clients = []
    
    for client in clients:
        client_name = client.get("client_name", "")
        hotel_name = client.get("hotel_name", "")
        
        for target in target_clients:
            if target.lower() in client_name.lower() or target.lower() in hotel_name.lower():
                found_clients.append(client)
                logger.info(f"Found target client: {client_name} / {hotel_name}")
    
    # If we don't have all the target clients, create the missing ones
    if len(found_clients) < len(target_clients):
        logger.info(f"Creating missing target clients ({len(found_clients)} found, {len(target_clients)} needed)")
        
        # Find which targets are missing
        found_names = []
        for client in found_clients:
            client_name = client.get("client_name", "")
            hotel_name = client.get("hotel_name", "")
            found_names.append(client_name.lower())
            found_names.append(hotel_name.lower())
        
        missing_targets = []
        for target in target_clients:
            if not any(target.lower() in name for name in found_names):
                missing_targets.append(target)
        
        logger.info(f"Missing targets: {missing_targets}")
        
        # Create missing clients
        for target in missing_targets:
            client_id = f"{target.upper().replace(' ', '_')}_CLIENT_001"
            
            # Check if client_id already exists
            if client_id in client_ids:
                logger.info(f"Client ID {client_id} already exists, skipping")
                continue
            
            new_client = {
                "id": client_id,
                "client_id": client_id,
                "client_name": target,
                "hotel_name": target,
                "contact_person": f"contact@{target.lower().replace(' ', '')}.com",
                "email": f"info@{target.lower().replace(' ', '')}.com",
                "current_stage": "I.Aşama",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert new client
            await db.clients.insert_one(new_client)
            logger.info(f"Created new client: {target}")
            
            # Create root folder for the new client
            root_folder = {
                "id": f"root_{client_id}",
                "client_id": client_id,
                "name": f"{target} SYS",
                "parent_folder_id": None,
                "folder_path": f"{target} SYS",
                "level": 0,
                "created_at": datetime.utcnow()
            }
            
            await db.folders.insert_one(root_folder)
            logger.info(f"Created root folder for {target}")
            
            # Create column folders (A, B, C, D SÜTUNU)
            for column in ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]:
                column_folder = {
                    "id": f"{column.lower().replace(' ', '_')}_{client_id}",
                    "client_id": client_id,
                    "name": column,
                    "parent_folder_id": root_folder["id"],
                    "folder_path": f"{target} SYS/{column}",
                    "level": 1,
                    "created_at": datetime.utcnow()
                }
                
                await db.folders.insert_one(column_folder)
                logger.info(f"Created column folder {column} for {target}")
    
    # Create test documents for each client
    logger.info("Creating test documents for each client")
    
    # Get updated list of clients
    clients = await db.clients.find().to_list(length=None)
    
    for client in clients:
        client_id = client["id"]
        client_name = client.get("client_name", "")
        
        # Check if client already has documents
        existing_docs = await db.documents.find({"client_id": client_id}).to_list(length=None)
        
        if len(existing_docs) > 0:
            logger.info(f"Client {client_name} already has {len(existing_docs)} documents, skipping")
            continue
        
        # Create a test document
        document = {
            "id": f"doc_{client_id}_{datetime.utcnow().timestamp()}",
            "client_id": client_id,
            "name": f"Test Document for {client_name}",
            "document_type": "TR1_CRITERIA",
            "stage": "I.Aşama",
            "file_path": f"/test/path/{client_id}/document.pdf",
            "original_filename": "document.pdf",
            "file_size": 1024,
            "uploaded_by": "admin",
            "created_at": datetime.utcnow(),
            "local_upload": True
        }
        
        # Get root folder for this client
        root_folder = await db.folders.find_one({"client_id": client_id, "level": 0})
        
        if root_folder:
            # Get A SÜTUNU folder
            a_folder = await db.folders.find_one({"client_id": client_id, "level": 1, "name": "A SÜTUNU"})
            
            if a_folder:
                document["folder_path"] = a_folder["folder_path"]
                document["folder_level"] = 1
            else:
                document["folder_path"] = root_folder["folder_path"]
                document["folder_level"] = 0
        
        await db.documents.insert_one(document)
        logger.info(f"Created test document for {client_name}")
    
    # Create test trainings for each client
    logger.info("Creating test trainings for each client")
    
    for client in clients:
        client_id = client["id"]
        client_name = client.get("client_name", "")
        
        # Check if client already has trainings
        existing_trainings = await db.trainings.find({"client_id": client_id}).to_list(length=None)
        
        if len(existing_trainings) > 0:
            logger.info(f"Client {client_name} already has {len(existing_trainings)} trainings, skipping")
            continue
        
        # Create a test training
        training = {
            "id": f"training_{client_id}_{datetime.utcnow().timestamp()}",
            "client_id": client_id,
            "name": f"Sürdürülebilirlik Eğitimi - {client_name}",
            "subject": "Sürdürülebilir Turizm Uygulamaları",
            "participant_count": 15,
            "trainer": "Rota Eğitmen",
            "training_date": datetime.utcnow(),
            "description": f"{client_name} için sürdürülebilir turizm uygulamaları eğitimi",
            "status": "planned",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.trainings.insert_one(training)
        logger.info(f"Created test training for {client_name}")
    
    logger.info("Test data creation completed")

async def main():
    await create_test_data()

if __name__ == "__main__":
    asyncio.run(main())