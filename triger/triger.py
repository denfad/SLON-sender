import telebot
from decouple import config
from telebot.types import Message
import logging
import random
from apscheduler.schedulers.background import BackgroundScheduler
from senderclient import send_toxic_message
from dbclient import DBClient


SCHEDULE_BY_MESSAGE = 0
SCHEDULE_WITH_DELAY = 1
SCHEDULE_RANDOM = 2


# настройки БД
bot = telebot.TeleBot(config('BOT_TOKEN'))
db_host = config('DB_HOST')
db_name = config('DB_NAME')
db_user = config('DB_USER')
db_password= config('DB_PASSWORD')
db_client = DBClient(db_host, db_name, db_user, db_password)


# Обработчик бота
@bot.message_handler(content_types=['text'])
def toxic_by_message(message: Message):
    # проверяем есть ли в бд связка username + chat_id, если нет то добавляем
    db_client.insert_user_chat(message.chat.id, message.from_user.username)

    # ищем пользователя в БД
    res = db_client.find_user_by_name_and_type(message.from_user.username, SCHEDULE_BY_MESSAGE)

    # данный пользователь есть в базе
    if res is not None:
        logging.info(f'User {res._t.target} send message to chat {message.chat.id}')
        # выбираем будем ли его травить
        choice = random.randint(1,5)
        if choice == 5:
            send_toxic_message(message.chat.id, message.from_user.username, message.id)


#  токсичить каждый час
def toxic_with_delay():
    # ищем пользователей в БД
    users = db_client.find_users_by_type(SCHEDULE_WITH_DELAY)
    for user in users:
        # рассылаем каждому пользователю по чатам сообщения
        chats = db_client.find_user_chats(user._t.target)
        for chat in chats:
            send_toxic_message(chat._t.chat_id, chat._t.username)

# рандомный токсик
def random_toxic():
    # ищем пользователей в БД
    users = db_client.find_users_by_type(SCHEDULE_RANDOM)

    for user in users:
        choice = random.randint(1, 10)
        if choice == 10:
            # рассылаем пользователю по чатам сообщения
            chats = db_client.find_user_chats(user._t.target)
            for chat in chats:
                send_toxic_message(chat._t.chat_id, chat._t.username)


# Настройка планировщика задач для угнетения каждый час
# фоновая задача выполнения каждый час
toxic_delay = int(config('TOXIC_DELAY'))
delay_scheduler = BackgroundScheduler()
delay_scheduler.add_job(func=toxic_with_delay, trigger="interval", seconds=toxic_delay)
delay_scheduler.start()

# Настройка планировщика задач для рандомного угнетения
# фоновая задача выполнения каждые пол часа
rand_toxic_delay = int(config('TOXIC_RANDOM_DELAY'))
random_scheduler = BackgroundScheduler()
random_scheduler.add_job(func=random_toxic, trigger="interval", seconds=rand_toxic_delay)
random_scheduler.start()

try:
    bot.polling(none_stop=True, interval=1)
except (KeyboardInterrupt, SystemExit):
    # Останавливаем планировщик при завершении работы приложения
    random_scheduler.shutdown()
    delay_scheduler.shutdown()
