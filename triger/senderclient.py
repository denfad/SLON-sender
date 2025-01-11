import json

import requests
import logging
import redis
import os
import pika

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logging.getLogger("pika").setLevel(logging.WARNING)
logger = logging.getLogger("TRIGER")

INCOMING_TASKS = "incoming_tasks"
READY_TASKS = "ready_tasks"

class ModelClient:
    def __init__(self, redis_client: redis.Redis):
        rabbit_host = os.getenv('RABBIT_HOST')
        rabbit_user = os.getenv('RABBIT_USER')
        rabbit_password = os.getenv('RABBIT_PASSWORD')
        credentials = pika.PlainCredentials(rabbit_user, rabbit_password)
        self.rabbit_client = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host, credentials=credentials))
        self.redis_client = redis_client

    def send_toxic_message(self, chat_id, tags, username = None, reply_id = None):
        tmp = self.redis_client.lrange(str(chat_id), 0, -1)
        context = list(map(lambda x: x.decode(), tmp))
        text = "Соси бибу" if reply_id is not None else f'{username} соси бибу'
        body = {"chat_id": str(chat_id), "reply_id": str(reply_id), "text": text, "username": username}
        try:
            self.send_to_queue(INCOMING_TASKS, json.dumps(body))
        except Exception as E:
            logger.error(f'Sender throw exception {E}')

    def send_to_queue(self, queue, text):
        channel = self.rabbit_client.channel()
        channel.queue_declare(queue=queue)
        channel.basic_publish(exchange='',
                              routing_key=queue,
                              body=text)
        channel.close()

