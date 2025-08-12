from flask import Flask, request, render_template, jsonify
import fitz  # PyMuPDF
import os

app = Flask(__name__)

CLICKED_WORDS = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    pdf = request.files['pdf']
    if pdf:
        text = extract_text_from_pdf(pdf)
        words = text.split()
        return render_template('viewer.html', words=words)
    return "No PDF uploaded", 400

@app.route('/click-word', methods=['POST'])
def click_word():
    word = request.json.get('word')
    if word:
        CLICKED_WORDS[word] = CLICKED_WORDS.get(word, 0) + 1
        return jsonify(status='success', word=word, count=CLICKED_WORDS[word])
    return jsonify(status='error'), 400

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

if __name__ == '__main__':
    app.run(debug=True)
