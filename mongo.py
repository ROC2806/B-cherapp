from urllib.parse import quote_plus
from pymongo import MongoClient
import streamlit as st

mongo_secrets = st.secrets["mongodb"]

# Username und Passwort URL-kodieren
MONGO_USERNAME = quote_plus(mongo_secrets["MONGO_USERNAME"])
MONGO_PASSWORD = quote_plus(mongo_secrets["MONGO_PASSWORD"])
MONGO_CLUSTER = mongo_secrets["MONGO_CLUSTER"]


# Verbindungs-URI zusammensetzen
MONGO_URI = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["Leseapp"]
wishlist_collection = db["wishlist"]
read_books_collection = db["read_books"]

def load_data():
    # Wunschliste und gelesene Bücher aus der Datenbank laden
    wishlist = list(wishlist_collection.find({"Status": "offen"}, {"_id": 0}))  # _id ignorieren
    read_books = list(read_books_collection.find({}, {"_id": 0}))  # _id ignorieren
    return {"wishlist": wishlist, "read_books": read_books}

def save_data(data):
    # Alle alten Einträge löschen
    wishlist_collection.delete_many({})
    read_books_collection.delete_many({})
    
    # Neue Daten einfügen (Wunschliste und gelesene Bücher)
    if data["wishlist"]:
        wishlist_collection.insert_many(data["wishlist"])
    if data["read_books"]:
        read_books_collection.insert_many(data["read_books"])