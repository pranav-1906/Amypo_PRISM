import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Fetch settings with safe fallbacks
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "prism_db")

try:
    # Initialize the MongoDB Client
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # Ping the server to verify the connection
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
    
    # Select the database
    db = client[DB_NAME]
    
    # Export the collections so your blueprints can import them cleanly
    questions_collection = db["questions"]
    logs_collection = db["evaluation_logs"]
    users_collection = db["users"]  # Pre-emptively adding this for your /login route
    
except Exception as e:
    print(f"❌ Failed to connect to MongoDB. Please check if MongoDB is running.")
    print(f"Error details: {e}")