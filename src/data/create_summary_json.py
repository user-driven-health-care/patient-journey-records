import requests
import json
import csv
import time
import re
import ollama
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# Fields to extract
FIELDS = {
    "AGE": "<Extracted age as an integer>",
    "GENDER": "<Male/Female/Other>",
    "APPETITE": "<Normal/Reduced/Increased/Not mentioned>",
    "DIET": "<Vegetarian/Non-Vegetarian/Mixed/Not mentioned>",
    "BOWEL AND BLADDER MOVEMENTS": "<Regular/Irregular/Constipation/Diarrhea/Not mentioned>",
    "PERSONAL HISTORY": "<Summary of personal details>",
    "SLEEP": "<Adequate/Inadequate/Insomnia/Not mentioned>",
    "ADDICTIONS": "<List all substance use like alcohol, tobacco, drugs>",
    "FAMILY HISTORY": "<Mention significant hereditary diseases or write 'Not significant'>",
    "GENERAL EXAMINATION": "<Brief summary of general health findings>",
    "TEMPERATURE": "<In Celsius or Fahrenheit, or 'Afebrile' if normal>",
    "PULSE RATE": "<Extracted value in bpm>",
    "BLOOD PRESSURE": "<Extracted value in mmHg>",
    "RESPIRATORY RATE": "<Extracted value in breaths per minute>",
    "SPO2": "<Extracted value in percentage>",
    "GRBS": "<Extracted glucose level in mg/dl>",
    "JVP": "<Extracted value or 'Not mentioned'>",
    "SYSTEMIC EXAMINATION": {
        "CVS": "<Cardiovascular findings>",
        "RS": "<Respiratory system findings>",
        "ABDOMEN": "<Findings related to the abdomen in text>",
        "CNS": "<Finding related to Central nervous system in text>"
    },
    "DIAGNOSIS": "<Final diagnosis based on findings in text>",
    "TREATMENT": "<List of medications with dosage in text>"
}


# Output directory for JSON files
OUTPUT_DIR = "src\data\Jsons\summary"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_blog_content(url):
    """Fetches and extracts text from a medical case blog URL."""
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract text from headings (h1-h6) and paragraphs (p)
        text = "\n".join(tag.get_text() for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span']))
        print(text)
        return text if text else "No text found."
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the blog: {e}")
        return "" 

def extract_medical_info(text):
    """Uses Phi-3.5 to extract structured medical data."""
    prompt = f"""
    Extract the following medical parameters from the given text. Ensure that the extracted values are accurate and formatted properly. Return the output strictly as a JSON object with the following keys:
    {FIELDS}

    **Rules:**
    1. Do not generate null values. If a value is missing, return `"Not mentioned"` instead.
    2. Strictly return **only** a valid JSON object, do not add explanations or extra formatting.
    3. Extract the values **directly from the text** without reinterpreting them.
    4. Ensure units are consistent (bpm for pulse, mmHg for BP, mg/dl for glucose, etc.).
    5. If no information is available for a section, return `"Not mentioned"` instead of `null`.
    6. Do not change keys.

    Text:
    {text}

    JSON Output:
    """

    response = ollama.chat(model='mistral', messages=[{"role": "user", "content": prompt}])

    # Extract only the JSON part
    content = response['message']['content'].strip()

    try:
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        json_content = content[json_start:json_end]

        return json.loads(json_content)
    except json.JSONDecodeError:
        print("Error parsing Phi-3.5 response. Raw response:", content)
        return {}

def create_json(url):
    """Processes a blog URL, extracts case details, and saves as JSON."""
    case_text = extract_blog_content(url)
    if not case_text or case_text == "No text found.":
        print(f"No valid case data found for {url}")
        return None

    extracted_data = extract_medical_info(case_text)
    
    if extracted_data and any(value != "Not mentioned" for value in extracted_data.values()):
        filename = os.path.join(OUTPUT_DIR, f"{url.replace('https://', '').replace('/', '_')}.json")
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(extracted_data, file, indent=4)
        print(f"Saved extracted data to {filename}")
    else:
        print(f"No relevant medical data extracted for {url}. Skipping save.")

    return extracted_data

def process_csv(input_csv):
    """Reads a CSV containing blog URLs and processes them one by one."""
    with open(input_csv, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header

        for row in reader:
            if row:
                url = row[0]
                print(f"Processing: {url}")
                create_json(url)
                time.sleep(2)  # Pause to avoid getting blocked

if __name__ == "__main__":
    csv_filename = "src\data\links\\blogpost_links.csv"  # Update with actual CSV file
    process_csv(csv_filename)
