from urllib.parse import urljoin
from celery import shared_task
from time import sleep
from django.conf import settings
import random
import re
import time
import requests

@shared_task
def send_whatsapp(num: str, msg: str):
    if not settings.WHATSAPP_URL:
        return
    number = "".join(re.findall(r"\d+", num))
    try:
        data = {"chatId": number, "session": "default"}
        whatsapp_request("/api/sendSeen", data)
        whatsapp_request("/api/startTyping", data)
        time.sleep(random.uniform(0.5, 1))
        whatsapp_request("/api/stopTyping", data)
        data = {
            "chatId": number,
            "reply_to": None,
            "text": msg,
            "linkPreview": True,
            "linkPreviewHighQuality": False,
            "session": "default",
        }
        response = whatsapp_request("/api/sendText", data)
        if response.status_code == 422:
            activate_session()
            response = whatsapp_request("/api/sendText", data)
        if response.status_code != 201:
            print(f"{response.status_code} Error al enviar whatsapp a {number}")
    except Exception as e:
        print("ERROR al enviar whatsapp: ", str(e))


def activate_session():
    whatsapp_request("api/sessions/default/restart")
    data = {"presence": "offline"}
    whatsapp_request("api/sessions/default/presence", data)


def whatsapp_request(link:str, data:dict = {}):
    headers = {
        "X-Api-Key": settings.WHATSAPP_APIKEY,
        "Content-Type": "application/json" 
    }
    url = urljoin(settings.WHATSAPP_URL, link)
    return requests.post(url, json=data, headers=headers)


