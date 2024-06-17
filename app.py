from flask import Flask, render_template, request
from openai import AzureOpenAI
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)

ENDPOINT = os.environ.get('ENDPOINT')
API_KEY = os.environ.get('OPENAI_API_KEY')

print (ENDPOINT)
print (API_KEY)

API_VERSION = "2024-02-01"
MODEL_NAME = "gpt-35-turbo"


client = AzureOpenAI(
 azure_endpoint=ENDPOINT,
 api_key=API_KEY,
 api_version=API_VERSION
)

MESSAGES = [
 {"role": "system", "content": "You are a friendly companion and comforts people when they are sad, celebrate successes with them. If the user asks questions unrelated to mental wellness, explain that as a mental health companion, you can only answer questions related to mental wellness."},

]

@app.route("/")
def home(): 
 return render_template("index.html") 
@app.route("/get")
def get_bot_response(): 
 
 userText = request.args.get('msg') 

 print("input is",userText)

 completion = client.chat.completions.create(
 model=MODEL_NAME,
 messages=MESSAGES,
 temperature=1.0,
 )
 response = completion.choices[0].message.content
 MESSAGES.append({ "role": "user", "content": userText })
 MESSAGES.append({ "role": "assistant", "content": response })
 print("Message",MESSAGES) 
 return response


 
if __name__ == "__main__":
    app.run(debug=True)
  
# HOST = os.environ.get('SERVER_HOST', 'localhost')
# try:
#     PORT = int(os.environ.get('SERVER_PORT', '8000'))
# except ValueError:
#     PORT = 8000
# app.run(HOST, PORT)