import os

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
import datab as db

from Create_table import create_user, create_wastes, create_category

load_dotenv('./workdir/.env')
TOKEN = os.getenv('TOKEN')
user_dict = eval(os.getenv('USERS'))

if __name__ == '__main__':

    try:
        create_category()
        create_wastes()
        create_user()
        for key, value in user_dict.items():
            db.add_new_user(key, value)
    except:
        pass
    # Проверка для создания таблиц в базе данных

    application = ApplicationBuilder().token(TOKEN).build()
    # Создает приложение бота по токену

    from handlers import handlers

    for handler in handlers:
        application.add_handler(handler)
    # Добавление хендлеров в приложение

    application.run_polling()
    # Запуск приложения

USERS = [value[0] for value in db.get_users()]
# Создание переменной для доступа пользователей
