import json
import os.path
import pickle
import re
import nltk
import random
import model_training as mt
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import strings as st
import owmrequest

# поиск токена для телеграмма
BOT_TOKEN = ''
city_id = 1508291
if os.path.isfile(st.BOT_TOKEN_FILENAME):
    f = open(st.BOT_TOKEN_FILENAME, "r")
    BOT_TOKEN = f.read()
    f.close()
else:
    print("Пожалуйста, создайте в папке проекта файл 'token.txt' и поместите туда токен для работы телеграм бота")

config_file = open(st.BOT_DATASET_FOR_TRAINING_FILENAME, "r")
BOT_CONFIG = json.load(config_file)
config_file.close()

with open(st.BOT_ANEKDOT, "r", encoding = 'cp1251', errors="ignore") as f:
    text_anekdot = f.read()
    text_anekdot = text_anekdot.split('* * *')

vectorizer = ''
model = ''


# подключение обученной модели
def connectBotModel():
    global vectorizer, model
    # если модель не существует
    if (not os.path.isfile(st.BOT_MODEL_FILENAME)) or (not os.path.isfile(st.BOT_VECTORIZER_FILENAME)):
        print("Обученная модель не найдена, запускается обучение")
        mt.train()  # запуск модуля обучения модели
        print("Обучение модели завершено")

    # чтение векторайзера из файла
    f = open(st.BOT_VECTORIZER_FILENAME, "rb")
    vectorizer = pickle.load(f)

    # чтение модели из файла
    f = open(st.BOT_MODEL_FILENAME, "rb")
    model = pickle.load(f)


connectBotModel()


# отбрасывает знаки препинания и приводит к нижнему регистру
def filter(text):
    text = text.lower()
    punctuation = r'[^\w\s]'  # регулярное выражение для того, чтобы остался только текст и пробелы
    return re.sub(punctuation, "", text)


# считает насколько тексты отличаются в процентах
def isMatching(text1, text2):
    text1 = filter(text1)
    text2 = filter(text2)
    distance = nltk.edit_distance(text1, text2)  # возвращает количество букв на которое различаются тексты
    avg_length = (len(text1) + len(text2)) / 2  # средняя длина исходных текстов
    return distance / avg_length


# отпределяет намерение по тексту
def getIntent(text):
    all_intents = BOT_CONFIG["intents"]
    for name, data in all_intents.items():
        for example in data["examples"]:
            if isMatching(text, example) < 0.4:
                return name


# получить ответ
def getAnswer(intent):
    responses = BOT_CONFIG['intents'][intent]["responses"]
    return random.choice(responses)


# бот: по фразе выдает ответ
# print(bot("Как дела?"))
def bot(text):
    intent = getIntent(text)

    if not intent:  # если намерение не найдено
        # тут подключается модель машинного обучения
        test = vectorizer.transform([text])
        intent = model.predict(test)[0]

    if intent:  # если намерение найдено
        return getAnswer(intent)
    return random.choice(BOT_CONFIG['failure_phrases'])


# функция ответа при получении команды /hello
def hello(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f'Hello, {update.effective_user.first_name}')

# функция показа погоды
def pogoda(update: Update, context: CallbackContext) -> None:
    owmrequest.visual(owmrequest.request_forecast("Челябинск"))
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('saved_figure.png', 'rb'))


# функция будет вызвана при получении сообщения
def botMessage(update: Update, context: CallbackContext) -> None:
    city = []
    reply = []
    text = update.message.text  # Получение сообщения
    if 'погода' in text.lower() and 'Ник' == text[:3:]:
        text = text.lower().split()
        city = text[-1:]
        reply = owmrequest.request_current_weather(city)
        update.message.reply_text(reply) # отправка сообщения
        # context.bot.send_message(chat_id=update.effective_chat.id, text=reply)
    elif 'прогноз' in text.lower() and 'Ник' == text[:3:]:
        text = text.lower().split()
        city = text[-1:]
        owmrequest.visual(owmrequest.request_forecast(city))
        update.message.reply_photo(photo=open('saved_figure.png', 'rb')) # отправка сообщения
        # context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('saved_figure.png', 'rb'))
    elif 'анекдот' in text.lower() and 'Ник' == text[:3:]:
        reply = random.choice(text_anekdot)
        update.message.reply_text(reply) # отправка сообщения
        # context.bot.send_message(chat_id=update.effective_chat.id, text=reply)
    else:
        reply = bot(text)  # подготовка ответного сообщения
        update.message.reply_text(reply) # отправка сообщения



# связываем созданного бота с тг

updater = Updater(BOT_TOKEN)

updater.dispatcher.add_handler(CommandHandler('hello', hello))  # конфигурация: при получении команды /hello вызвать соотвествующую функцию
updater.dispatcher.add_handler(CommandHandler('Pogoda', pogoda))	# информация о погоде
updater.dispatcher.add_handler(MessageHandler(Filters.text, botMessage))  # при получении любого текстового сообщения вызывается функция botMessage

print("Бот запущен")
updater.start_polling()
updater.idle()
