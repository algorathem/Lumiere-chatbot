from flask import Flask, render_template, request
from openai import AzureOpenAI
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)

ENDPOINT = "b11ec81e-0219-4603-8578-9f601a0fc972"
API_KEY = "https://polite-ground-030dc3103.4.azurestaticapps.net/api/v1"


print (ENDPOINT)
print (API_KEY)

API_VERSION = "2024-02-01"
MODEL_NAME = "gpt-35-turbo"

client = AzureOpenAI(
 azure_endpoint=ENDPOINT,
 api_key=API_KEY,
 api_version=API_VERSION,
)

@app.route("/")
def home(): 
 return render_template("index.html")
@app.route("/get")
def get_bot_response(): 
 userText = request.args.get('msg') 
 print("Usertext: "+ userText)

 MESSAGES = [
 {"role": "system", "content": "You are a friendly companion and comforts people when they are sad, celebrate successes with them. If you are asked for your name, introduce yourself as Lumiere. If you are asked to answer questions not related to mental well-being, explain that you don't know the answer. If you are tasked to perform tasks not directly related to the user's mental state, explain that it is beyond you."},
 {"role": "user", "content": userText},
]
 completion = client.chat.completions.create(
 model=MODEL_NAME,
 messages=MESSAGES,
 temperature=1.0
 )
 response = completion.choices[0].message.content
 print("Response: "+response)
 
 return response
 
 
# if __name__ == "__main__":
#  app.run()
HOST = os.environ.get('SERVER_HOST', 'localhost')
try:
    PORT = int(os.environ.get('SERVER_PORT', '8000'))
except ValueError:
    PORT = 8000
app.run(HOST, PORT)