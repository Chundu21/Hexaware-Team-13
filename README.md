# 📄 SmartDocs: Intelligent Document Classification Web App

## 👋 Introduction

SmartDocs is a **Flask-based AI-powered web application** that allows users (even students and beginners) to:
- Upload documents
- Automatically extract text (using OCR for images and PDFs)
- Classify the document using a powerful AI model
- Save the results to a CSV or MySQL database
- Receive classification summaries via email

This app also supports Gmail integration to classify attachments from the inbox.

---

## ✨ What You Can Do With It

- Upload and classify **PDFs**, **images**, and **Word files**
- Drag-and-drop uploads from your system
- Use your **Gmail** to fetch latest attachments for classification
- Extract text using OCR (Optical Character Recognition)
- Use AI (zero-shot classification) to detect the type of document: Resume, Invoice, Letter, etc.
- Save results into a **CSV** or **MySQL database**
- View everything neatly in a **web dashboard**
- Receive an **email summary** after saving data

---

## 🛠 Technologies Used

| Technology         | Role |
|-------------------|------|
| Flask             | Backend web server |
| Jinja2            | HTML rendering |
| Transformers (Hugging Face) | AI classification model |
| pytesseract       | OCR from images |
| pdfplumber        | Extract text from PDF |
| python-docx       | Extract text from Word (.docx) files |
| imaplib, email    | Fetch attachments from Gmail |
| MySQL Connector   | Save data to database |
| smtplib           | Send email summaries |
| HTML, CSS         | Web dashboard and UI |

---

## 🔧 How to Set It Up (Beginner Friendly)

### ✅ 1. Clone the Project
```bash
git clone https://github.com/yourusername/smartdocs.git
cd smartdocs
```

### ✅ 2. Install Required Libraries
```bash
pip install -r requirements.txt
```

### ✅ 3. Install Tesseract OCR
- Download: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- After install, make sure this line in `app.py` is correct:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### ✅ 4. Add Your Gmail App Password
In the code:
```python
EMAIL_ADDRESS = 'your_email@gmail.com'
EMAIL_PASSWORD = 'your_app_password'  # Use Gmail App Password, NOT your real password
```
👉 To generate app password: Go to Gmail → Manage your Google Account → Security → App passwords

### ✅ 5. Run the App
```bash
python app.py
```
Go to your browser and open [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔐 Login Info (for testing)

| Username | Password |
|----------|----------|
| admin    | pass123  |



## 🧠 Classification Model Used

- **Model**: `facebook/bart-large-mnli` (from Hugging Face)
- **Type**: Zero-shot classification
- **Works Without Training!**
- **Possible Labels**:
  - Resume
  - Invoice
  - Report
  - Letter
  - Legal
  - Admin
  - HR
  - Tech
  - Finance
  - Marketing
  - General

---

## 📬 Gmail Integration

The app can:
- Automatically connect to your Gmail inbox
- Download the latest attachment
- Extract its content and classify it using AI
- Add metadata like sender and receiver emails
- Add this document to the dashboard

Make sure you allow IMAP access in Gmail settings.

---

## 💾 Save Data

From the dashboard, you can:
- 💾 Save all entries to a CSV file
- 🛢 Save all data to a MySQL database (you’ll enter your DB username and password)
- 📩 Automatically receive a summary email

---

## 📜 Sample Use Case (for Students)

> Let’s say you are building a **Document Management System** project for your college submission. You can use this application and explain:
- How AI classifies documents
- How OCR helps with text extraction
- How drag-drop and email automation works
- How results are stored securely in databases or files
- How everything works in a Flask web app

This project covers many real-world topics like **AI, Databases, File Handling, Email Automation, Web Dev**, and more.

---

## 🛡️ Security Notes

- Do not expose passwords or sensitive info on public GitHub
- Use `.env` file or environment variables in production
- Gmail login must use App Passwords for safety

---

## 👨‍💻 Author

**Developed by:**
- SAI SNEHANTH .C
- MAHALAKSHMI .L
- THENDRAL .A
- MURALI KRISHNAA .K


---

## 📃 License

MIT License – Feel free to use and modify.