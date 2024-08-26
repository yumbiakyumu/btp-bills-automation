# Bill Processing and Firestore Integration

This project provides a pipeline to process bill texts using OpenAI's GPT model and store the results in a Firestore database. It consists of two main scripts:

1. **adding.py**: Contains functions to generate descriptions, positives, negatives, and extract dates from bill texts.
2. **save_to_firestore.py**: Fetches bill texts, processes them using the functions from `adding.py`, and updates the Firestore database.

## Setup

1. **Install Dependencies**
   ```bash
   pip install openai firebase-admin requests

# Configure Firebase

- Obtain a Firebase service account key and save it .
- Place the JSON file in the project directory.

# OpenAI API Key

- Set up your OpenAI API key in the `adding.py` file.

# Files and Functions

## adding.py

- `generate_description(bill_text)`: Generates a short description for the bill using OpenAI's GPT model.
- `clean_text(text)`: Cleans the text by removing unwanted characters.
- `generate_positives(bill_text)`: Generates a list of positive aspects of the bill.
- `generate_negatives(bill_text)`: Generates a list of negative aspects of the bill.
- `extract_date(bill_text)`: Extracts a relevant date from the bill text.

## save_to_firestore.py

- `create_session()`: Creates a reusable HTTP session with retries.
- `fetch_text_from_url(session, text_url)`: Fetches bill text from a given URL.
- `load_last_processed(file_name)`: Loads the last processed document ID from a JSON file.
- `save_last_processed(doc_id, file_name)`: Saves the last processed document ID to a JSON file.

### Processing Logic:

- Fetches documents from the Firestore `sbills` collection.
- Processes each document to generate description, positives, negatives, and date.
- Updates the Firestore documents with the generated data.

# Usage

## Run the save_to_firestore.py Script

```bash
python -u "path_to_your_script/save_to_firestore.py"

## Notes

- Ensure the Firestore database and storage bucket are properly configured.
- Adjust the batch size and sleep time in `save_to_firestore.py` as needed to manage API rate limits and server load.

## Troubleshooting

- If processing stops unexpectedly, check the `last_processed_sbills.json` file to see the last processed document ID.
- Delete or reset the `last_processed_sbills.json` file to reprocess documents from the beginning.