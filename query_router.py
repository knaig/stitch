import logging
import os
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/search": {"origins": "*"}, r"/write-content": {"origins": "http://134.209.150.110:3000"}})

# Setup logging
logging.basicConfig(level=logging.INFO)

# Ensure pipeline and document_store are set up before handling requests
setup_pipeline("./trump_clip1_transcription/transcription_with_timestamps_processed_segments.json", 
               "./trump_clip1_transcription/document_store.pkl")

@app.route('/search', methods=['POST'])
def search():
    if request.is_json:
        data = request.get_json()
        logging.info(f"Received data: {data}")  # Log received data
        query = data.get('query')
        
        if query:
            try:
                # Perform the search query
                result = search_query(query)

                # Assuming `result` contains the path to the relevant video segment
                segment_path = result.get('segment_path')

                if segment_path and os.path.exists(segment_path):
                    logging.info(f"Segment found: {segment_path}")
                    response = jsonify({"segment_path": segment_path})
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    return response
                else:
                    logging.error("Relevant video segment not found.")
                    return jsonify({"error": "Relevant video segment not found."}), 404

            except Exception as e:
                logging.error(f"Error processing query: {e}")
                return jsonify({"error": "An error occurred while processing your request."}), 500
        else:
            return jsonify({"error": "Query parameter is missing."}), 400
    
    return jsonify({"error": "Invalid request format; JSON expected."}), 400

@app.route('/video_segment', methods=['GET'])
def stream_video_segment():
    segment_path = request.args.get('segment_path')
    if not segment_path or not os.path.exists(segment_path):
        logging.error(f"Video segment not found: {segment_path}")
        return jsonify({"error": "Segment not found"}), 404

    try:
        range_header = request.headers.get('Range', None)
        file_size = os.path.getsize(segment_path)
        start, end = 0, file_size - 1

        if range_header:
            range_match = range_header.replace('bytes=', '').split('-')
            start = int(range_match[0])
            end = int(range_match[1]) if range_match[1] else end

        chunk_size = 1024 * 1024  # 1MB chunks
        length = end - start + 1

        def generate():
            with open(segment_path, 'rb') as video_file:
                video_file.seek(start)
                while True:
                    chunk = video_file.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        response = Response(generate(), status=206, mimetype='video/mp4', headers={
            'Content-Range': f'bytes {start}-{end}/{file_size}',
            'Accept-Ranges': 'bytes',
            'Content-Length': str(length),
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        })
        return response

    except Exception as e:
        logging.error(f"Error streaming video: {e}")
        return jsonify({"error": "An error occurred while streaming the video."}), 500

if __name__ == "__main__":
    # Run the Flask app with the host set to '0.0.0.0' to allow external connections
    app.run(host='0.0.0.0', port=5000)
