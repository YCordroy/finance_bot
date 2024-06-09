from telegram.ext import ApplicationBuilder

from Settings import TOKEN
from Tables import (
    Base,
    engine,
    add_categories,
    add_users
)

if __name__ == '__main__':

    Base.metadata.create_all(bind=engine)
    add_categories()
    add_users()

    application = ApplicationBuilder().token(TOKEN).build()
    # Создает приложение бота по токену

    from Handlers import handlers

    for handler in handlers:
        application.add_handler(handler)
    # Добавление хендлеров в приложение

    application.run_polling()
    # Запуск приложения
