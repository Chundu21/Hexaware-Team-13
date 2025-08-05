# Full Flask App with Login, Operator, Drag-and-Drop Upload, Reclassification, CSV/DB Save, Styled UI

from flask import Flask, request, redirect, url_for, render_template_string, session, send_file
from werkzeug.utils import secure_filename
from transformers import pipeline
import pytesseract, pdfplumber, os, csv, datetime
from PIL import Image
import docx
import imaplib
import email
from email.header import decode_header
import base64
import mysql.connector

app = Flask(_name_)
app.secret_key = 'your_secret_key'

pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

LABELS = ["Resume", "Invoice", "Report", "Letter", "Legal", "Admin", "HR", "Tech", "Finance", "Marketing", "General"]
CSV_FILE = "session_data.csv"
DB_NAME = "doc_classifier"
TABLE_NAME = "documents"

# --- Utility Functions ---
def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".png", ".jpg", ".jpeg"]:
        return pytesseract.image_to_string(Image.open(file_path))
    elif ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif ext == ".docx":
        doc = docx.Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

def fetch_latest_email_attachment():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login("hexaproject941@gmail.com", "yxuziwoghexefdzb")
    mail.select("inbox")

    result, data = mail.search(None, "ALL")
    email_ids = data[0].split()
    if not email_ids:
        return None, None, None, None

    latest_email_id = email_ids[-1]
    result, msg_data = mail.fetch(latest_email_id, "(RFC822)")
    raw_email = msg_data[0][1]

    msg = email.message_from_bytes(raw_email)
    from_email = msg["From"]
    to_email = msg["To"]

    for part in msg.walk():
        content_disposition = part.get("Content-Disposition")
        if content_disposition and "attachment" in content_disposition:
            filename = part.get_filename()
            if filename:
                filepath = os.path.join("uploads", secure_filename(filename))
                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))
                return filepath, filename, from_email, to_email

    return None, None, None, None


def classify_text(text):
    result = classifier(text, candidate_labels=LABELS)
    sorted_labels_scores = sorted(zip(result['labels'], result['scores']), key=lambda x: x[1], reverse=True)
    sorted_labels = [l for l, s in sorted_labels_scores]
    sorted_scores = [s for l, s in sorted_labels_scores]
    top_label = sorted_labels[0]
    scores = {label: f"{score*100:.2f}%" for label, score in zip(sorted_labels, sorted_scores)}
    return top_label, scores

def save_to_csv(entries):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(entries[0].keys()))
        writer.writeheader()
        writer.writerows(entries)

def ensure_db_and_table(cursor):
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255),
            type VARCHAR(100),
            operator VARCHAR(100),
            upload_time DATETIME,
            classification TEXT,
            extracted_text TEXT,
            metadata VARCHAR(255),
            ingested DATETIME,
            extracted DATETIME,
            classified DATETIME,
            routed DATETIME
        )
    """)

def insert_to_db(entries, user, pwd):
    conn = mysql.connector.connect(host="localhost", user=user, password=pwd)
    cursor = conn.cursor()
    ensure_db_and_table(cursor)
    cursor.execute(f"USE {DB_NAME}")
    for row in entries:
        cursor.execute(f"""
            INSERT INTO {TABLE_NAME} 
            (filename, type, operator, upload_time, classification, extracted_text, metadata, ingested, extracted, classified, routed) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['Filename'], row['Type'], row['Operator'], row['Upload Time'],
            row['Classification'][:1000], row['Extracted Text'][:2000], row['Metadata'][:255],
            row['Ingested'], row['Extracted'], row['Classified'], row['Routed']
        ))
    conn.commit()
    cursor.close()
    conn.close()

# --- Routes ---
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'pass123':
            session['logged_in'] = True
            return redirect(url_for('operator'))
        return "<h3>Invalid login</h3>"
    return '''
<div style="text-align:center; padding-top:50px; background: linear-gradient(to bottom, #e0f7fa, #ffffff); height:100vh;">
<!-- Top Logo -->
    <br><link rel="icon" type="image/jpeg" href="/static/favicon.jpg">
    <img src="/static/favicon.jpg" alt="SmartDocs Logo" style="width:150px; border-radius:10px; box-shadow:0 0 10px #004080; margin-bottom:30px;"><br>

    <!-- Login Form Box -->
    <div style="display:inline-block; background-color:black; padding:40px 50px; border-radius:20px; color:white; box-shadow:0 0 25px rgba(0,0,0,0.6); text-align:left;">
        <h2 style="text-align:center; color:#00ccff;">🔐 Login</h2>
        <form method="post" style="margin-top:20px;">
            <label><b>Username:</b></label><br>
            <input name="username" style="width:100%; padding:10px; margin-top:5px; margin-bottom:20px; border:none; border-radius:5px; background-color:#f0f4ff;"><br>

            <label><b>Password:</b></label><br>
            <input name="password" type="password" style="width:100%; padding:10px; margin-top:5px; margin-bottom:25px; border:none; border-radius:5px; background-color:#f0f4ff;"><br>

            <input type="submit" value="Login" style="width:100%; padding:10px; background-color:#00ccff; color:black; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">
        </form>
    </div>

</div>
'''

@app.route('/operator', methods=['GET', 'POST'])
def operator():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        operator_name = request.form.get('operator')
        session['operator'] = operator_name
        session['session_data'] = []
        return redirect(url_for('dashboard'))
    return '''
<div style="text-align:center; padding-top:50px; background: linear-gradient(to bottom, #e0f7fa, #ffffff); height:100vh;">

    <!-- Top Logo -->
    <br><img src="/static/favicon.jpg" alt="Favicon" style="width:180px; margin-bottom:30px; border-radius:10px; box-shadow:0 0 10px #004080;"><br>

    <!-- Operator Info Black Box -->
    <div style="display:inline-block; background-color:black; padding:40px 50px; border-radius:20px; color:white; box-shadow:0 0 25px rgba(0,0,0,0.6); text-align:left;">
        <h2 style="text-align:center; color:#00ccff;">👨‍💼 Operator Info</h2>

        <form method="post" style="margin-top:20px;">
            <label for="operator"><b>Enter Your Name:</b></label><br>
            <input name="operator" required style="width:100%; padding:10px; margin-top:10px; margin-bottom:25px; border:none; border-radius:5px; background-color:#f0f4ff;"><br>

            <input type="submit" value="Proceed" style="width:100%; padding:10px; background-color:#00ccff; color:black; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">
        </form>
    </div>

</div>
'''

@app.route("/fetch_email", methods=["POST"])
def fetch_email():
    file_path, filename, from_email, to_email = fetch_latest_email_attachment()
    if not file_path:
        return redirect(url_for("dashboard"))

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = extract_text(file_path)
    top_label, scores = classify_text(text[:512])

    sorted_scores = sorted(scores.items(), key=lambda x: float(x[1].strip('%')), reverse=True)
    classification_text = "\n".join([f"{k}: {v}" for k,v in sorted_scores])
    top_conf = sorted_scores[0][1]

    entry = {
        "Filename": filename,
        "Type": "Email Attachment",
        "Operator": session.get('operator', 'Unknown'),
        "Upload Time": now,
        "Classification": f"{classification_text}\nFile '{filename}' is sent to {top_label} ({top_conf})",
        "Ingested": now,
        "Extracted": now,
        "Classified": now,
        "Routed": now,
        "Extracted Text": text[:3000],
        "Metadata": f"From: {from_email} | To: {to_email} | Source: Email"
    }

    filenames = [e['Filename'] for e in session.get('session_data', [])]
    if filename not in filenames:
        session.setdefault('session_data', []).append(entry)
        session.modified = True

    return redirect(url_for("dashboard"))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'operator' not in session:
        return redirect(url_for('operator'))

    message = ""
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(file_path):
                    base, ext = os.path.splitext(filename)
                    filename = f"{base}_{datetime.datetime.now().strftime('%H%M%S')}{ext}"
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)

                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                text = extract_text(file_path)
                label, scores = classify_text(text[:512])

                sorted_scores = sorted(scores.items(), key=lambda x: float(x[1].strip('%')), reverse=True)
                classification_text = "\n".join([f"{k}: {v}" for k,v in sorted_scores])
                top_conf = sorted_scores[0][1]
                metadata = session.get('metadata', 'Uploaded via web')


                entry = {
                    "Filename": filename,
                    "Type": file.mimetype,
                    "Operator": session['operator'],
                    "Upload Time": now,
                    "Classification": f"{classification_text}\nFile '{filename}' is sent to {label} ({top_conf})",
                    "Ingested": now,
                    "Extracted": now,
                    "Classified": now,
                    "Routed": now,
                    "Extracted Text": text[:3000],
                    "Metadata": f"Name: {filename} | Size: {os.path.getsize(file_path)} bytes"
                }
                filenames = [e['Filename'] for e in session['session_data']]
                if filename not in filenames:
                    session['session_data'].append(entry)
                    session.modified = True
                    message = f"✅ File '{filename}' classified as {label}"
                else:
                    message = f"⚠ File '{filename}' already exists. Upload skipped."
        elif 'reclassify_name' in request.form:
            docname = request.form['reclassify_name']
            newlabel = request.form['newlabel']
            for row in session['session_data']:
                if row['Filename'] == docname:
                    row['Classification'] += f"\nFile '{docname}' has been manually reclassified to {newlabel} by {session['operator']}"
            message = f"🛠 File '{docname}' manually reclassified."

    return render_template_string('''
<html>
<head>
    <title>📄 Document Dashboard</title>
    <link rel="icon" href="/static/favicon.jpg" type="image/jpeg">
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background-color: #434141;
            color: white;
            text-align: center;
            padding: 30px;
        }
        h2, h3 {
            color: #00ccff;
        }
        input[type="file"], select, input[type="text"], input[type="password"] {
            padding: 8px;
            border-radius: 5px;
            border: none;
            margin: 5px;
            width: 250px;
        }
        input[type="submit"], button {
            background-color: #00ccff;
            color: black;
            padding: 8px 16px;
            margin: 8px;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover, input[type="submit"]:hover {
            background-color: #009acc;
        }
        .drop-zone {
            border: 2px dashed #00ccff;
            padding: 20px;
            margin: 20px;
            color: #00ccff;
            border-radius: 10px;
        }
        table {
            margin: auto;
            border-collapse: collapse;
            background-color: #111111;
            color: white;
            box-shadow: 0 0 10px #00ccff;
        }
        th, td {
            padding: 10px 15px;
            border: 1px solid #00ccff;
        }
        th {
            background-color: #002233;
            color: #00ccff;
        }
        img {
            width: 60px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px #00ccff;
        }
    </style>
    <script>
    function dropHandler(ev) {
        ev.preventDefault();
        const dt = ev.dataTransfer;
        const files = dt.files;
        document.getElementById("fileinput").files = files;
    }
    function dragOverHandler(ev) {
        ev.preventDefault();
    }
    </script>
</head>
<body>

    <img src="/static/favicon.jpg" alt="Favicon">
    <h2>📥 Upload Documents</h2>

    {% if message %}
        <p style="color:#00ff88; font-weight:bold">{{ message }}</p>
    {% endif %}

    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file" id="fileinput" required><br>
        <div class="drop-zone" ondrop="dropHandler(event);" ondragover="dragOverHandler(event);">
            Drag and drop your file here
        </div>
        <input type="submit" value="Classify">
    </form>

    <form method="post">
        <select name="reclassify_name">
            {% for row in session.session_data %}
                <option value="{{ row['Filename'] }}">{{ row['Filename'] }}</option>
            {% endfor %}
        </select>
        Reclassify to:
        <select name="newlabel">
            {% for label in labels %}
                <option value="{{ label }}">{{ label }}</option>
            {% endfor %}
        </select>
        <button type="submit">🔁 Reclassify</button>
    </form>

    <form action="/fetch_email" method="post">
        <button type="submit">📩 Fetch & Classify from Gmail</button>
    </form>

    <h3>🗂 Dashboard</h3>
    {% if session.session_data %}
    <table>
        <tr>
            {% for k in session.session_data[0].keys() %}
                <th>{{ k }}</th>
            {% endfor %}
        </tr>
        {% for row in session.session_data %}
        <tr>
            {% for v in row.values() %}
                <td>{{ v }}</td>
            {% endfor %}
        </tr>
        {% endfor %}
    </table>
    {% else %}
        <p style="color:#888">No documents uploaded.</p>
    {% endif %}

    <form action="/save_csv" method="post"><button>💾 Save to CSV</button></form>
    <form action="/download_csv"><button>📥 Download CSV</button></form>
    <form action="/save_db" method="post">
        <input name="db_user" placeholder="DB Username">
        <input name="db_pass" type="password" placeholder="Password">
        <button>🛢 Save to DB</button>
    </form>
    <form action="/logout" method="post"><button>🚪 Logout</button></form>

</body>
</html>
''', message=message, labels=LABELS)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/download_csv')
def download_csv():
    if os.path.exists(CSV_FILE):
        return send_file(CSV_FILE, as_attachment=True)
    return "<h2>CSV not found!</h2><a href='/dashboard'>Go Back</a>"

@app.route('/save_db', methods=['POST'])
def save_db():
    if 'session_data' not in session or not session['session_data']:
        return "<h2>No files to save!</h2><a href='/dashboard'>Go Back</a>"
    try:
        user = request.form['db_user']
        pwd = request.form['db_pass']
        insert_to_db(session['session_data'], user, pwd)

        # 💡 Email summary after DB save
        summaries = []
        for row in session['session_data']:
            summaries.append(f"""File: {row['Filename']}
Sent to: {row['Classification'].splitlines()[-1]}
Uploaded by: {row['Operator']}
Time: {row['Upload Time']}
---------------------------""")
        full_summary = "\n".join(summaries)
        send_email(full_summary)

        return "<h2 style='color:green'>✅ Data saved to MySQL and email sent!</h2><a href='/dashboard'>Go Back</a>"
    except Exception as e:
        return f"<h2>Database error: {e}</h2><a href='/dashboard'>Go Back</a>"


    
@app.route('/save_csv', methods=['POST'])
def save_csv():
    if 'session_data' in session and session['session_data']:
        save_to_csv(session['session_data'])

        # Build email summary
        summaries = []
        for row in session['session_data']:
            summaries.append(f"""File: {row['Filename']}
Sent to: {row['Classification'].splitlines()[-1]}
Uploaded by: {row['Operator']}
Time: {row['Upload Time']}
---------------------------""")
        full_summary = "\n".join(summaries)

        send_email(full_summary)
        return redirect(url_for('dashboard'))

    return "<h2>No data to save!</h2><a href='/dashboard'>Go Back</a>"


   
import smtplib
from email.message import EmailMessage

EMAIL_ADDRESS = 'hexaproject941@gmail.com'
EMAIL_PASSWORD = 'yxuziwoghexefdzb'

def send_email(summary):
    msg = EmailMessage()
    msg['Subject'] = 'Document Classification Summary'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = '2022peccb257@gmail.com'
    msg.set_content(summary)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

if _name_ == '_main_':
    app.run(debug=True)