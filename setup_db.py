"""
Setup script: Creates the MongoDB collections and indexes for restMovies.

Prerequisites:
  - MongoDB running on localhost:27017
  - pip install pymongo python-dotenv

Usage:
  python setup_db.py
"""
import os
import pymongo
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "restMovies")

client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB]

# ---- 1. Create collections (idempotent) ----
existing = db.list_collection_names()

for name in ["movies", "users", "ratings", "comments"]:
    if name not in existing:
        db.create_collection(name)
        print(f"  Created collection: {name}")
    else:
        print(f"  Collection already exists: {name}")

# ---- 2. Create indexes ----
# Users: unique username
db["users"].create_index("username", unique=True)
print("  Index: users.username (unique)")

# Ratings: one rating per user per movie, plus fast lookup by movieId
db["ratings"].create_index([("movieId", 1), ("userId", 1)], unique=True)
db["ratings"].create_index("movieId")
print("  Index: ratings.(movieId, userId) (unique)")
print("  Index: ratings.movieId")

# Comments: fast lookup by movieId, sorted by date
db["comments"].create_index([("movieId", 1), ("createdAt", -1)])
print("  Index: comments.(movieId, createdAt)")

# Movies: text search on title, indexes for common query fields
db["movies"].create_index("title")
db["movies"].create_index("cast")
db["movies"].create_index("genres")
db["movies"].create_index("directors")
db["movies"].create_index("countries")
db["movies"].create_index("year")
db["movies"].create_index("runtime")
print("  Index: movies (title, cast, genres, directors, countries, year, runtime)")

# ---- 3. Insert a sample movie if collection is empty ----
if db["movies"].count_documents({}) == 0:
    sample_movie = {
        "title": "The Shawshank Redemption",
        "year": 1994,
        "runtime": 142,
        "genres": ["Drama"],
        "directors": ["Frank Darabont"],
        "cast": ["Tim Robbins", "Morgan Freeman"],
        "countries": ["USA"],
        "plot": "Two imprisoned men bond over a number of years.",
    }
    result = db["movies"].insert_one(sample_movie)
    print(f"\n  Inserted sample movie with _id: {result.inserted_id}")
else:
    print(f"\n  Movies collection already has {db['movies'].count_documents({})} document(s)")

print("\nDatabase setup complete!")
print(f"  URI: {MONGO_URI}")
print(f"  DB:  {MONGO_DB}")
