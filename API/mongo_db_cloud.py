from flask import Flask, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# MongoDB Atlas connection string (replace with your own connection string)
MONGO_URI = "mongodb+srv://<username>:<password>@cluster0.mongodb.net/mydatabase?retryWrites=true&w=majority"

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI)
db = client['mydatabase']  # Replace with your database name
collection = db['mycollection']  # Replace with your collection name

@app.route('/get_data', methods=['GET'])
def get_data():
    # Query the MongoDB collection (empty query to fetch all documents)
    documents = collection.find()

    # Convert MongoDB documents to a list of dictionaries
    data = []
    for doc in documents:
        doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
        data.append(doc)
    
    # Return the data as JSON
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)