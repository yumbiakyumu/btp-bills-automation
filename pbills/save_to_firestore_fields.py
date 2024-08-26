import firebase_admin
from firebase_admin import credentials, firestore, storage
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
import time
import random
import json
from google.api_core.exceptions import DeadlineExceeded 
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Import functions from adding.py
from adding import generate_description, generate_positives, generate_negatives, extract_date, clean_text

# Load environment variables
# load_dotenv()  # Uncomment if you're using a .env file locally

# Initialize Firebase Admin SDK with credentials from the environment variable
firebase_credentials = os.getenv('FIREBASE_CREDENTIALS')  # This should be the entire JSON string
if firebase_credentials is None:
    raise ValueError("FIREBASE_CREDENTIALS environment variable is not set.")

# Parse the JSON string into a dictionary
cred_dict = json.loads(firebase_credentials)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {"storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET')})
# Get Firestore client
db = firestore.client()

# Get Storage bucket
bucket = storage.bucket()

def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def fetch_text_from_url(session, text_url):
    try:
        response = session.get(text_url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching text from {text_url}: {str(e)}")
        return None

def load_last_processed(file_name):
    try:
        with open(file_name, 'r') as file:
            data = json.load(file)
            return data.get('last_processed_doc')
    except FileNotFoundError:
        return None

def save_last_processed(doc_id, file_name):
    with open(file_name, 'w') as file:
        json.dump({'last_processed_doc': doc_id}, file)

# Create a session for reuse
session = create_session()

# Fetch the sbills collection
sbills_ref = db.collection('pbills')
last_processed_doc = load_last_processed('pbills/last_processed_pbills.json')
sbills_docs = sbills_ref.stream()

# Process documents in batches
batch_size = 10
docs_processed = 0
docs_to_update = []
start_processing = last_processed_doc is None

print(f"Starting processing from document: {last_processed_doc}")

while True:
    try:
        for doc in sbills_docs:
            print(f"Checking document: {doc.id}")

            if not start_processing and doc.id == last_processed_doc:
                start_processing = True
                print(f"Resuming processing after last processed document: {last_processed_doc}")
                continue
            
            if not start_processing:
                print(f"Skipping document: {doc.id}")
                continue
            
            doc_id = doc.id
            bill = doc.to_dict()

            print(f"Processing document: {doc_id}")

            # Only proceed if description, positives, negatives, or date are missing
            if not all(key in bill for key in ["description", "positives", "negatives", "date"]):
                text_url = bill.get("text_url")
                if text_url:
                    # Fetch the text from the URL
                    text_content = fetch_text_from_url(session, text_url)
                    
                    if text_content:
                        # Clean the text
                        cleaned_text = clean_text(text_content)
                        
                        # Generate description, positives, and negatives using OpenAI's GPT model
                        if "description" not in bill:
                            bill["description"] = generate_description(cleaned_text)
                        if "positives" not in bill:
                            bill["positives"] = generate_positives(cleaned_text)
                        if "negatives" not in bill:
                            bill["negatives"] = generate_negatives(cleaned_text)
                        
                        # Extract a relevant date
                        if "date" not in bill:
                            bill["date"] = extract_date(cleaned_text)
                        
                        # Add to batch update list
                        docs_to_update.append((doc_id, bill))
                        docs_processed += 1

                        print(f"Document {doc_id} queued for update.")
                        
                        # Check if we've reached the batch size
                        if docs_processed >= batch_size:
                            # Perform the updates
                            for doc_id, updated_bill in docs_to_update:
                                sbills_ref.document(doc_id).update(updated_bill)
                                print(f"Document {doc_id} updated with new fields.")
                                save_last_processed(doc_id, 'last_processed_pbills.json')
                            
                            # Reset for next batch
                            docs_to_update = []
                            docs_processed = 0
                            
                            # Sleep to prevent overwhelming servers
                            sleep_time = random.uniform(2, 5)
                            print(f"Sleeping for {sleep_time} seconds...")
                            time.sleep(sleep_time)
                    else:
                        print(f"Failed to fetch text for document {doc_id}.")
                else:
                    print(f"No text URL found for document {doc_id}.")
            else:
                print(f"Document {doc_id} already has all fields.")
        
        # Perform updates for any remaining documents
        for doc_id, updated_bill in docs_to_update:
            sbills_ref.document(doc_id).update(updated_bill)
            print(f"Document {doc_id} updated with new fields.")
            save_last_processed(doc_id, 'last_processed_pbills.json')
        
        print("All documents have been processed and updated.")
        break
    except DeadlineExceeded as e:
        print("Deadline exceeded. Retrying...")
        time.sleep(5)
        sbills_docs = sbills_ref.stream() 
        continue
