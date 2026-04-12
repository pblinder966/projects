from flask import Flask, render_template, request
from model import search_query

app = Flask(__name__)
@app.route("/", methods=["GET", "POST"])
def home():
    results = None
    query = ""
    if request.method == "POST":
        query = request.form.get("query")
        if query:
            results = search_query(query)
    return render_template("index.html", results=results, query=query)
if __name__ == "__main__":
    app.run(debug=True)