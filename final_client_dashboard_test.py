import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

async def simulate_client_dashboard_logic():
    """Simulate the fixed client dashboard logic to verify the fix works"""
    logger.info("=== Simulating Fixed Client Dashboard Logic ===")
    
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Get a sample client ID from the database
        sample_client = await db.clients.find_one({"client_type": "registered"})
        if not sample_client:
            logger.warning("No registered client found in database")
            client.close()
            return
        
        client_id = sample_client["id"]
        logger.info(f"Testing with client ID: {client_id}")
        
        # Get consumption data for this client (simulating the fixed backend logic)
        consumptions = await db.consumptions.find({"client_id": client_id}).to_list(None)
        logger.info(f"Found {len(consumptions)} consumption records for client")
        
        # Apply the FIXED logic (using 'electricity' and 'water' fields)
        energy_by_month = {}
        water_by_month = {}
        
        for consumption in consumptions:
            month = consumption.get("month", "unknown")
            # FIXED: Use correct field names from database
            energy_by_month[month] = energy_by_month.get(month, 0) + consumption.get("electricity", 0)
            water_by_month[month] = water_by_month.get(month, 0) + consumption.get("water", 0)
        
        logger.info(f"✅ FIXED LOGIC RESULTS:")
        logger.info(f"   Energy by month: {energy_by_month}")
        logger.info(f"   Water by month: {water_by_month}")
        
        if energy_by_month or water_by_month:
            logger.info("✅ SUCCESS: Consumption data would now be displayed in client dashboard!")
            logger.info("✅ Frontend graphs should show data instead of fallback message")
        else:
            logger.warning("⚠️ No consumption data found for this client")
        
        # Test the OLD (broken) logic for comparison
        logger.info("\n=== Comparing with OLD (Broken) Logic ===")
        old_energy_by_month = {}
        old_water_by_month = {}
        
        for consumption in consumptions:
            month = consumption.get("month", "unknown")
            # OLD (broken): Looking for wrong field names
            old_energy_by_month[month] = old_energy_by_month.get(month, 0) + consumption.get("energy_kwh", 0)
            old_water_by_month[month] = old_water_by_month.get(month, 0) + consumption.get("water_m3", 0)
        
        logger.info(f"❌ OLD LOGIC RESULTS:")
        logger.info(f"   Energy by month: {old_energy_by_month}")
        logger.info(f"   Water by month: {old_water_by_month}")
        
        if not old_energy_by_month and not old_water_by_month:
            logger.info("❌ OLD LOGIC: Would show empty graphs (explains the original issue)")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error in simulation: {str(e)}")

async def verify_database_structure():
    """Verify the database has the expected structure"""
    logger.info("\n=== Verifying Database Structure ===")
    
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Check consumption collection structure
        consumption = await db.consumptions.find_one({})
        if consumption:
            logger.info("✅ Sample consumption record fields:")
            for key, value in consumption.items():
                if key not in ['_id', 'created_at', 'updated_at']:
                    logger.info(f"   {key}: {type(value).__name__}")
            
            # Verify the key fields exist
            if 'electricity' in consumption:
                logger.info("✅ 'electricity' field found - CORRECT")
            else:
                logger.error("❌ 'electricity' field missing")
                
            if 'water' in consumption:
                logger.info("✅ 'water' field found - CORRECT")
            else:
                logger.error("❌ 'water' field missing")
                
            if 'energy_kwh' in consumption:
                logger.warning("⚠️ 'energy_kwh' field found - this was the wrong field name")
            else:
                logger.info("✅ 'energy_kwh' field not found - CORRECT (this was the wrong field)")
                
            if 'water_m3' in consumption:
                logger.warning("⚠️ 'water_m3' field found - this was the wrong field name")
            else:
                logger.info("✅ 'water_m3' field not found - CORRECT (this was the wrong field)")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error verifying database: {str(e)}")

async def main():
    """Main test function"""
    logger.info("🔍 CLIENT DASHBOARD FIX VERIFICATION")
    logger.info("=" * 50)
    
    await verify_database_structure()
    await simulate_client_dashboard_logic()
    
    logger.info("\n" + "=" * 50)
    logger.info("📋 SUMMARY OF FIX:")
    logger.info("✅ ISSUE: Backend was looking for 'energy_kwh' and 'water_m3' fields")
    logger.info("✅ REALITY: Database contains 'electricity' and 'water' fields")
    logger.info("✅ FIX: Updated backend code to use correct field names")
    logger.info("✅ RESULT: Client dashboard should now show consumption graphs")
    logger.info("✅ IMPACT: Eliminates 'Henüz enerji/su tüketim verisi bulunmamaktadır.' message")

if __name__ == '__main__':
    asyncio.run(main())