import re
import time
from urllib.parse import urljoin, urlparse

import tldextract
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Regex patterns
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
)

OBFUSCATED_REGEX = re.compile(
    r"([a-zA-Z0-9._%+-]+)\s*(?:\[at\]|\(at\)|at)\s*"
    r"([a-zA-Z0-9.-]+)\s*(?:\[dot\]|\(dot\)|dot|\.)\s*"
    r"([a-zA-Z]{2,})",
    re.IGNORECASE
)

def normalize_url(url):
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

def crawl_all_pages(start_url, max_pages=500):
    driver = setup_driver()

    visited = set()
    to_visit = [start_url]
    emails = set()

    base_domain = tldextract.extract(start_url).registered_domain

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        visited.add(url)
        print(f"Crawling: {url}")

        try:
            driver.get(url)
            time.sleep(2)  # allow JS to load

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # Extract normal emails
            emails.update(EMAIL_REGEX.findall(html))

            # Extract obfuscated emails
            for match in OBFUSCATED_REGEX.findall(html):
                emails.add(f"{match[0]}@{match[1]}.{match[2]}")

            # Find all internal links
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                parsed = urlparse(link)

                if parsed.scheme not in ("http", "https"):
                    continue

                domain = tldextract.extract(link).registered_domain
                if domain == base_domain:
                    clean_link = link.split("#")[0].rstrip("/")
                    if clean_link not in visited:
                        to_visit.append(clean_link)

        except Exception:
            continue

    driver.quit()
    return sorted(emails), len(visited)

if __name__ == "__main__":
    website = input("Enter company website (example.com): ").strip()
    website = normalize_url(website)

    print("\nStarting full site crawl...\n")
    emails, pages = crawl_all_pages(website)


    print("\nCrawl completed.")
    print(f"Pages crawled: {pages}")

    if emails:
        print("\nEmails found:")
        for email in emails:
            print(email)
    else:
        print("\nNo emails found on the website.")

