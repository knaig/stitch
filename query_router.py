from flask import Flask, request, jsonify
from transformers import pipeline
from indexing import search_query, setup_pipeline
from flask_cors import CORS
import os

from transformers import pipeline



app = Flask(__name__)
#CORS(app, resources={r"/search": {"origins": "*"}, r"/write-content": {"origins": "*"}})  # Allow all origins for '/search' and '/write-content'
CORS(app, resources={r"/*": {
    "origins": "*",
    "allow_headers": ["Content-Type", "Authorization"],
    "methods": ["GET", "POST", "PUT", "DELETE"]
}})

# Ensure pipeline and document_store are set up before handling requests
setup_pipeline(".\\trump_clip1_transcription\\transcription_with_timestamps_processed_segments.json", ".\\trump_clip1_transcription\\document_store.pkl")

@app.route('/search', methods=['POST'])
def search():
    if request.is_json:
        data = request.get_json()
        print("data = ", data)
        query = data.get('query')
        if query:
            result = search_query(query)
            response = jsonify(result)       
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response
    return jsonify({"error": "Invalid request"}), 400

if __name__ == '__main__':
    app.run(debug=True)
