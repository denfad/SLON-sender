import telebot
from telebot.types import Message
import logging
import secrets
from apscheduler.schedulers.background import BackgroundScheduler
from senderclient import ModelClient
from dbclient import DBClient
import os
from dotenv import load_dotenv
import redis

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logger = logging.getLogger("TRIGER")

logger.info("Starting Triger")

SCHEDULE_BY_MESSAGE = 0
SCHEDULE_WITH_DELAY = 1
SCHEDULE_RANDOM = 2

# redis
redis_host = os.getenv('REDIS_HOST')
redis_password = os.getenv('REDIS_PASS')
if redis_password is None:
    redis_client = redis.Redis(host=redis_host, db=0)
else:
    redis_client = redis.Redis(host=redis_host, db=0, password=redis_password)
# настройки бота
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
# настройки бд
db_client = DBClient()
# взаимодействие с моделью
model_client = ModelClient(redis_client)

# Обработчик бота
@bot.message_handler(content_types=['text'])
def toxic_by_message(message: Message):
    logger.info(f'Get message from user {message.from_user.username} in chat {message.chat.id}')
    # добавление сообщения в контекст
    count = redis_client.lpush(f'{message.chat.id}', message.text).numerator
    if count > 5:
        redis_client.rpop(f'{message.chat.id}', count - 5)
    # проверяем есть ли в бд связка username + chat_id, если нет то добавляем
    db_client.insert_user_chat(message.chat.id, f'@{message.from_user.username}')

    # ищем пользователя в БД
    res = db_client.find_user_by_name_and_type(f'@{message.from_user.username}', SCHEDULE_BY_MESSAGE)

    # данный пользователь есть в базе
    if res is not None:
        # выбираем будем ли его травить
        choice = secrets.choice([1,2,3])
        if choice == 3:
            logger.info(f'User {res._t.target} send message to chat {message.chat.id}')
            model_client.send_toxic_message(message.chat.id, res._t.tags, f'@{message.from_user.username}', message.id)


#  токсичить каждый час
def toxic_with_delay():
    # ищем пользователей в БД
    users = db_client.find_users_by_type(SCHEDULE_WITH_DELAY)
    for user in users:
        # рассылаем каждому пользователю по чатам сообщения
        chats = db_client.find_user_chats(user._t.target)
        for chat in chats:
            logger.info(f'User {chat._t.username} send message to chat {chat._t.chat_id}')
            model_client.send_toxic_message(chat._t.chat_id, user._t.tags, chat._t.username)

# рандомный токсик
def random_toxic():
    # ищем пользователей в БД
    users = db_client.find_users_by_type(SCHEDULE_RANDOM)

    for user in users:
        choice = secrets.choice([1,2])
        if choice == 2:
            # рассылаем пользователю по чатам сообщения
            chats = db_client.find_user_chats(user._t.target)
            for chat in chats:
                logger.info(f'User {chat._t.username} send message to chat {chat._t.chat_id}')
                model_client.send_toxic_message(chat._t.chat_id, user._t.tags, chat._t.username)


# Настройка планировщика задач для угнетения каждый час
# фоновая задача выполнения каждый час
delay_scheduler = BackgroundScheduler()
delay_scheduler.add_job(toxic_with_delay, 'cron', hour='0-23')
delay_scheduler.start()

# Настройка планировщика задач для рандомного угнетения
# фоновая задача выполнения каждые пол часа
random_scheduler = BackgroundScheduler()
random_scheduler.add_job(random_toxic, 'cron', hour='0-23')
random_scheduler.start()

try:
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
except (KeyboardInterrupt, SystemExit):
    # Останавливаем планировщик при завершении работы приложения
    random_scheduler.shutdown()
    delay_scheduler.shutdown()
