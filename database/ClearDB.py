from pymongo import MongoClient

# Connect to your MongoDB Atlas
client = MongoClient("")
db = client['']
collection = db['']

# Delete all documents
collection.delete_many({})

print("All documents deleted, collection still exists!")
