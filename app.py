import os
import json
import docx
import textwrap
import requests
import tiktoken
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import openai
from openai.error import RateLimitError

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
customsearch_cx = os.getenv("customsearch_cx")
app.secret_key = os.getenv("flask_secret_key")
method_prompt_token = 800
FILE_DIR = './files/'
tick = tiktoken.get_encoding("gpt2")

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
            output_file = FILE_DIR + "converted_" + \
                os.path.splitext(uploaded_file.filename)[0] + ".txt"
            docx_to_txt(working_file, output_file)
            session['working_file'] = output_file
        else:
            session['working_file'] = working_file

    return redirect(url_for('index'))


def generate_summary(text, prompt):
    # Split the text into chunks
    chunks = textwrap.wrap(text, width=4096 - method_prompt_token, break_long_words=False)
    # Generate a summary for each chunk and store it in a list
    summaries = []
    for chunk in chunks:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "assistant", "content": chunk},
            {"role": "user", "content": prompt},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        summaries.append(response.choices[0].message["content"])
    # Combine the summaries and generate a final summary
    final_summary = " ".join(summaries)
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "assistant", "content": final_summary},
        {"role": "user", "content": prompt},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    content = response.choices[0].message["content"]
    total_tokens = response['usage']['total_tokens']
    return content, total_tokens


@app.route("/gpt-3.5-turbo", methods=['GET', 'POST'])
def gpt4():
    prompt = request.args.get(
        'user_input') if request.method == 'GET' else request.form['user_input']
    # Check if 'working_file' exists in the session
    if 'working_file' not in session:
        return jsonify(content="请先上传一个文件。")
    # Feed file as prompt, precede file content with user prompt
    with open(session['working_file'], 'r') as f:
        text = f.read()
        text = clip_text(text)
    # Generate summary
    content, total_tokens = generate_summary(text, prompt)
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

def clip_text(text, method_prompt_token=800):
    text_token = len(tick.encode(text))
    clip_text_index = int(
        len(text)*(4096-method_prompt_token)/text_token)
    clip_text = text[:clip_text_index]
    return clip_text

def search_google(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": customsearch_cx,
        "q": query,
    }
    response = requests.get(url, params=params)
    search_results = response.json()
    return search_results


if __name__ == '__main__':
    app.run(debug=True)
