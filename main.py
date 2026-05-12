import os
import requests
from fastapi import FastAPI, Request
from langchain_groq import ChatGroq

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "monsecret123")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="llama3-8b-8192")

@app.get("/webhook")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(request.query_params.get("hub.challenge"))
    return {"message": "Token invalide"}

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    phone_number = None
    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone_number = message["from"]
        user_text = message["text"]["body"]

        response = llm.invoke(
            f"Tu es un assistant commercial. Réponds en français à : {user_text}"
        )
        bot_response = response.content
        send_whatsapp_message(phone_number, bot_response)

    except Exception as e:
        print(f"Erreur: {e}")
        if phone_number:
            send_whatsapp_message(phone_number, "Désolé, une erreur est survenue.")

    return {"status": "ok"}

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }
    requests.post(url, json=payload, headers=headers)
