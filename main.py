import os

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
# import datab as db
from handlers import handlers

# from Create_table import create_user, create_wastes, create_category

load_dotenv()
TOKEN = os.getenv('TOKEN')

if __name__ == '__main__':

    application = ApplicationBuilder().token(TOKEN).build()
    # Создает приложение бота по токену

    for handler in handlers:
        application.add_handler(handler)
    # Добавление хендлеров в приложение

    application.run_polling()
    # Запуск приложения
