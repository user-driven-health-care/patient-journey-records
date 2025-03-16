import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os
from groq import Groq

OUTPUT_DIR = "src\data\Jsons\temporal"

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
    Given the following medical case blog content, extract a timeline of events in JSON format.
    Each timeline entry should have: ordinal (number), time (specific time mentioned), useractivity (what happened), 
    symptom (any symptoms mentioned), diagnosis (any diagnoses), and treatment (any treatments).
    
    Use ONLY information explicitly stated in the content. If a field has no information, leave it as an empty string.
    Start a new timeline entry ONLY when a new time frame is mentioned.
    Use the exact medical terminology and descriptions from the text.
    Once the results are ready, think step by step and make sure the the 'time' parameter in timeline is strictly ascending. Reorder the 'ordinal' entries if necessary. 
    
    Blog content:
    {content}
    
    Format the response as a valid JSON array of timeline entries like this:
    ```json
    [
      {{"ordinal": 1, "time": "specific time mentioned", "useractivity": "what happened", "symptom": "symptoms mentioned", "diagnosis": "diagnoses mentioned", "treatment": "treatments mentioned"}},
      ...
    ]
    ```
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
    url = input("Enter the blog post URL: ")
    case_data = generate_case_json(url)
    filename = filename = os.path.join(OUTPUT_DIR, f"{url.split('/')[-1].split('.')[0]}_case.json")
    save_json_to_file(case_data, filename)
    print("\nGenerated JSON:\n")
    print(json.dumps(case_data, indent=2))

if __name__ == "__main__":
    main()