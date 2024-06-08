from flask import Flask, render_template, request
# pip install openai

from openai import AzureOpenAI

ENDPOINT = "https://polite-ground-030dc3103.4.azurestaticapps.net/api/v1"
API_KEY = "INSERT_API_KEY"

API_VERSION = "2024-02-01"
MODEL_NAME = "gpt-35-turbo"

client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION,
)

MESSAGES = [
    {"role": "system", "content": "You are an empathetic therapist."},
    {"role": "user", "content": "hello"},
    {
        "role": "assistant",
        "content": "Hello, how can I help you?",
    },
    {"role": "user", "content": "i feel (.*)"},
    {
        "role": "assistant",
        "content": "Why do you feel {}?"
    }
]

completion = client.chat.completions.create(
    model=MODEL_NAME,
    messages=MESSAGES,
    temperature=1.0
)

print(completion.model_dump_json(indent=2))

app = Flask(__name__)

# def get_completion(prompt, model="gpt-3.5-turbo"):
#     messages = [{"role": "user", "content": prompt}]
#     response = openai.ChatCompletion.create(
#         model=model,
#         messages=messages,
#         temperature=0, # this is the degree of randomness of the model's output
#     )
#   return response.choices[0].message["content"]
@app.route("/")
def home():    
    return render_template("index.html")
@app.route("/get")
def get_bot_response():    
    userText = request.args.get('msg')  
    response = completion.choices[0].message.content
    #return str(bot.get_response(userText)) 
    return response
if __name__ == "__main__":
  app.run()