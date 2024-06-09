from flask import Flask, render_template, request
from openai import AzureOpenAI
from dotenv import load_dotenv
import os


load_dotenv()


ENDPOINT = os.environ.get('ENDPOINT')
API_KEY = os.environ.get('API_KEY')

API_VERSION = "2024-02-01"
MODEL_NAME = "gpt-35-turbo"

client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION,
)


MESSAGES = [
    {"role": "system", "content": "You are a friendly companion and comforts people when they are sad, celebrate successes with them."},
    {"role": "user", "content": "Hello"},
    {
        "role": "assistant",
        "content": "Hey, how are you doing?",
    },
    {"role": "user", "content": "I am bored."},
    {"role": "assistant", "content": "Why do you think you are bored?"}
]


completion = client.chat.completions.create(
    model=MODEL_NAME,
    messages=MESSAGES,
    temperature=1.0
)



app = Flask(__name__)


@app.route("/")
def home():    
    return render_template("index.html")
@app.route("/get")
def get_bot_response():    
    userText = request.args.get('msg')  
    print("Usertext: "+ userText)
    response = completion.choices[0].message.content
    print("Response: "+response)
    return response
    
if __name__ == "__main__":
  app.run()