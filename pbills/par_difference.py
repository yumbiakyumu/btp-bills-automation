import json

# Read the full list of bills
with open('full_list.json', 'r') as f:
    full_list = json.load(f)

# Read the processed list of bills
with open('data-scrapper\pbills\processed_list.json', 'r') as f:
    processed_list = json.load(f)

# Create sets of titles for each list
full_titles = set(bill['title'] for bill in full_list)
processed_titles = set(bill['title'] for bill in processed_list)

# Find the difference between the two sets
difference = full_titles - processed_titles

# Count the number of bills in the difference
count = len(difference)

print(f"Number of bills in full_list but not in processed_list: {count}")

# Optionally, print the titles of these bills
print("\nTitles of bills not in processed_list:")
for title in difference:
    print(title)