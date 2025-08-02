import requests
import json
import logging
import sys
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://d787e851-4fbb-4d90-a594-90394e6ba15e.preview.emergentagent.com/api"

def check_database_directly():
    """Check MongoDB database directly for waste management records"""
    logger.info("\n=== Checking MongoDB database directly ===")
    
    try:
        import pymongo
        
        # Connect to MongoDB using URI from .env file
        with open('/app/backend/.env', 'r') as f:
            env_content = f.read()
            for line in env_content.splitlines():
                if line.startswith('MONGO_URL='):
                    mongo_url = line.split('=', 1)[1].strip().strip('"')
                    break
                    
        logger.info(f"Using MongoDB URL: {mongo_url}")
        
        # Connect to MongoDB
        client = pymongo.MongoClient(mongo_url)
        db_name = "sustainable_tourism_crm"  # Default DB name
        
        # Check if DB_NAME is specified in .env
        with open('/app/backend/.env', 'r') as f:
            env_content = f.read()
            for line in env_content.splitlines():
                if line.startswith('DB_NAME='):
                    db_name = line.split('=', 1)[1].strip().strip('"')
                    break
                    
        logger.info(f"Using database name: {db_name}")
        db = client[db_name]
        
        # Check waste_management collection
        waste_records = list(db.waste_management.find())
        logger.info(f"Found {len(waste_records)} waste records in database")
        
        if len(waste_records) > 0:
            logger.info(f"First record: {waste_records[0]}")
        else:
            logger.info("No waste records found in database")
        
        # Check clients collection
        clients = list(db.clients.find())
        logger.info(f"Found {len(clients)} clients in database")
        
        if len(clients) > 0:
            logger.info(f"First client: {clients[0]}")
            
            # Create a test waste record directly in the database
            client_id = clients[0]["id"]
            
            # Check if waste record already exists for this client/month/year
            existing = db.waste_management.find_one({
                "client_id": client_id,
                "year": 2024,
                "month": 6
            })
            
            if existing:
                logger.info(f"Waste record already exists for client {client_id}, year 2024, month 6")
            else:
                # Calculate totals and rates
                recyclable_waste = 25.0 + 15.5 + 30.0 + 10.0  # plastic + glass + paper + metal
                total_waste = 50.5 + recyclable_waste + 5.0 + 20.0  # organic + recyclable + electronic + mixed
                recycling_rate = (recyclable_waste / total_waste * 100) if total_waste > 0 else 0
                
                # Cost calculations
                waste_cost = total_waste * 2.5 + 5.0 * 15.0  # General waste + oil waste
                recycling_income = recyclable_waste * 0.8
                net_cost = waste_cost - recycling_income
                
                waste_record = {
                    "id": str(uuid.uuid4()),
                    "client_id": client_id,
                    "year": 2024,
                    "month": 6,
                    "organic_waste": 50.5,
                    "plastic_waste": 25.0,
                    "glass_waste": 15.5,
                    "paper_waste": 30.0,
                    "metal_waste": 10.0,
                    "electronic_waste": 5.0,
                    "oil_waste": 5.0,
                    "mixed_waste": 20.0,
                    "total_waste": total_waste,
                    "recycling_rate": round(recycling_rate, 2),
                    "waste_cost": round(waste_cost, 2),
                    "recycling_income": round(recycling_income, 2),
                    "net_cost": round(net_cost, 2),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                db.waste_management.insert_one(waste_record)
                logger.info(f"Created waste record with ID: {waste_record['id']} for client: {client_id}")
        else:
            logger.info("No clients found in database")
        
        return True
    except Exception as e:
        logger.error(f"Error checking database directly: {str(e)}")
        return False

def main():
    """Run database check"""
    logger.info("Starting database check...")
    
    # Check database directly
    db_result = check_database_directly()
    
    # Summary
    logger.info("\n=== Summary ===")
    logger.info(f"Database check: {'PASSED' if db_result else 'FAILED'}")
    
    if db_result:
        logger.info("Database check PASSED")
        return 0
    else:
        logger.error("Database check FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())