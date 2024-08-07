import json

def validate_json(filename):
    try:
        with open(filename, 'r') as file:
            json.load(file)
        print("JSON is valid.")
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")

validate_json('C:\stitch\processed_segments.json')
