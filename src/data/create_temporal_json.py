import os
import re
import csv
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from groq import Groq

OUTPUT_DIR = "src\\data\\Jsons\\temporal"

def extract_blog_content(url):
    """Extract the content from a blog post URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        content = ""
        if "blogspot.com" in url:
            post_body = soup.find('div', class_='post-body')
            if post_body:
                content = post_body.get_text(separator=" ", strip=True)
            
            published_date = None
            date_element = soup.find('abbr', class_='published')
            if date_element and 'title' in date_element.attrs:
                published_date = date_element['title']
            else:
                time_element = soup.find('time')
                if time_element and 'datetime' in time_element.attrs:
                    published_date = time_element['datetime']
        else:
            article = soup.find('article') or soup.find('div', class_=re.compile('post|article|entry|content'))
            if article:
                content = article.get_text(separator=" ", strip=True)
            else:
                content = soup.get_text(separator=" ", strip=True)
        
        image_urls = []
        img_tags = soup.find_all('img')
        for img in img_tags:
            if 'src' in img.attrs:
                img_src = img['src']
                if not img_src.startswith(('http://', 'https://')):
                    base_url = '/'.join(url.split('/')[:3])
                    img_src = f"{base_url}/{img_src.lstrip('/')}"
                image_urls.append(img_src)
        
        return {'content': content, 'published_date': published_date, 'image_urls': image_urls}
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return None

def generate_timeline_with_groq(content):
    """Use Groq API with Llama 3 model to generate a structured timeline."""
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    prompt = f"""
    You are given a medical blog post containing one or more cardiac case studies. Your task is to extract structured data from this post in a temporal JSON format.
    1. Detect if the blog contains one or multiple case studies.
    2. For each case study, extract a metadata object with:
    - "url": the URL of the blog post
    - "datetime": publication date or stated date
    - "links": internal/external links
    - "additional_metadata": any extra non-timeline details
    3. For each case, extract a "timeline" array, with each entry like:
        {{
            "ordinal": 1,
            "time": "specific time mentioned",   // This field must not be empty and must be in an acceptable format 
            "activity": "what happened",
            "symptom": "symptoms mentioned",
            "diagnosis": "diagnoses mentioned",
            "treatment": "treatments mentioned",
            "notes": {{
                "demographics": "...",
                "physical_exam": "...",
                "investigations": "...",
                "lab_measurements": "...",
                "discussion": "..."
            }}
        }}
    4. Events must be sorted in chronological order and re-numbered accordingly.
    5. Leave empty strings for missing fields, except for "time" which must always have valid, explicit information (e.g., "on admission", "2 days before admission", "January 5, 2021").
    6. Use only explicitly stated text from the blog.
    Blog content:
    {content}
    Output the JSON structure only.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            max_tokens=4000,
            temperature=0,
        )
        
        response_content = chat_completion.choices[0].message.content
        json_pattern = r'\[\s*\{.*\}\s*\]'
        json_match = re.search(json_pattern, response_content, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group(0))
        
    except (KeyError, json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing JSON from Groq response: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return []


def generate_case_json(url):
    """Generate a structured JSON for a medical case from a blog URL."""
    blog_data = extract_blog_content(url)
    if not blog_data:
        return {"error": "Failed to extract blog content"}
    
    published_date = blog_data.get('published_date')
    formatted_datetime = datetime.now().strftime('%Y-%m-%dT%H:%M:%S-00:00')
    if published_date:
        for fmt in ('%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%d %H:%M:%S'):
            try:
                formatted_datetime = datetime.strptime(published_date, fmt).strftime('%Y-%m-%dT%H:%M:%S%z')
                break
            except ValueError:
                continue
    
    timeline = generate_timeline_with_groq(blog_data['content'])
    
    return {"metadata": {"url": url, "datetime": formatted_datetime}, "timeline": timeline, "imageurl": blog_data['image_urls']}

def save_json_to_file(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON saved to {filename}")

def main():
    input_file = "src\data\links\\test.csv"
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row['URL']
            case_data = generate_case_json(url)     # row 30
            filename = os.path.join(OUTPUT_DIR, f"{url.split('/')[-1].split('.')[0]}_case.json")
            save_json_to_file(case_data, filename)
            print("\nGenerated JSON:\n")
            print(json.dumps(case_data, indent=2))

if __name__ == "__main__":
    main()