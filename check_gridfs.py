import pymongo
from bson import ObjectId
import gridfs

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "rotacrm"

# Connect to MongoDB
mongo_client = pymongo.MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]
fs = gridfs.GridFS(db)

# Check documents with gridfs_id
docs = list(db.documents.find({"gridfs_id": {"$exists": True}}).limit(5))
print(f"Found {len(docs)} documents with gridfs_id")

for doc in docs:
    doc_id = doc.get("id")
    doc_name = doc.get("name")
    gridfs_id = doc.get("gridfs_id")
    
    print(f"Document ID: {doc_id}")
    print(f"Document Name: {doc_name}")
    print(f"GridFS ID: {gridfs_id}")
    
    # Check if the file exists in GridFS
    try:
        file_id_obj = ObjectId(gridfs_id)
        exists = fs.exists(file_id_obj)
        print(f"File exists in GridFS: {exists}")
        
        if exists:
            # Get the file from GridFS
            grid_file = fs.get(file_id_obj)
            
            # Check file metadata
            print(f"GridFS file info: filename={grid_file.filename}, content_type={grid_file.content_type}, length={grid_file.length}")
            
            # Read the first 100 bytes of the file content
            content = grid_file.read(100)
            
            # Check if content is a PDF (starts with %PDF)
            is_pdf = content.startswith(b"%PDF-")
            print(f"Is PDF: {is_pdf}")
            
            # Check if content is text (contains placeholder text)
            is_placeholder = b"This is a placeholder document content" in content
            print(f"Is Placeholder: {is_placeholder}")
            
            # Print the first 50 bytes as hex
            print(f"First 50 bytes: {content[:50].hex()}")
    except Exception as e:
        print(f"Error checking GridFS: {str(e)}")
    
    print("---")

# Check GridFS files
files = list(db.fs.files.find().limit(5))
print(f"\nFound {len(files)} files in GridFS")

for file_info in files:
    file_id = file_info["_id"]
    filename = file_info.get("filename")
    content_type = file_info.get("contentType") or file_info.get("metadata", {}).get("content_type")
    length = file_info.get("length")
    
    print(f"File ID: {file_id}")
    print(f"Filename: {filename}")
    print(f"Content Type: {content_type}")
    print(f"Length: {length}")
    
    # Get the file from GridFS
    try:
        grid_file = fs.get(file_id)
        
        # Read the first 100 bytes of the file content
        content = grid_file.read(100)
        
        # Check if content is a PDF (starts with %PDF)
        is_pdf = content.startswith(b"%PDF-")
        print(f"Is PDF: {is_pdf}")
        
        # Check if content is text (contains placeholder text)
        is_placeholder = b"This is a placeholder document content" in content
        print(f"Is Placeholder: {is_placeholder}")
        
        # Print the first 50 bytes as hex
        print(f"First 50 bytes: {content[:50].hex()}")
    except Exception as e:
        print(f"Error reading file: {str(e)}")
    
    print("---")

# Close MongoDB connection
mongo_client.close()