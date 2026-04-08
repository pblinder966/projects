from flask import Flask, render_template, request, send_file
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def is_internal(base, link):
    return urlparse(base).netloc == urlparse(link).netloc

def crawl_site(base_url, max_pages=15):
    visited = set()
    queue = [base_url]
    emails_found = set()

    while queue and len(visited) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue

        visited.add(url)

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
        except:
            continue

        text = soup.get_text()
        emails = re.findall(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            text
        )
        emails_found.update(emails)

        for a in soup.find_all("a", href=True):
            link = urljoin(base_url, a["href"])
            if is_internal(base_url, link) and link not in visited:
                queue.append(link)

    return emails_found


@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    file_ready = False

    if request.method == "POST":
        file = request.files["excel_file"]
        df = pd.read_excel(file)
        df["Emails_Found"] = ""

        for i, row in df.iterrows():
            url = row["Company_URL"]
            emails = crawl_site(url)

            if emails:
                email_str = ", ".join(emails)
                df.at[i, "Emails_Found"] = email_str
                results.append({"url": url, "emails": email_str})
            else:
                df.at[i, "Emails_Found"] = "No email found"
                results.append({"url": url, "emails": "No email found"})

        df.to_excel("output.xlsx", index=False)
        file_ready = True

    return render_template(
        "index.html",
        results=results,
        file_ready=file_ready
    )


@app.route("/download")
def download():
    return send_file("output.xlsx", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
