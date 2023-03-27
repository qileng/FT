import re
import openai
import docx

from docx import Document

openai.api_key = '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'

def generate_text(text,prompt):
    model_engine = "text-davinci-003"
    prompt = (prompt[:2048] + '...') if len(prompt) > 2048 else prompt
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "assistant", "content": text},
        {"role": "user", "content": prompt},
    ]
    )
    message = response.choices
    return re.sub('[^0-9a-zA-Z\n\.\?,!]+', ' ', message)

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
        

# Replace these with the paths to your input and output files
input_file = "Sample_openai.docx"
output_file = "Sample_openai.txt"

docx_to_txt(input_file, output_file)

with open('Sample_openai.txt', 'r', encoding='utf-8') as file2:
    content = file2.read()

input_text = content

prompt = "上述文本讲了什么？"

generated_text = generate_text(text=input_text,prompt=prompt)
print(generated_text)
