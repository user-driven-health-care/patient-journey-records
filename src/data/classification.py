import csv
import re
import os
import glob
import requests
from bs4 import BeautifulSoup

# Define keywords that indicate a cardiac case.
CARDIAC_KEYWORDS = [
    'heart', 'cardiac', 'ECG', 'electrocardiogram', 'chest pain',
    'myocardial', 'arrhythmia', 'heart failure', 'angina', 'palpitations'
]

def extract_section(text, section_title):
    """
    Extracts content from a section starting with the given section_title.
    Assumes section titles are followed by a colon or newline.
    """
    pattern = rf"{section_title}[:\n](.*?)(?=\n[A-Z][a-z]+[:\n]|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def extract_blog_text(url):
    """
    Fetches a blog post from the given URL and extracts the main text content.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for common Blogspot content containers.
    content_div = soup.find('div', class_='post-body') or soup.find('div', class_='entry-content')
    if not content_div:
        content_div = soup.find('article')
    if not content_div:
        print(f"Main content not found in {url}.")
        return ""
    
    # Remove unwanted elements such as scripts and styles.
    for tag in content_div.find_all(['script', 'style']):
        tag.decompose()
    
    text = content_div.get_text(separator='\n', strip=True)
    
    return text

def classify_case(text):
    """
    Classifies the case as 'cardiac' or 'non-cardiac' by focusing on specific sections
    such as 'Diagnosis', 'Introduction', or 'Case History'.
    """
    # First, try to extract the 'Diagnosis' section.
    diagnosis_text = extract_section(text, "Diagnosis")
    
    # If not found, try 'Introduction' then 'Case History'.
    if not diagnosis_text:
        diagnosis_text = extract_section(text, "Introduction")
    if not diagnosis_text:
        diagnosis_text = extract_section(text, "Case History")
    
    # Use the section text if available; otherwise, fall back to the full text.
    search_text = diagnosis_text if diagnosis_text else text.lower()
    
    for keyword in CARDIAC_KEYWORDS:
        if keyword.lower() in search_text.lower():
            return 'cardiac'
    return 'non-cardiac'

def process_blogposts_from_csv(input_csv_path):
    """
    Reads blogpost URLs from an input CSV file, extracts and classifies the content,
    and returns a list of results.
    
    Parameters:
        input_csv_path (str): Path to the input CSV file (one URL per row).
        
    Returns:
        list: A list of [URL, classification] results.
    """
    results = []
    with open(input_csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if not row:
                continue
            url = row[0].strip()
            print(f"Processing: {url}")
            content = extract_blog_text(url)
            classification = 'unknown' if not content else classify_case(content)
            results.append([url, classification])
    return results

def process_csv(input_csv_path, output_csv_path):
    print(f"Reading from file: {input_csv_path}")
    results = process_blogposts_from_csv(input_csv_path)
    # Write compiled results to the output CSV file.
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['URL', 'Classification'])
        writer.writerows(results)
    
    print(f"All classifications complete. Results saved to {output_csv_path}.")

# Example usage:
if __name__ == "__main__":
    input_csv = "src\data\links\\blogpost_links.csv"  
    output_csv = "src\data\links\classified_blogpost_links.csv"  # Output CSV file with all classifications
    process_csv(input_csv, output_csv)
