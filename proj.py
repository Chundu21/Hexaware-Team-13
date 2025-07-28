import subprocess, sys, os, csv, time, datetime, http.server, socketserver, cgi
from transformers import pipeline
import pytesseract, pdfplumber, docx
from PIL import Image

# Auto-install dependencies
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for p in ["pytesseract", "pdfplumber", "transformers", "Pillow", "tabulate", "python-docx"]:
    try:
        _import_(p if p != "Pillow" else "PIL")
    except:
        install(p)

# Configuration
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
LABELS = ["Invoice", "Resume", "Contract", "Report", "Receipt", "ID Card", "Certificate"]
CSV_FILE = "results.csv"
UPLOAD_DIR = "uploads"
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Extraction
def extract_text(file_path):
    ext = file_path.lower().split(".")[-1]
    if ext == "pdf":
        with pdfplumber.open(file_path) as pdf:
            return "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
    elif ext in ["png", "jpg", "jpeg"]:
        image = Image.open(file_path)
        return pytesseract.image_to_string(image)
    elif ext == "docx":
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    return ""

def route(label):
    l = label.lower()
    if "invoice" in l: return "📊 Accounting"
    if "resume" in l: return "👥 HR"
    if "contract" in l: return "⚖ Legal"
    return "📁 General Department"

def save_to_csv(name, file, label, route_to, score, preview):
    row = [name, file, label, route_to, score, preview[:300].replace("\n", " ").strip(), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    header = ["Name", "File", "Classification", "Route", "Confidence (%)", "Preview", "Last Updated"]
    write_header = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, mode="a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(header)
        writer.writerow(row)

class WebHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_page.encode())
        else:
            super().do_GET()

    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.get('Content-Type'))
        if ctype == 'multipart/form-data':
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
            name = form.getvalue("name") or "Anonymous"
            file_item = form['file']

            if file_item.filename:
                fn = os.path.basename(file_item.filename)
                save_path = os.path.join(UPLOAD_DIR, fn)
                with open(save_path, 'wb') as f:
                    f.write(file_item.file.read())

                timestamps = { "Ingested": datetime.datetime.now().strftime("%H:%M:%S") }
                text = extract_text(save_path)
                timestamps["Extracted"] = datetime.datetime.now().strftime("%H:%M:%S")

                result = classifier(text[:1000], LABELS)
                top_label = result['labels'][0]
                score = round(result['scores'][0] * 100, 2)
                routed = route(top_label)
                timestamps["Classified"] = datetime.datetime.now().strftime("%H:%M:%S")
                timestamps["Routed"] = datetime.datetime.now().strftime("%H:%M:%S")

                save_to_csv(name, fn, top_label, routed, score, text)

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                response = f"""
                <html><body>
                <h2>✅ Processed: {fn}</h2>
                <p><b>Name:</b> {name}</p>
                <p><b>Classification:</b> {top_label}</p>
                <p><b>Confidence:</b> {score}%</p>
                <p><b>Routed to:</b> {routed}</p>
                <h4>Workflow Timestamps:</h4>
                <ul>{"".join([f"<li>{k} @ {v}</li>" for k,v in timestamps.items()])}</ul>
                <a href="/">🏠 Go back</a>
                </body></html>
                """
                self.wfile.write(response.encode())

html_page = """
<html>
<head><title>📁 Document Classifier</title></head>
<body style='font-family:Arial; padding:20px;'>
<h2>📄 Upload Document</h2>
<form enctype="multipart/form-data" method="post">
  <label>Name: <input type="text" name="name" required></label><br><br>
  <label>File: <input type="file" name="file" required></label><br><br>
  <input type="submit" value="Upload & Classify">
</form>
<hr>
<p>🔍 Supported formats: PDF, DOCX, JPG, PNG</p>
</body>
</html>
"""

PORT = 8000
with socketserver.TCPServer(("", PORT), WebHandler) as httpd:
    print(f"🚀 Serving at http://localhost:{PORT}")
    httpd.serve_forever()