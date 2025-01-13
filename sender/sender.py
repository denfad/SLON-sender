import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os
from dotenv import load_dotenv
import pika
import time
import json
from flask import Flask

app = Flask(__name__)
@app.route('/health')
def index():
    return "Hello, World!"


INCOMING_TASKS = "incoming_tasks"
READY_TASKS = "ready_tasks"

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger("pika").setLevel(logging.WARNING)
logger = logging.getLogger("SENDER")

logger.info("Starting Sender")

token = os.getenv('BOT_TOKEN')


def send(text, chat_id, reply_id, username):
    bot = telebot.TeleBot(token)
    try:
        if chat_id is not None and reply_id is not None:
            bot.send_message(chat_id=chat_id, text=text, reply_to_message_id=reply_id)
            logger.info(f'Send message \"{text}\" to chat {chat_id} for message {reply_id}')
        elif chat_id is not None:
            bot.send_message(chat_id=chat_id, text=f'{username}, {text}')
            logger.info(f'Send message \"{username}, {text}\" to chat {chat_id}')
        else:
            logger.error(f'Unexpected message')
    except Exception as E:
        logger.error(f'Telegram throw exception {E}')


def create_rabbit_client():
    rabbit_host = os.getenv('RABBIT_HOST')
    rabbit_user = os.getenv('RABBIT_USER')
    rabbit_password = os.getenv('RABBIT_PASSWORD')
    if rabbit_user is not None:
        credentials = pika.PlainCredentials(rabbit_user, rabbit_password)
        return pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host, credentials=credentials))
    else:
        return pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host))


def read_queue():
    rabbit_client = create_rabbit_client()
    channel = rabbit_client.channel()
    channel.queue_declare(queue=READY_TASKS)
    message = channel.basic_get(READY_TASKS, auto_ack=True)
    channel.close()
    rabbit_client.close()
    if message[2] is not None:
        data = json.loads(message[2].decode())
        logger.info(f'Working on {data}')
        username = data.get("username")
        chat_id = data.get("chat_id")
        reply_id = data.get("reply_id")
        text = data.get("text")
        send(text, chat_id, reply_id, username)


# Настройка планировщика задач
scheduler = BackgroundScheduler()
scheduler.add_job(func=read_queue, trigger="interval", seconds=1, max_instances=30)

try:
    # Стартуем планировщик
    scheduler.start()
    app.run(port=8000)
except (KeyboardInterrupt, SystemExit):
    # Останавливаем планировщик при завершении работы приложения
    scheduler.shutdown()

