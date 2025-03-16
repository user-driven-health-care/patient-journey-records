import requests
import csv
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

OUTPUT_DIR = "src\data\links"

def extract_filtered_blogspot_links(url):
    """Extracts filtered blogspot links from a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP request errors
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(url, href)  # Construct full URL

            # Keep links that contain 'blogspot.com' but exclude 'classworkdecjan.blogspot.com'
            if "blogspot.com" in full_url and "classworkdecjan.blogspot.com" not in full_url:
                links.append(full_url)

        return links

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL {url}: {e}")
        return []

def collect_all_blogspot_links(base_url, start_page, end_page):
    """Collects links from multiple blog pages within the given range."""
    all_links = []
    for i in range(start_page, end_page + 1):
        url = base_url.format(i)
        links = extract_filtered_blogspot_links(url)
        all_links.extend(links)
        print(all_links)
    return all_links

def save_links(links, output_dir="src/data/links"):
    """Saves all links in a single CSV file without overwriting."""
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists
    filename = os.path.join(output_dir, "blogpost_links.csv")

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Links"])  # Add header
        writer.writerows([[link] for link in links])  # Write all links

    print(f"Saved {len(links)} links to {filename}")

def main():
    base_url = "https://classworkdecjan.blogspot.com/2022/02/udhc-cases-mirror-{}.html"
    start_page = 2
    end_page = 5

    print("Collecting blogspot links...")
    links = collect_all_blogspot_links(base_url, start_page, end_page)

    if links:
        print(f"Total {len(links)} links collected.")
        save_links(links, OUTPUT_DIR)
    else:
        print("No links found.")

if __name__ == "__main__":
    main()

