import requests
from bs4 import BeautifulSoup
import os
import pandas as pd

def download_image(url, folder_path):
    try:
        response = requests.get(url)
        filename = os.path.join(folder_path, os.path.basename(url))
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def download_images_from_article(url, folder_path):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all(attrs={'class':'post-outer-container'})        
        for article in articles:
            imgs = article.find_all('img')
            for img in imgs:
                img_url = img.get('src')
                if img_url:
                    download_image(img_url, folder_path)
    except Exception as e:
        print(f"Error downloading images from {url}: {e}")
        
def extract_text_from_article(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')
        for article in articles:
            article_text = article.get_text(separator='\n')
            return article_text
    except Exception as e:
        print(f"Error extracting text from {url}: {e}")
        return f"Error extracting text from {url}: {e}"


fr = open("unique_date_link.txt", 'r')
links = fr.readlines()
count = 1
urls = []
url_text = []
for bloglink in links:
    url = bloglink.strip()
    print(url)
    folder_path = f'F:\medical_data\downloaded_images\{count}'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    download_images_from_article(url, folder_path)
    text = extract_text_from_article(url)
    urls.append(url)
    url_text.append(text)
    count = count + 1

dict = {'URL': urls, 
        'text': url_text 
       } 
  
df = pd.DataFrame(dict) 

df.to_csv('F:\medical_data\data.csv')

fr.close()