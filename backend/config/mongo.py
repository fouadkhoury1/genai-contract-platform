# config/mongo.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env if needed

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "genai_contracts")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]