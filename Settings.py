import os
from locale import setlocale, LC_ALL

from dotenv import load_dotenv
from sqlalchemy import create_engine


load_dotenv('./workdir/.env')

engine = create_engine('sqlite:///workdir/Myfin.db')

TOKEN = os.getenv('TOKEN')

user_dict = eval(os.getenv('USERS'))
# Список пользователей для записи в бд

LANGUAGE = setlocale(LC_ALL, 'ru_RU.UTF-8')

KEYS = ['Категория', 'Пользователь', 'Сумма', 'Комментарий']
# Ключи для очистки контекста