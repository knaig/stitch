import pickle
import json
import re
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import DensePassageRetriever, FARMReader
from haystack.pipelines import ExtractiveQAPipeline
import argparse
import os
import datetime
from haystack import Answer  # Import Answer from the relevant module
from haystack import Document  # Import Document from the appropriate module


def load_data(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")    
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
    

def index_data(processed_segments, document_store, retriever):
    documents = [{'content': segment['content']} for segment in processed_segments if isinstance(segment, dict) and 'content' in segment]
    document_store.write_documents(documents)
    document_store.update_embeddings(retriever)

def validate_result_structure(result):
    if not isinstance(result, dict) or 'documents' not in result:
        return False, "Invalid result format"
    documents = [{'content': doc.content} for doc in result['documents']]
    return True, "Result structure is valid"


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle Answer objects
        if isinstance(obj, Answer):
            return obj.to_dict()  # Convert Answer to dictionary
        # Handle Document objects
        if isinstance(obj, Document):
            return obj.to_dict()  # Convert Document to dictionary

        # Handle non-serializable objects
        if isinstance(obj, (set, bytes)):
            return list(obj)  # Convert sets and bytes to lists
        if hasattr(obj, 'tolist'):
            return obj.tolist()  # Convert numpy arrays or similar objects to lists
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()  # Convert datetime objects to ISO format strings
        # Call the default method for other types
        return super().default(obj)

def search_query(query):
    global pipeline
    try:
        result = pipeline.run(query=query, params={"Retriever": {"top_k": 1}, "Reader": {"top_k": 1}})
        
        # Write the result to a file for debugging
        with open(".\\trump_clip1_transcription\\pipeline_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)

        is_valid, message = validate_result_structure(result)
        if not is_valid:
            return {'message': 'Invalid result format'}

        # Extract the closest match and its starting timestamp
        if result['answers'] and len(result['answers']) > 0:
            closest_match = result['answers'][0]  # Assuming the closest match is the first answer
            answer_text = closest_match.answer if hasattr(closest_match, 'answer') else "No answer"
            
            # Add debug statement for closest_match
            print("closest_match:", closest_match)

            # Extract start time from context
            start_time = 0
            if hasattr(closest_match, 'context'):
                context = closest_match.context
                print("context:", context)  # Debugging line to see the context
                
                # Extract start time from context
                start_index = context.find('"start":')
                if start_index != -1:
                    start_index += len('"start":')
                    end_index = context.find(',', start_index)
                    start_time_str = context[start_index:end_index].strip()
                    start_time = float(start_time_str)

            # Prepare the formatted result
            formatted_result = {
                'answer': answer_text,
                'start': start_time,
                'documents': [{'content': answer_text}]
            }

            # Write the formatted result to a file for debugging
            with open(".\\trump_clip1_transcription\\formatted_result.json", "w", encoding="utf-8") as f:
                json.dump(formatted_result, f, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)

            return formatted_result
        else:
            return {'message': 'No match found'}

    except Exception as e:
        print("Error in search_query:", str(e))
        return {'message': 'Error processing query'}


def load_document_store(file_path):
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None

def initialize_document_store():
    document_store = InMemoryDocumentStore()
    retriever = DensePassageRetriever(document_store=document_store)
    reader = FARMReader(model_name_or_path="distilbert-base-uncased-distilled-squad", use_gpu=False)
    pipeline = ExtractiveQAPipeline(reader, retriever)
    return document_store, retriever, pipeline

def setup_pipeline(ps_file_path, ds_file_path):
    global pipeline
    document_store = load_document_store(ds_file_path)
    if document_store is None:
        document_store, retriever, pipeline = initialize_document_store()
        processed_segments = load_data(ps_file_path)
        index_data(processed_segments, document_store, retriever)
        with open(ds_file_path, 'wb') as f:
            pickle.dump(document_store, f)
    else:
        retriever = DensePassageRetriever(document_store=document_store)
        reader = FARMReader(model_name_or_path="distilbert-base-uncased-distilled-squad", use_gpu=False)
        pipeline = ExtractiveQAPipeline(reader, retriever)

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Index processed segments and configure search pipeline.")
    parser.add_argument("processed_segments_path", type=str, help="Path to the processed segments JSON file")
    parser.add_argument("document_store_dir", type=str, help="Directory to store the document store file")
    args = parser.parse_args()

    # Ensure the document store directory exists
    if not os.path.exists(args.document_store_dir):
        os.makedirs(args.document_store_dir)

    # Define the document store file path
    document_store_path = os.path.join(args.document_store_dir, 'document_store.pkl')

    # Print paths for debugging
    print(f"Processed segments path: {args.processed_segments_path}")
    print(f"Document store path: {document_store_path}")

    setup_pipeline(args.processed_segments_path, document_store_path)
    

if __name__ == "__main__":
    main()
