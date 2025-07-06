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

async def get_users():
    """Get all users from the database"""
    logger.info("\n=== Getting users from database ===")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Get all users
        users = await db.users.find({}).to_list(length=None)
        logger.info(f"Found {len(users)} users in the database")
        
        # Print user details
        for i, user in enumerate(users):
            logger.info(f"User {i+1}:")
            logger.info(f"  ID: {user.get('id')}")
            logger.info(f"  Clerk User ID: {user.get('clerk_user_id')}")
            logger.info(f"  Name: {user.get('name')}")
            logger.info(f"  Email: {user.get('email')}")
            logger.info(f"  Role: {user.get('role')}")
            logger.info(f"  Client ID: {user.get('client_id')}")
            logger.info(f"  Created At: {user.get('created_at')}")
        
        return users
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return []

async def get_guest_engagement():
    """Get all guest engagement records from the database"""
    logger.info("\n=== Getting guest engagement records from database ===")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Get all guest engagement records
        records = await db.guest_engagement.find({}).to_list(length=None)
        logger.info(f"Found {len(records)} guest engagement records in the database")
        
        # Print record details
        for i, record in enumerate(records):
            logger.info(f"Record {i+1}:")
            logger.info(f"  ID: {record.get('id')}")
            logger.info(f"  Guest Name: {record.get('guest_name')}")
            logger.info(f"  Room Number: {record.get('room_number')}")
            logger.info(f"  Client ID: {record.get('client_id')}")
            logger.info(f"  Eco Actions: {record.get('eco_actions')}")
            logger.info(f"  Sustainability Score: {record.get('sustainability_score')}")
            logger.info(f"  Created At: {record.get('created_at')}")
        
        return records
    except Exception as e:
        logger.error(f"Error getting guest engagement records: {str(e)}")
        return []

async def main():
    """Main function to run database queries"""
    logger.info("Starting database queries...")
    
    # Get users
    users = await get_users()
    
    # Get guest engagement records
    records = await get_guest_engagement()
    
    # Print summary
    logger.info("\n=== SUMMARY ===")
    logger.info(f"Total users: {len(users)}")
    logger.info(f"Total guest engagement records: {len(records)}")
    
    # Count users by role
    admin_users = [user for user in users if user.get('role') == 'admin']
    client_users = [user for user in users if user.get('role') == 'client']
    logger.info(f"Admin users: {len(admin_users)}")
    logger.info(f"Client users: {len(client_users)}")
    
    # Count users with client_id
    users_with_client_id = [user for user in users if user.get('client_id')]
    logger.info(f"Users with client_id: {len(users_with_client_id)}")

if __name__ == "__main__":
    asyncio.run(main())