import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_html_links(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'xml')
        links = soup.find_all('loc')
        html_links = []
        for link in links:
            href = link.text
            if href.endswith('.html'):
                html_links.append(href)
        return html_links
    except Exception as e:
        print("Error occurred:", e)
        return []

def get_sitemap_url(url):
    try:
        response = requests.get(url + "/robots.txt")
        lines = response.text.split("\n")
        for line in lines:
            if line.startswith("Sitemap:"):
                return line.split(": ")[1].strip()
    except Exception as e:
        print("Error occurred while retrieving robots.txt:", e)
    return None

if __name__ == "__main__":
    fr = open("unique_links.txt", 'r')
    fw = open("unique_date_link.txt", 'w')
    links = fr.readlines()
    for bloglink in links:
        start_url = bloglink.strip()
        print(start_url)
        sitemap_url = get_sitemap_url(start_url)
        if sitemap_url:
            print("Sitemap found:", sitemap_url)
            html_links = extract_html_links(sitemap_url)
            print("HTML links in sitemap:")
            for link in html_links:
                fw.write(link+'\n')
                print(link)
        else:
            print("Sitemap not found.")
    fr.close()
    fw.close()