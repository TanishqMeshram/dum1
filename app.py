import os
import re
import nltk
import logging
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from spellchecker import SpellChecker
from nltk.tokenize import word_tokenize
from PyPDF2 import PdfReader
from docx import Document
from flask_cors import CORS

logging.basicConfig(level=logging.DEBUG)

nltk.download('punkt')

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains on all routes
app.config['UPLOAD_FOLDER'] = 'uploads/'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

spell = SpellChecker()

common_names_and_terms = set([
    "Bharat", "Sahil", "Tanishq", "Python", "Java", "SQL", "HTML", "CSS", "JavaScript", "AWS", "Azure", "GCP",
    "TensorFlow", "PyTorch", "NumPy", "Pandas", "scikit-learn", "GitHub", "Linux", "Docker", "Kubernetes", "Vivek",
    "Figma", "CMS", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", 
    "November", "December", "Nagpur", "Wordpress", "Internpe", "Rupesh", "Ramesh", "Suresh", "Anshun", "Rutuj", "Taklikar",
    "Rajkumar", "Rao", "Bahadure", "Bhardwaj", "Bansod", "Meshram", "Dudhani", "Mohammad", "Ansari", "Kale", "Nasre", 
    "Kharapkar", "Patankar"
])

def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
    return text

def extract_text_from_docx(file_path):
    text = ""
    try:
        doc = Document(file_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        logging.error(f"Error extracting text from DOCX: {e}")
    return text

def analyze_resume(file_path, file_extension):
    content = ""
    try:
        if file_extension == '.pdf':
            content = extract_text_from_pdf(file_path)
        elif file_extension == '.docx':
            content = extract_text_from_docx(file_path)
        else:
            with open(file_path, 'r') as file:
                content = file.read()
    except Exception as e:
        logging.error(f"Error analyzing resume: {e}")
    
    mistakes = []

    if not re.search(r'\b\d{10}\b', content) or not re.search(r'\b[\w.-]+?@\w+?\.\w+?\b', content):
        mistakes.append("Missing contact information (phone number or email).")

    tokens = word_tokenize(content)
    misspelled_words = [
        word for word in tokens 
        if word.isalpha() 
        and word not in common_names_and_terms 
        and spell.correction(word) != word
    ]
    if misspelled_words:
        mistakes.append("Spelling errors found: " + ", ".join(misspelled_words[:5]))

    required_headings = ["Education", "Experience", "Skills"]
    missing_headings = [heading for heading in required_headings if heading.lower() not in content.lower()]
    if missing_headings:
        mistakes.append("Missing section headings: " + ", ".join(missing_headings))

    return mistakes[:3]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logging.error("No file part in request")
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        logging.error("No selected file")
        return jsonify({'error': 'No selected file'})

    if file:
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_extension = os.path.splitext(filename)[1].lower()
            mistakes = analyze_resume(file_path, file_extension)
            return jsonify({'mistakes': mistakes})
        except Exception as e:
            logging.error(f"Error saving file: {e}")
            return jsonify({'error': 'Failed to process file'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
