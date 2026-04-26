from flask import Flask, render_template, request, jsonify
import os
import numpy as np
import faiss
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# =====================
# GLOBAL STATE
# =====================
all_chunks = []
all_sources = []
index = None

model = SentenceTransformer("all-MiniLM-L6-v2")


# =====================
# PDF LOADER
# =====================
def load_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


# =====================
# SPLIT TEXT
# =====================
def split_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap

    return chunks


# =====================
# EMBEDDINGS
# =====================
def embed(texts):
    return model.encode(texts)

def embed_query(query):
    return model.encode([query])


# =====================
# FAISS INDEX
# =====================
def add_to_index(embeddings):
    global index

    embeddings = np.array(embeddings).astype("float32")

    if index is None:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)

    index.add(embeddings)


# =====================
# RETRIEVAL
# =====================
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


# =====================
# ANSWER GENERATION
# =====================
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
        "message": output[:900]
    }


# =====================
# HOME PAGE
# =====================
@app.route("/", methods=["GET", "POST"])
def home():
    global all_chunks, all_sources, index

    message = None
    ask_ready = False

    if request.method == "POST":

        files = request.files.getlist("pdf")

        for file in files:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            text = load_pdf(filepath)
            chunks = split_text(text)

            embeddings = embed(chunks)
            add_to_index(embeddings)

            all_chunks.extend(chunks)
            all_sources.extend([file.filename] * len(chunks))

        message = "PDFs uploaded successfully!"
        ask_ready = True

    return render_template("index.html", message=message, ask_ready=ask_ready)


# =====================
# ASK API (AJAX)
# =====================
@app.route("/ask", methods=["POST"])
def ask():
    if index is None:
        return jsonify({"type": "error", "message": "Upload PDFs first!"})

    query = request.form["query"]
    results = retrieve(query)
    response = generate_answer(query, results)

    return jsonify(response)


# =====================
# RUN APP
# =====================
if __name__ == "__main__":
    app.run(debug=True)