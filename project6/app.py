
import os
from flask import Flask, render_template, request, redirect, url_for
import cv2
import numpy as np
from ultralytics import YOLO
from sklearn.cluster import DBSCAN

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

model = YOLO("yolov8n.pt")

ANIMAL_CLASSES = {"cow", "sheep", "horse", "elephant", "dog"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def cluster_herds(centroids, eps=80):
    if len(centroids) == 0:
        return []
    clustering = DBSCAN(eps=eps, min_samples=2).fit(centroids)
    return clustering.labels_

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if file and allowed_file(file.filename):
            path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(path)
            return redirect(url_for("detect", filename=file.filename))
    return render_template("index.html")

@app.route("/detect/<filename>")
def detect(filename):
    img_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    img = cv2.imread(img_path)

    results = model(img)[0]

    boxes = []
    centroids = []

    for r in results.boxes:
        cls_id = int(r.cls[0])
        conf = float(r.conf[0])
        name = model.names[cls_id]

        if name in ANIMAL_CLASSES and conf > 0.4:
            x1, y1, x2, y2 = map(int, r.xyxy[0])
            boxes.append((x1, y1, x2, y2, name))
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            centroids.append([cx, cy])

    herd_labels = cluster_herds(np.array(centroids)) if len(centroids) else []

    herd_sizes = {}
    if len(centroids):
        for lbl in set(herd_labels):
            if lbl != -1:
                herd_sizes[int(lbl)] = list(herd_labels).count(lbl)

    herd_count = len(herd_sizes)

    for i, box in enumerate(boxes):
        x1, y1, x2, y2, name = box
        tag = "solo"
        color = (0, 255, 0)
        if len(centroids) and herd_labels[i] != -1:
            tag = f"herd-{int(herd_labels[i])}"
            color = (255, 0, 0)

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, f"{name} ({tag})", (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    out_path = os.path.join(app.config["UPLOAD_FOLDER"], "out_" + filename)
    cv2.imwrite(out_path, img)

    return render_template(
        "result.html",
        input_image=filename,
        output_image="out_" + filename,
        total_animals=len(boxes),
        herd_count=herd_count,
        herd_sizes=herd_sizes
    )

@app.route("/map", methods=["POST"])
def map_view():
    lat_raw = request.form.get("lat", "")
    lon_raw = request.form.get("lon", "")
    count = int(request.form.get("count", 0))

    try:
        lat = float(lat_raw)
        lon = float(lon_raw)
    except (ValueError, TypeError):
        lat = 28.6139
        lon = 77.2090

    herd_location = {
        "lat": lat,
        "lon": lon,
        "count": count
    }

    return render_template("map.html", herd_location=herd_location)



if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
