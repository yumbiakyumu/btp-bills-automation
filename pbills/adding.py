import openai
import re
import os
from dotenv import load_dotenv

# Load environment variables from the .env file (if needed for local testing)
# load_dotenv()

# Set up OpenAI API key
openai_api_key = os.getenv('OPENAIKEY')  # Ensure this matches the secret name in GitHub
if openai_api_key is None:
    raise ValueError("OPENAI_KEY environment variable is not set.")

openai.api_key = openai_api_key

def generate_description(bill_text):
    """Generate a short description for the bill using OpenAI's GPT model."""
    truncated_text = bill_text[:3000]
    
    response = openai.ChatCompletion.create(
        model="gpt-4",  # Ensure the model name is correct
        messages=[
            {"role": "user", "content": f"Generate a description of less than 23 words for the following bill (do not start with the bill name or Kenyan bill): {truncated_text}"}
        ],
        temperature=0.2 
    )
    return response['choices'][0]['message']['content'].strip()

def clean_text(text):
    """Remove leading/trailing whitespace, numbers, and unwanted symbols from the text."""
    # Remove leading/trailing whitespace and specific symbols
    text = re.sub(r'^\s*\*\*\s*|\s*\*\*\s*$|^\d+\.\s*', '', text)  
    text = re.sub(r'^\*\*', '', text)  
    return text.strip()

def format_entry(entry):
    """Format a single positive or negative entry."""
    if ':' in entry and '.' in entry:
        title, explanation = entry.split(':', 1)
        explanation = explanation.split('.')[0].strip()  # Get text before the first period
        return {
            "title": clean_text(title.strip()),  # Clean title
            "explanation": clean_text(explanation.strip())  # Clean explanation
        }
    else:
        return {"title": "", "explanation": ""}  # Return empty dictionary if format is incorrect

def generate_positives(bill_text):
    """Generate 10 positives for the bill using OpenAI's GPT model."""
    truncated_text = bill_text[:3000]
    
    response = openai.ChatCompletion.create(
        model="gpt-4",  
        messages=[
            {"role": "user", "content": f"Generate 10 concise positives in the format 'Short title (4 to 5 words) : explanation (not more than 30 words).' relevant to the following bill: {truncated_text}"}
        ],
        temperature=0.2 
    )
    
    # Process the response to extract and format positives
    positives = response['choices'][0]['message']['content'].strip().split('\n')
    formatted_positives = [format_entry(pos) for pos in positives if format_entry(pos)["title"] and format_entry(pos)["explanation"]]  # Ensure valid entries
    
    # Ensure we have exactly 10 positives, filling with empty dictionaries if necessary
    while len(formatted_positives) < 10:
        formatted_positives.append({"title": "", "explanation": ""})  # Placeholder for missing positives
    
    return formatted_positives  # Return formatted positives

def generate_negatives(bill_text):
    """Generate 10 negatives for the bill using OpenAI's GPT model."""
    truncated_text = bill_text[:3000]
    
    response = openai.ChatCompletion.create(
        model="gpt-4", 
        messages=[
            {"role": "user", "content": f"Generate 10 concise negatives in the format 'Short title (4 to 5 words) : explanation (not more than 30 words).' relevant to the following bill: {truncated_text}"}
        ],
        temperature=0.2  
    )
    
    # Process the response to extract and format negatives
    negatives = response['choices'][0]['message']['content'].strip().split('\n')
    formatted_negatives = [format_entry(neg) for neg in negatives if format_entry(neg)["title"] and format_entry(neg)["explanation"]]  # Ensure valid entries
    
    # Ensure we have exactly 10 negatives, filling with empty dictionaries if necessary
    while len(formatted_negatives) < 10:
        formatted_negatives.append({"title": "", "explanation": ""})  # Placeholder for missing negatives
    
    return formatted_negatives  # Return formatted negatives

def extract_date_with_model(bill_text):
    """Use the model to extract the relevant date associated with the bill."""
    truncated_text = bill_text[:3000]

    response = openai.ChatCompletion.create(
        model="gpt-4", 
        messages=[
            {"role": "user", "content": f"Extract the relevant date from the following bill text. Return only the date without any additional text: {truncated_text}"}
        ],
        temperature=0.2  
    )
    
    return response['choices'][0]['message']['content'].strip()

def extract_date(bill_text):
    """Extract a relevant date associated with the bill."""
    date_from_model = extract_date_with_model(bill_text)
    if date_from_model:
        return date_from_model  # Return the date found by the model
    return "Unknown"  # Return "Unknown" if no date was found

def process_bill(bill):
    """Process a single bill, adding description, positives/negatives, and date if not already present."""
    bill_text = bill.get("text", "")
    if bill_text:
        if not bill.get("description"):
            bill['description'] = generate_description(bill_text)
        if not bill.get("positives"):
            bill['positives'] = generate_positives(bill_text)
        if not bill.get("negatives"):
            bill['negatives'] = generate_negatives(bill_text)
        if not bill.get("date"):
            bill['date'] = extract_date(bill_text)
    return bill