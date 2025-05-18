import requests
import re


WHATSAPP_URL = "http://localhost:5001/send"
WHATSAPP_AUTH = ("user", "secret")


def send_whatsapp(num: str, msg: str):
    number = "".join(re.findall(r"\d+", num))
    try:
        data = {
            "number": number,
            "message": msg,
        }
        requests.post(WHATSAPP_URL, auth=WHATSAPP_AUTH, json=data)
    except Exception as e:
        print(f"Error al enviar whatsapp: {str(e)}")
