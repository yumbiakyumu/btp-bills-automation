import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "http://parliament.go.ke"
DOCUMENT_LIST_URL = f"{BASE_URL}/the-senate/house-business/bills"

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

def get_document_list():
    """Fetch the list of documents from the website."""
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
            document_list.append(document_data)
        print(f"Scraped page {page} of documents")
        page += 1
        time.sleep(2)  # Be polite and avoid overwhelming the server
    return document_list

def main():
    """Main function to fetch and save the document list."""
    document_list = get_document_list()
    for document in document_list:
        print(document)

    # Optionally, save to a JSON file
    with open("sbills/sen_full_list.json", "w") as f:
        json.dump(document_list, f, indent=4)

if __name__ == "__main__":
    main()