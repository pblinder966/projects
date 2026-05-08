from flask import Flask, render_template, request, jsonify
import os
import numpy as np
import faiss
import re
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

app = Flask(__name__)


UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER



all_chunks = []
all_sources = []
all_toc = {}

index = None


model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_toc(reader):

    try:
        outlines = reader.outline

        toc = []

        def parse_outline(items):

            for item in items:

                if isinstance(item, list):
                    parse_outline(item)

                else:
                    title = getattr(item, "title", str(item))
                    toc.append(title)

        parse_outline(outlines)

        return toc

    except:
        return []


def generate_toc(text):

    lines = text.split("\n")

    toc = []

    for line in lines:

        line = line.strip()

        if len(line) < 5:
            continue

  
        if (
            line.isupper()
            or re.match(r'^\d+[\.\)]\s+', line)
            or re.match(r'^(chapter|section)', line.lower())
        ):

            toc.append(line)

    toc = list(dict.fromkeys(toc))

    return toc[:20]



def load_pdf(file_path):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

   
    toc = extract_toc(reader)

    if not toc:
        toc = generate_toc(text)

    return text, toc


def split_text(text, chunk_size=500, overlap=50):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunks.append(text[start:end])

        start = end - overlap

    return chunks



def embed(texts):

    return model.encode(texts)



def embed_query(query):

    return model.encode([query])


def add_to_index(embeddings):

    global index

    embeddings = np.array(embeddings).astype("float32")

    if index is None:

        dim = embeddings.shape[1]

        index = faiss.IndexFlatL2(dim)

    index.add(embeddings)


def retrieve(query, k=4, threshold=1.2):

    global index, all_chunks, all_sources

    query_vec = embed_query(query).astype("float32")

    distances, indices = index.search(query_vec, k)

    results = []

    for dist, idx in zip(distances[0], indices[0]):

        if idx < len(all_chunks) and dist < threshold:

            results.append({
                "text": all_chunks[idx],
                "source": all_sources[idx],
                "score": float(dist)
            })

    return results



def generate_answer(query, results):

    if not results:

        return {
            "type": "fallback",
            "message": "Answer not found in PDFs.",
            "google": f"https://www.google.com/search?q={query}"
        }

    output = ""

    for r in results:

        output += f"[{r['source']}] {r['text']}\n\n"

    return {
        "type": "answer",
        "message": output[:1200]
    }


@app.route("/", methods=["GET", "POST"])

def home():

    global all_chunks, all_sources, all_toc, index

    message = None

    ask_ready = False

    if request.method == "POST":

        files = request.files.getlist("pdf")

        for file in files:

            if file.filename == "":
                continue

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                file.filename
            )

            file.save(filepath)
            text, toc = load_pdf(filepath)
            chunks = split_text(text)

            embeddings = embed(chunks)

            add_to_index(embeddings)

            all_chunks.extend(chunks)

            all_sources.extend(
                [file.filename] * len(chunks)
            )

           
            all_toc[file.filename] = toc

        message = f"""
        ✦ {len(files)} document(s) processed —
        {len(all_chunks)} chunks indexed.
        """

        ask_ready = True

    if index is not None:
        ask_ready = True

    return render_template(
        "index.html",
        message=message,
        ask_ready=ask_ready,
        all_sources=all_sources,
        all_toc=all_toc
    )


@app.route("/ask", methods=["POST"])

def ask():

    global index

    if index is None:

        return jsonify({
            "type": "error",
            "message": "Upload PDFs first!"
        })

    query = request.form["query"]

    results = retrieve(query)

    response = generate_answer(query, results)

    return jsonify(response)


if __name__ == "__main__":

    app.run(debug=True)