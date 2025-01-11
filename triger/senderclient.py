import requests
import logging
import redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("TRIGER")


class ModelClient:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
    def send_toxic_message(self, chat_id, tags, username = None, reply_id = None):
        tmp = self.redis_client.lrange(str(chat_id), 0, -1)
        context = list(map(lambda x: x.decode(), tmp))
        text = "Соси бибу" if reply_id is not None else f'{username} соси бибу'
        body = {"chat_id": str(chat_id), "reply_id": reply_id, "text": text}
        try:
            requests.post("http://localhost:8000/send", json=body)
        except Exception as E:
            logger.error(f'Sender throw exception {E}')

