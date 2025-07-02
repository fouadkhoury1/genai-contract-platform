# test_mongo.py
from config.mongo import db

def test_connection():
    print("Collections:", db.list_collection_names())

if __name__ == "__main__":
    test_connection()