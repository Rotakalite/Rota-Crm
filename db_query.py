import os
import sys
import json
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
db_name = "sustainable_tourism_crm"

async def get_clients():
    """Get all clients from the database"""
    logger.info("\n=== Getting clients from database ===")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Get all clients
        clients = await db.clients.find({}).to_list(length=None)
        logger.info(f"Found {len(clients)} clients in the database")
        
        # Print client details
        for i, client_data in enumerate(clients):
            logger.info(f"Client {i+1}:")
            logger.info(f"  ID: {client_data.get('id')}")
            logger.info(f"  Name: {client_data.get('name')}")
            logger.info(f"  Hotel Name: {client_data.get('hotel_name')}")
            logger.info(f"  Contact Person: {client_data.get('contact_person')}")
            logger.info(f"  Email: {client_data.get('email')}")
            logger.info(f"  Current Stage: {client_data.get('current_stage')}")
        
        return clients
    except Exception as e:
        logger.error(f"Error getting clients: {str(e)}")
        return []

async def get_documents():
    """Get all documents from the database"""
    logger.info("\n=== Getting documents from database ===")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Get all documents
        documents = await db.documents.find({}).to_list(length=None)
        logger.info(f"Found {len(documents)} documents in the database")
        
        # Group documents by client_id
        documents_by_client = {}
        for doc in documents:
            client_id = doc.get('client_id')
            if client_id not in documents_by_client:
                documents_by_client[client_id] = []
            documents_by_client[client_id].append(doc)
        
        # Print document distribution by client
        logger.info(f"Documents are distributed across {len(documents_by_client)} clients")
        
        for client_id, docs in documents_by_client.items():
            logger.info(f"Client ID: {client_id} has {len(docs)} documents")
            
            # Print details of first few documents for each client
            for i, doc in enumerate(docs[:3]):  # Show only first 3 docs per client
                logger.info(f"  Document {i+1}:")
                logger.info(f"    ID: {doc.get('id')}")
                logger.info(f"    Name: {doc.get('name')}")
                logger.info(f"    Type: {doc.get('document_type')}")
                logger.info(f"    Stage: {doc.get('stage')}")
                logger.info(f"    File Path: {doc.get('file_path')}")
                logger.info(f"    Original Filename: {doc.get('original_filename')}")
            
            if len(docs) > 3:
                logger.info(f"    ... and {len(docs) - 3} more documents")
        
        return documents
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return []

async def get_trainings():
    """Get all trainings from the database"""
    logger.info("\n=== Getting trainings from database ===")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Get all trainings
        trainings = await db.trainings.find({}).to_list(length=None)
        logger.info(f"Found {len(trainings)} trainings in the database")
        
        # Group trainings by client_id
        trainings_by_client = {}
        for training in trainings:
            client_id = training.get('client_id')
            if client_id not in trainings_by_client:
                trainings_by_client[client_id] = []
            trainings_by_client[client_id].append(training)
        
        # Print training distribution by client
        logger.info(f"Trainings are distributed across {len(trainings_by_client)} clients")
        
        for client_id, client_trainings in trainings_by_client.items():
            logger.info(f"Client ID: {client_id} has {len(client_trainings)} trainings")
            
            # Print details of first few trainings for each client
            for i, training in enumerate(client_trainings[:3]):  # Show only first 3 trainings per client
                logger.info(f"  Training {i+1}:")
                logger.info(f"    ID: {training.get('id')}")
                logger.info(f"    Name: {training.get('name')}")
                logger.info(f"    Subject: {training.get('subject')}")
                logger.info(f"    Trainer: {training.get('trainer')}")
                logger.info(f"    Participant Count: {training.get('participant_count')}")
                logger.info(f"    Status: {training.get('status')}")
                
                # Format training date if available
                training_date = training.get('training_date')
                if training_date:
                    logger.info(f"    Training Date: {training_date}")
            
            if len(client_trainings) > 3:
                logger.info(f"    ... and {len(client_trainings) - 3} more trainings")
        
        return trainings
    except Exception as e:
        logger.error(f"Error getting trainings: {str(e)}")
        return []

async def main():
    """Main function to run all data queries"""
    logger.info("Starting database queries...")
    
    # Get clients
    clients = await get_clients()
    
    # Get documents
    documents = await get_documents()
    
    # Get trainings
    trainings = await get_trainings()
    
    # Print summary
    logger.info("\n=== SUMMARY ===")
    logger.info(f"Total clients: {len(clients)}")
    logger.info(f"Total documents: {len(documents)}")
    logger.info(f"Total trainings: {len(trainings)}")
    
    # Print data structure for Email Management integration
    logger.info("\n=== DATA STRUCTURE FOR EMAIL MANAGEMENT INTEGRATION ===")
    
    # Client structure
    if clients:
        logger.info("Client structure:")
        client_example = clients[0]
        for key, value in client_example.items():
            if key != "_id":  # Skip MongoDB _id
                logger.info(f"  {key}: {type(value).__name__}")
    
    # Document structure
    if documents:
        logger.info("Document structure:")
        doc_example = documents[0]
        for key, value in doc_example.items():
            if key != "_id":  # Skip MongoDB _id
                logger.info(f"  {key}: {type(value).__name__}")
    
    # Training structure
    if trainings:
        logger.info("Training structure:")
        training_example = trainings[0]
        for key, value in training_example.items():
            if key != "_id":  # Skip MongoDB _id
                logger.info(f"  {key}: {type(value).__name__}")

if __name__ == "__main__":
    asyncio.run(main())