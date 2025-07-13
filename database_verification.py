#!/usr/bin/env python3
"""
Direct database verification to check the actual numbers
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection from backend .env
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

async def verify_database_numbers():
    """Verify the actual numbers in the database"""
    logger.info("🔍 DIRECT DATABASE VERIFICATION")
    logger.info("=" * 60)
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        logger.info(f"📡 Connected to MongoDB: {DB_NAME}")
        
        # Count clients
        total_clients = await db.clients.count_documents({})
        logger.info(f"👥 Total Clients: {total_clients}")
        
        # Get client details
        clients = await db.clients.find({}).to_list(length=None)
        logger.info(f"📋 Client Details:")
        for i, client in enumerate(clients, 1):
            name = client.get('name', 'Unknown')
            hotel_name = client.get('hotel_name', 'Unknown')
            stage = client.get('current_stage', 'Unknown')
            logger.info(f"   {i}. {name} ({hotel_name}) - Stage: {stage}")
        
        # Count documents
        total_documents = await db.documents.count_documents({})
        logger.info(f"📄 Total Documents: {total_documents}")
        
        # Get document details
        documents = await db.documents.find({}).to_list(length=None)
        logger.info(f"📋 Document Details:")
        for i, doc in enumerate(documents, 1):
            name = doc.get('name', 'Unknown')
            client_id = doc.get('client_id', 'Unknown')
            logger.info(f"   {i}. {name} (Client: {client_id})")
        
        # Count trainings
        total_trainings = await db.trainings.count_documents({})
        logger.info(f"🎓 Total Trainings: {total_trainings}")
        
        # Get training details
        trainings = await db.trainings.find({}).to_list(length=None)
        logger.info(f"📋 Training Details:")
        for i, training in enumerate(trainings, 1):
            name = training.get('name', 'Unknown')
            client_id = training.get('client_id', 'Unknown')
            logger.info(f"   {i}. {name} (Client: {client_id})")
        
        # Stage distribution
        stage_1_clients = await db.clients.count_documents({"current_stage": "I.Aşama"})
        stage_2_clients = await db.clients.count_documents({"current_stage": "II.Aşama"})
        stage_3_clients = await db.clients.count_documents({"current_stage": "III.Aşama"})
        
        logger.info("=" * 60)
        logger.info("📊 SUMMARY:")
        logger.info(f"   👥 Total Clients: {total_clients}")
        logger.info(f"   📄 Total Documents: {total_documents}")
        logger.info(f"   🎓 Total Trainings: {total_trainings}")
        logger.info(f"   📈 Stage Distribution:")
        logger.info(f"      - Stage 1: {stage_1_clients}")
        logger.info(f"      - Stage 2: {stage_2_clients}")
        logger.info(f"      - Stage 3: {stage_3_clients}")
        
        # Expected vs actual
        logger.info("=" * 60)
        logger.info("🎯 EXPECTED VS ACTUAL:")
        expected_clients = 2
        expected_documents = 2
        expected_trainings = 2
        
        logger.info(f"   Clients: Expected {expected_clients}, Actual {total_clients}")
        logger.info(f"   Documents: Expected {expected_documents}, Actual {total_documents}")
        logger.info(f"   Trainings: Expected {expected_trainings}, Actual {total_trainings}")
        
        # Close connection
        client.close()
        
        return {
            "total_clients": total_clients,
            "total_documents": total_documents,
            "total_trainings": total_trainings,
            "stage_distribution": {
                "stage_1": stage_1_clients,
                "stage_2": stage_2_clients,
                "stage_3": stage_3_clients
            },
            "clients": clients,
            "documents": documents,
            "trainings": trainings
        }
        
    except Exception as e:
        logger.error(f"❌ Database verification failed: {str(e)}")
        return None

async def main():
    """Main function"""
    logger.info("🚀 STARTING DIRECT DATABASE VERIFICATION")
    logger.info(f"⏰ Test Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    result = await verify_database_numbers()
    
    if result:
        logger.info("✅ Database verification completed successfully")
    else:
        logger.error("❌ Database verification failed")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())