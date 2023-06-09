import os
import json
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
        working_file = FILE_DIR+uploaded_file.filename
        uploaded_file.save(working_file)
        session['working_file'] = working_file
    return redirect(url_for('index'))

@app.route("/gpt-3.5-turbo", methods=['GET', 'POST'])
def gpt4():
    user_input = request.args.get('user_input') if request.method == 'GET' else request.form['user_input']
    # feed file as prompt, precede file content with user prompt
    f = open(session['working_file'], 'r')
    text = user_input + f.read()
    # Send API request
    messages = [{"role": "user", "content": text}]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        ) 
        content = response.choices[0].message["content"]
    except RateLimitError:
        content = "The server is experiencing a high volume of requests. Please try again later."

    return jsonify(content=content)

if __name__ == '__main__':
    app.run(debug=True)
