from pymongo import MongoClient
import json

# Connect to MongoDB
mongo_client = MongoClient('mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941')

# Check the rotacrm database
db = mongo_client['rotacrm']

print('Collections in rotacrm database:', db.list_collection_names())

# Check if there's a clients collection
if 'clients' in db.list_collection_names():
    # Search for specific clients
    print('\nSearching for clients with specific names in rotacrm database...')
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

    # Check all clients in database
    print('\nChecking all clients in rotacrm database...')
    all_clients = list(db.clients.find({}))
    print(f'Total clients in database: {len(all_clients)}')
    for client in all_clients:
        print(f"ID: {client.get('id')}, Name: {client.get('name')}, Hotel: {client.get('hotel_name')}")
else:
    print('No clients collection found in rotacrm database')

# Check if there's a users collection
if 'users' in db.list_collection_names():
    # Check users collection for CLIENT role users
    print('\nChecking users collection for CLIENT role users in rotacrm database...')
    users = list(db.users.find({'role': 'client'}))
    print(f'Found {len(users)} users with CLIENT role:')
    for user in users:
        print(f"ID: {user.get('id')}, Name: {user.get('name')}, Email: {user.get('email')}, Client ID: {user.get('client_id', 'None')}")
else:
    print('No users collection found in rotacrm database')

# Check for any other collections that might store client data
print('\nChecking for other collections that might store client data in rotacrm database...')
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
                # Check if any documents contain the search terms
                for term in search_terms:
                    for field in sample_doc.keys():
                        if isinstance(sample_doc[field], str):
                            query = {field: {'$regex': term, '$options': 'i'}}
                            count = db[collection_name].count_documents(query)
                            if count > 0:
                                print(f"Found {count} documents in {collection_name} with '{term}' in field '{field}'")
                                docs = list(db[collection_name].find(query).limit(5))
                                for doc in docs:
                                    print(f"  Document: {doc}")