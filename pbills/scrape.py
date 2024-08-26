import requests
from bs4 import BeautifulSoup
import json
import time
import os

BASE_URL = "http://parliament.go.ke"
DOCUMENT_LIST_URL = f"{BASE_URL}/the-national-assembly/house-business/bills"
FULL_LIST_PATH = r"pbills/full_list.json" 

def load_existing_data():
    """Load the existing data from full_list.json."""
    if os.path.exists(FULL_LIST_PATH):
        with open(FULL_LIST_PATH, "r") as f:
            return json.load(f)
    return []

def extract_document_data(row):
    """Extract document data from a table row."""
    document_data = {}
    try:
        link_tag = row.find("td", {"class": "views-field views-field-nothing"}).find("a", href=True)
        document_data["pdf_url"] = link_tag["href"] if link_tag else "Unknown"
        document_data["title"] = link_tag.text.strip() if link_tag else "Unknown"
    except AttributeError:
        print(f"Error processing row: {row}")
        document_data["pdf_url"] = "Unknown"
        document_data["title"] = "Unknown"
    return document_data

def document_exists(document, existing_documents):
    """Check if a document already exists in the existing data."""
    for existing_document in existing_documents:
        if document["pdf_url"] == existing_document["pdf_url"]:
            return True
    return False

def get_document_list(existing_documents):
    """Fetch the list of documents from the website and check if they exist."""
    document_list = []
    page = 0
    while True:
        response = requests.get(f"{DOCUMENT_LIST_URL}?page={page}")
        if response.status_code != 200:
            print(f"Failed to retrieve page {page}")
            break
        soup = BeautifulSoup(response.content, "html.parser")
        rows = soup.find_all("tr")
        if not rows:
            break
        for row in rows:
            document_data = extract_document_data(row)
            if not document_exists(document_data, existing_documents):
                document_list.append(document_data)
        print(f"Scraped page {page} of documents")
        page += 1
        time.sleep(2)  # Be polite and avoid overwhelming the server
    return document_list

def main():
    """Main function to fetch and save the document list."""
    existing_documents = load_existing_data()
    new_documents = get_document_list(existing_documents)

    if new_documents:
        # Update the existing data with the new documents
        existing_documents.extend(new_documents)
        with open(FULL_LIST_PATH, "w") as f:
            json.dump(existing_documents, f, indent=4)
        print(f"Added {len(new_documents)} new documents to {FULL_LIST_PATH}")
    else:
        print("No new documents found.")

if __name__ == "__main__":
    main()
