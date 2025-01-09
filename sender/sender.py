import telebot
from flask import Flask, request, jsonify
import queue
from decouple import config
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logger = logging.getLogger("SENDER")

logger.info("Starting Sender")

token = config('BOT_TOKEN')
messages = queue.Queue()


def send(text, chat_id, reply_id):
    bot = telebot.TeleBot(token)
    try:
        if chat_id is not None and reply_id is not None:
            bot.send_message(chat_id=chat_id, text=text, reply_to_message_id=reply_id)
            logger.info(f'Send message \"{text}\" to chat {chat_id} for message {reply_id}')
        elif chat_id is not None:
            bot.send_message(chat_id=chat_id, text=text)
            logger.info(f'Send message \"{text}\" to chat {chat_id}')
        else:
            logger.error(f'Unexpected message')
    except Exception as E:
        logger.error(f'Telegram throw exception {E}')


def read_queue():
    if not messages.empty():
        data = messages.get_nowait()
        logger.info(f'Working on {data}')
        chat_id = data.get("chat_id")
        reply_id = data.get("reply_id")
        text = data.get("text")
        send(text, chat_id, reply_id)


# Настройка планировщика задач
scheduler = BackgroundScheduler()
scheduler.add_job(func=read_queue, trigger="interval", seconds=3)

# Стартуем планировщик
scheduler.start()
app = Flask(__name__)


@app.route('/send', methods = ['POST'])
async def send_message():
    data = request.json
    messages.put(data)
    resp = jsonify(success=True)
    return resp


try:
    sender_port = int(config('SENDER_PORT'))
    app.run(port=sender_port, host="0.0.0.0")
except (KeyboardInterrupt, SystemExit):
    # Останавливаем планировщик при завершении работы приложения
    scheduler.shutdown()

