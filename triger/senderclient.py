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
        self.redis_client = redis_client

    def send_toxic_message(self, chat_id, tags, username = None, reply_id = None):
        tmp = self.redis_client.lrange(str(chat_id), 0, -1)
        context = list(map(lambda x: x.decode(), tmp))
        body = {"chat_id": str(chat_id),
                "reply_id": str(reply_id) if reply_id is not None else None,
                "tags": tags,
                "context": context,
                "username": username if username is not None else None}
        try:
            self.send_to_queue(INCOMING_TASKS, json.dumps(body))
        except Exception as E:
            logger.error(f'Sender throw exception {E}')

    def send_to_queue(self, queue, text):
        rabbit_client = self.create_rabbit_client()
        channel = rabbit_client.channel()
        channel.queue_declare(queue=queue)
        channel.basic_publish(exchange='',
                              routing_key=queue,
                              body=text)
        channel.close()
        rabbit_client.close()


    def create_rabbit_client(self):
        rabbit_host = os.getenv('RABBIT_HOST')
        rabbit_user = os.getenv('RABBIT_USER')
        rabbit_password = os.getenv('RABBIT_PASSWORD')
        if rabbit_user is not None:
            credentials = pika.PlainCredentials(rabbit_user, rabbit_password)
            return pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host, credentials=credentials))
        else:
            return pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host))
