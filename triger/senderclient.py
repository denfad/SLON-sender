import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("TRIGER")

def send_toxic_message(chat_id, username = None, reply_id = None):
    text = "Соси бибу" if reply_id is not None else f'{username} соси бибу'
    body = {"chat_id": chat_id, "reply_id": reply_id, "text": text}
    try:
        requests.post("http://localhost:8000/send", json=body)
    except Exception as E:
        logger.error(f'Sender throw exception {E}')

