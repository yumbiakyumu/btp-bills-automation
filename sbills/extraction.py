import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen
from io import BytesIO
from pdf2image import convert_from_bytes
import pytesseract
from tqdm import tqdm

# Function to extract text from a scanned PDF URL
def extract_text_from_pdf(pdf_url):
    try:
        with urlopen(pdf_url) as response:
            pdf_content = BytesIO(response.read())

        # Convert PDF to images
        images = convert_from_bytes(pdf_content.read())

        text = ""
        for image in images:
            # Use pytesseract to do OCR on the image
            text += pytesseract.image_to_string(image) + "\n"

        return text.strip()
    except Exception as e:
        print(f"Error processing {pdf_url}: {str(e)}")
        return ""

# Load the JSON data from full_list.json and processed_list.json
with open("sbills/sen_full_list.json", "r") as f:
    full_list = json.load(f)

with open("sbills/sen_processed_list.json", "r") as f:
    processed_list = json.load(f)

# Create sets of titles for each list
full_titles = set(bill['title'] for bill in full_list if bill['title'] != "Unknown")
processed_titles = set(bill['title'] for bill in processed_list if bill['title'] != "Unknown")

# Find the difference between the two sets (bills in full_list but not in processed_list)
difference_titles = full_titles - processed_titles

# Print the number of bills in full_list but not in processed_list
count = len(difference_titles)
print(f"Number of bills in sen_full_list but not in processed_list: {count}")

# Print the titles of these bills
print("\nTitles of bills not in sen_processed_list:")
for title in difference_titles:
    print(title)

# Filter full_list to only include bills that are not in processed_list and skip "Unknown" entries
bills_to_process = [
    bill for bill in full_list
    if bill['title'] in difference_titles and bill['pdf_url'] != "Unknown" and bill['title'] != "Unknown"
]

# Create a ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=6) as executor:
    # Submit tasks and store futures
    future_to_bill = {
        executor.submit(extract_text_from_pdf, bill["pdf_url"]): bill for bill in bills_to_process
    }

    # Process completed tasks with progress bar
    for future in tqdm(
        as_completed(future_to_bill), total=len(bills_to_process), desc="Extracting text"
    ):
        bill = future_to_bill[future]
        try:
            bill["text"] = future.result()
        except Exception as e:
            print(f"Error processing {bill['pdf_url']}: {str(e)}")
            bill["text"] = ""

# Append the pdf_url and title of the processed bills to processed_list.json
for bill in bills_to_process:
    processed_list.append({"pdf_url": bill["pdf_url"], "title": bill["title"]})

# Save the updated processed_list to a JSON file
processed_list_path = r"sbills\sen_processed_list.json"
with open(processed_list_path, "w", encoding="utf-8") as f:
    json.dump(processed_list, f, ensure_ascii=False, indent=2)

# Save the extracted data to a JSON file
output_path = "sbills\sen-bills.json"

# Check if any bills were processed
if bills_to_process:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bills_to_process, f, ensure_ascii=False, indent=2)
else:
    # If no bills were processed, create an empty JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([], f)


print(f"Extraction complete. Data saved to {output_path}")
print(f"Processed list updated. Data saved to {processed_list_path}")
