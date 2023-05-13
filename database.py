# Student's name: Phu Nguyen
# Course: CPSC 449-01 13991
# Assignment: Final Project
# Date: May 12, 2023

from pymongo import MongoClient
from dotenv import load_dotenv
import os
import pymongo

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client.bookstore
books_collection = db['books']

# Indexing
# Create a compound index of title and sales
books_collection.create_index([("sales", pymongo.DESCENDING), ("title", pymongo.ASCENDING)])

# Create a compound index of author and stock
books_collection.create_index([("stock", pymongo.DESCENDING), ("author", pymongo.ASCENDING)])

# Create a single index of price range
books_collection.create_index([("price", pymongo.ASCENDING)])

# Check indexes info
# print(sorted(list(books_collection.index_information())))

