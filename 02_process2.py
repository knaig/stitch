import argparse
import spacy
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
import logging
import time
from multiprocessing import Pool, Manager
import json
import os

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler("log_file.log")  # Output to file
    ]
)

# Initialize spaCy model globally
nlp = spacy.load("en_core_web_sm")

# Load sentiment analysis pipeline and models globally
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
model = AutoModel.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")

start_time = time.time()

def analyze_chunk(chunk, chunk_index, total_chunks, counter, lock):
    with lock:
        counter.value += 1
        progress = (counter.value / total_chunks) * 100
    logging.info(f"Analyzing chunk {chunk_index + 1}/{total_chunks} ({progress:.2f}% complete)")
    # Perform NER, sentiment analysis, and embeddings on the chunk
    doc = nlp(chunk)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    sentiment = sentiment_pipeline(chunk)
    inputs = tokenizer(chunk, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        embeddings_chunk = model(**inputs).last_hidden_state.mean(dim=1)
    processed_segment = {
        "content": chunk,
        "meta": {
            "entities": entities,
            "sentiment": sentiment,
            "embeddings": embeddings_chunk.numpy().tolist()
        }
    }
    logging.info(json.dumps(processed_segment, indent=2))  # Log each processed segment for debugging
    return processed_segment

def analyze_text(transcription):
    max_length = 512
    chunks = [transcription[i:i + max_length] for i in range(0, len(transcription), max_length)]
    
    total_chunks = len(chunks)
    manager = Manager()
    counter = manager.Value('i', 0)
    lock = manager.Lock()
    chunk_indexed = [(chunk, index, total_chunks, counter, lock) for index, chunk in enumerate(chunks)]

    with Pool() as pool:
        processed_segments = pool.starmap(analyze_chunk, chunk_indexed)

    return processed_segments

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Analyze transcription text.")
    parser.add_argument("file_path", type=str, help="Path to the transcription text file")
    args = parser.parse_args()

    # Read the transcription text from the file
    with open(args.file_path, 'r', encoding='utf-8') as file:
        transcription = file.read()

    # Analyze the transcription
    logging.info("Starting analysis")
    processed_segments = analyze_text(transcription)
    logging.info("Analysis complete")

    # Validate JSON structure
    try:
        json.dumps(processed_segments)
    except (TypeError, ValueError) as e:
        raise ValueError("Invalid JSON structure in processed segments.") from e

    # Derive the output file name for processed segments
    base_name, ext = os.path.splitext(args.file_path)
    output_file = f"{base_name}_processed_segments{ext}"

    # Save the processed segments as a single JSON array
    with open(output_file, "w") as f:
        json.dump(processed_segments, f, indent=2)
    
    logging.info(f"Processed segments saved to {output_file}")

if __name__ == "__main__":
    main()
