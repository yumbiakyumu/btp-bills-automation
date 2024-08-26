import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
from dotenv import load_dotenv
import json
import random
import string
import requests
from urllib.parse import urlparse
import time
from requests.adapters import HTTPAdapter
from urllib3 import Retry

# Load environment variables from the .env file
load_dotenv()

# Initialize Firebase Admin SDK with credentials from the .env file
cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS'))
firebase_admin.initialize_app(cred, {"storageBucket": os.getenv('FIREBASE_STORAGE_BUCKET')})

# Get Firestore client
db = firestore.client()

# Get Storage bucket
bucket = storage.bucket()

# Load JSON data
with open("pbills/parliament-bills.json", "r", encoding="utf-8") as file:
    data = json.load(file)


def generate_unique_id():
    prefix = "pbill_"
    alphanumeric = string.ascii_lowercase + string.digits
    random_part = "".join(random.choice(alphanumeric) for _ in range(21))
    return prefix + random_part


def create_session():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def upload_pdf_to_storage(session, pdf_url, file_name):
    try:
        # Download the PDF
        response = session.get(pdf_url, timeout=30)
        response.raise_for_status()

        # Upload to Firebase Storage
        blob = bucket.blob(f"pbills/{file_name}")
        blob.upload_from_string(response.content, content_type="application/pdf")

        # Make the blob publicly accessible
        blob.make_public()

        return blob.public_url
    except requests.exceptions.RequestException as e:
        print(f"Error downloading or uploading PDF from {pdf_url}: {str(e)}")
        return None


# Create a session for reuse
session = create_session()

# Iterate through data and save to Firestore
for index, item in enumerate(data):
    # Generate a unique ID for each document
    doc_id = generate_unique_id()

    # Handle PDF
    if "pdf_url" in item:
        pdf_file_name = os.path.basename(urlparse(item["pdf_url"]).path)
        storage_pdf_url = upload_pdf_to_storage(session, item["pdf_url"], doc_id)
        if storage_pdf_url:
            item["pdf_url"] = storage_pdf_url
        else:
            print(f"Failed to upload PDF for document {doc_id}")

    # Handle large text content
    if "text" in item:
        text_content = item["text"]
        text_file_name = f"{doc_id}.txt"

        # Upload text content to Firebase Storage
        text_blob = bucket.blob(f"pbills_text/{text_file_name}")
        text_blob.upload_from_string(text_content, content_type="text/plain")
        text_blob.make_public()

        # Replace text content with the storage URL in the item
        item["text_url"] = text_blob.public_url
        del item["text"]  # Remove the text content from the main document

    # Get a reference to the document with the generated ID
    doc_ref = db.collection("pbills").document(doc_id)

    # Set the data for the document
    doc_ref.set(item)

    print(f"Document added with ID: {doc_id}")

    # Add a delay every 10 requests to avoid overwhelming the server
    if (index + 1) % 5 == 0:
        print("Pausing for 2 seconds...")
        time.sleep(2)

print("All documents have been added to Firestore.")