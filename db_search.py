from pymongo import MongoClient
import json

# Connect to MongoDB
client = MongoClient('mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941')
db = client['sustainable_tourism_crm']

print('Collections in database:', db.list_collection_names())

# Search for specific clients
print('\nSearching for clients with specific names...')
search_terms = ['DENEME OTEL', 'TEST OTEL', 'SES123', 'Can', 'ALP OTEL']
query = {'$or': []}

# Search in name field
for term in search_terms:
    query['$or'].append({'name': {'$regex': term, '$options': 'i'}})
    query['$or'].append({'hotel_name': {'$regex': term, '$options': 'i'}})

clients = list(db.clients.find(query))
print(f'Found {len(clients)} clients matching search criteria:')
for client in clients:
    print(f"ID: {client.get('id')}, Name: {client.get('name')}, Hotel: {client.get('hotel_name')}")

# Check users collection for CLIENT role users
print('\nChecking users collection for CLIENT role users...')
users = list(db.users.find({'role': 'client'}))
print(f'Found {len(users)} users with CLIENT role:')
for user in users:
    print(f"ID: {user.get('id')}, Name: {user.get('name')}, Email: {user.get('email')}, Client ID: {user.get('client_id', 'None')}")

# Check all clients in database
print('\nChecking all clients in database...')
all_clients = list(db.clients.find({}))
print(f'Total clients in database: {len(all_clients)}')
for client in all_clients:
    print(f"ID: {client.get('id')}, Name: {client.get('name')}, Hotel: {client.get('hotel_name')}")

# Check if there are other databases in the same connection
print('\nChecking for other databases in the same connection...')
databases = client.list_database_names()
print(f'Databases: {databases}')

# Check for any other collections that might store client data
print('\nChecking for other collections that might store client data...')
for collection_name in db.list_collection_names():
    if collection_name not in ['clients', 'users']:
        print(f'\nChecking collection: {collection_name}')
        # Look for fields that might contain client identifiers
        sample_doc = db[collection_name].find_one()
        if sample_doc:
            print(f'Sample document fields: {list(sample_doc.keys())}')
            
            # Check if collection has client_id field
            if 'client_id' in sample_doc:
                print(f'Collection {collection_name} has client_id field')
                # Count documents for each client
                for client in all_clients:
                    count = db[collection_name].count_documents({'client_id': client.get('id')})
                    if count > 0:
                        print(f"Client {client.get('name')} has {count} documents in {collection_name}")