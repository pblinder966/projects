import requests
from flask import Flask, render_template

app = Flask(__name__)

api = "QSas7AliP7GS9Kn0uVtfb6IaZP0KjBw2NxZAyMc9"

url = f"https://api.nasa.gov/neo/rest/v1/feed?api_key={api}"

@app.route('/<date>')
def specificdate(date):
    response = requests.get(url + "&start_date=" + date + "&end_date=" + date)

    if response.status_code == 200:
        nasadata = response.json()
        return render_template("index.html", data=nasadata)

@app.route('/')
def main():
    response = requests.get(url)

    if response.status_code == 200:
        nasadata = response.json()
        return render_template("index.html", data=nasadata)

if __name__ == "__main__":
    app.run(debug=True)