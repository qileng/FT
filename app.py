import os
import json
import docx
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import openai
from openai.error import RateLimitError

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")
app.secret_key = os.getenv("flask_secret_key")
FILE_DIR = './files/'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        file_ext = os.path.splitext(uploaded_file.filename)[1]
        working_file = FILE_DIR+uploaded_file.filename
        uploaded_file.save(working_file)

        if file_ext.lower() == ".docx":
            output_file = FILE_DIR + "converted_" + os.path.splitext(uploaded_file.filename)[0] + ".txt"
            docx_to_txt(working_file, output_file)
            session['working_file'] = output_file
        else:
            session['working_file'] = working_file

    return redirect(url_for('index'))

@app.route("/gpt-3.5-turbo", methods=['GET', 'POST'])
def gpt4():
    prompt = request.args.get('user_input') if request.method == 'GET' else request.form['user_input']

    # Check if 'working_file' exists in the session
    if 'working_file' not in session:
        return jsonify(content="请先上传一个文件。")

    # feed file as prompt, precede file content with user prompt
    with open(session['working_file'], 'r') as f:
        text = f.read()

    # Send API request
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "assistant", "content": text},
        {"role": "user", "content": prompt},
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        content = response.choices[0].message["content"]
        total_tokens = response['usage']['total_tokens']
    except RateLimitError:
        content = "The server is experiencing a high volume of requests. Please try again later."
        total_tokens = 0

    return jsonify(content=content, total_tokens=total_tokens)

def docx_to_txt(input_file, output_file):
    # Read the .docx file
    doc = docx.Document(input_file)
    
    # Extract the text from each paragraph
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
        
    # Save the extracted text to the .txt file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(text))

if __name__ == '__main__':
    app.run(debug=True)

