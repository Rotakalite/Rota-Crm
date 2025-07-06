import pymongo
import json
from datetime import datetime
from bson import json_util

# MongoDB connection details
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"

def parse_json(data):
    """Convert MongoDB data to JSON serializable format"""
    return json.loads(json_util.dumps(data))

def main():
    """Connect to MongoDB and print data"""
    # Connect to MongoDB
    client = pymongo.MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get all collections
    collections = db.list_collection_names()
    print(f"Collections in database: {collections}")
    
    # Get clients data
    clients = list(db.clients.find())
    print(f"\nFound {len(clients)} clients:")
    for client in clients:
        # Remove MongoDB ObjectId which is not JSON serializable
        client_data = parse_json(client)
        print(json.dumps(client_data, indent=2))
    
    # Get documents data
    documents = list(db.documents.find())
    print(f"\nFound {len(documents)} documents:")
    for doc in documents:
        # Remove MongoDB ObjectId which is not JSON serializable
        doc_data = parse_json(doc)
        print(json.dumps(doc_data, indent=2))
    
    # Get trainings data
    trainings = list(db.trainings.find())
    print(f"\nFound {len(trainings)} trainings:")
    for training in trainings:
        # Remove MongoDB ObjectId which is not JSON serializable
        training_data = parse_json(training)
        print(json.dumps(training_data, indent=2))

if __name__ == "__main__":
    main()