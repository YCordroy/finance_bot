import re
import time
from io import BytesIO
from datetime import date, datetime
import locale

from pandas import DataFrame
from telegram import (
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    CallbackQuery
)
from telegram.ext import ConversationHandler

from Keyboards import (
    inline_month_calendar,
    buttons_for_change,
    report_month_calendar,
    change_user,
    report_keyboard
)
import datab as db
from main import USERS

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
CATEGORY, PRICE, COMMENT = range(3)
KEYS = ['Категория', 'Пользователь', 'Сумма', 'Комментарий']


async def add(update: Update, context) -> int:
    """Вызывает клавиатуру для выбора категории"""
    if not check_user(update):
        return

    user_id = update.message.from_user.id
    message_id = update.message.message_id

    await context.bot.delete_message(user_id, message_id)

    reply_keyboard: list[list] = [[values[1]] for values in db.get_categories()]
    markup_key: ReplyKeyboardMarkup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    text: str = 'Выберете категорию'
    await update.message.reply_text(text=text, reply_markup=markup_key)

    return CATEGORY


async def set_category(update: Update, context) -> int:
    """Обрабатывает выбор категории и перводит на этап ввода стоимости"""
    context.user_data['Категория'] = update.message.text
    user_id = update.message.from_user.id
    message_id = update.message.message_id

    # Проверка на то, что категория есть в базе данных
    categories_names = [values[1] for values in db.get_categories()]

    if update.message.text in categories_names:
        context.user_data['Пользователь']: int = update.message.from_user.id
        text: str = 'Введите сумму'
        await update.message.reply_text(text)
        await context.bot.delete_message(user_id, message_id)
        await context.bot.delete_message(user_id, message_id - 1)
        return PRICE
    else:
        await context.bot.delete_message(user_id, message_id - 1)
        await add(update, context)


async def set_price(update: Update, context) -> int:
    """Получает сумму, записывает в контекст, переводит на комментарий"""
    user_id = update.message.from_user.id
    message_id = update.message.message_id

    try:
        context.user_data['Сумма']: float = float(update.message.text)
        text: str = 'Введите комментарий или /skip, для пропуска'
        await update.message.reply_text(text)
        await context.bot.delete_message(user_id, message_id)
        await context.bot.delete_message(user_id, message_id - 1)

        return COMMENT
    except Exception:
        text: str = 'Сумма должна быть цифрой!'
        await update.message.reply_text(text)
        await context.bot.delete_message(user_id, message_id)
        await context.bot.delete_message(user_id, message_id - 1)


async def set_comment(update: Update, context):
    """Получает комментарий, вызывает функцию записи в бд"""
    context.user_data['Комментарий']: str = update.message.text
    await save(update, context)
    return ConversationHandler.END


async def save(update: Update, context):
    """Сохраняет в бд введенную информацию и выводит ее в сообщение"""
    db.insert_payments(context)

    inline_markup: InlineKeyboardMarkup = buttons_for_change()

    text: str = f'''
Данные о покупке:
{date.today().strftime('%d-%B-%Y')}
Категория: {context.user_data['Категория']}
Сумма: {context.user_data['Сумма']}
Комментарий: {context.user_data.get('Комментарий', '-')}
'''

    message_data = await update.message.reply_text(text=text, reply_markup=inline_markup)

    # Записываем message id в базу данных
    message_id: int = message_data.message_id
    user_id: int = context.user_data['Пользователь']
    db.set_message_id(user_id, message_id)

    user_id = update.message.from_user.id
    message_id = update.message.message_id
    await context.bot.delete_message(user_id, message_id)
    await context.bot.delete_message(user_id, message_id - 1)

    for key in KEYS:
        context.user_data[key] = None
        del context.user_data['Комментарий']
    return ConversationHandler.END


async def end_add(update: Update, context):
    """Принудительно заканчивает диалог"""
    for key in KEYS:
        context.user_data[key] = None
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    await context.bot.delete_message(user_id, message_id)
    await context.bot.delete_message(user_id, message_id - 1)
    return ConversationHandler.END


async def change_category_keyboard(update: Update, context) -> None:
    """Изменяет клавиатуру сообщения на шаг выбора категории"""
    query: CallbackQuery = update.callback_query
    categories: list[tuple] = [(f're_set_category_{key}', name) for key, name in db.get_categories()]
    buttons: list[list] = [[InlineKeyboardButton(name, callback_data=callback)] for callback, name in categories]
    buttons.append([InlineKeyboardButton('Назад', callback_data='back')])
    inline_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(buttons)

    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=inline_markup
    )


async def re_set_category(update: Update, context) -> None:
    """Изменяет запись категории в базе данных"""
    query: CallbackQuery = update.callback_query
    new_category_id: int = int(re.match(r're_set_category_(\d+)', query.data).group(1))
    user_id: int = query.from_user.id
    message_id: int = query.message.message_id
    db.re_set_category(user_id, message_id, new_category_id)

    text: str = db.get_waste_info(user_id, message_id)
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=message_id,
        text=text
    )

    await back(update, context)


async def back(update: Update, context) -> None:
    """Возвращает клавиатуру сообщения к исходному состоянию"""
    inline_markup: InlineKeyboardMarkup = buttons_for_change()
    query: CallbackQuery = update.callback_query

    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=inline_markup
    )


async def keyboard_for_del(update: Update, context) -> None:
    """Изменяет клавиатуру сообщения, для подтверждения удаления"""
    query: CallbackQuery = update.callback_query
    buttons: list[list] = [
        [InlineKeyboardButton('Удалить', callback_data='confirm_del')],
        [InlineKeyboardButton('Назад', callback_data='back')]
    ]
    inline_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(buttons)

    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=inline_markup
    )


async def confirm_del(update: Update, context) -> None:
    """Удаляет запись в базе данных и сообщение в чате"""
    query: CallbackQuery = update.callback_query
    user_id: int = query.from_user.id
    message_id: int = query.message.message_id

    db.del_waste(user_id, message_id)

    await context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=message_id
    )


async def select_date(update: Update, context) -> None:
    """Выводит клавиатуру для выбора даты"""
    query: CallbackQuery = update.callback_query
    date_now: list = query.data.split('_')
    keyboard = inline_month_calendar(int(date_now[-2]), int(date_now[-1]))

    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=keyboard
    )


async def change_date(update: Update, context) -> None:
    """Изменяет дату в базе данных, на выбранную пользователем"""
    query: CallbackQuery = update.callback_query
    user_id: int = query.from_user.id
    message_id: int = query.message.message_id
    new_date = datetime.strptime(query.data.split('_')[1], '%Y-%m-%d').date()

    db.change_date(user_id, message_id, new_date)

    text: str = db.get_waste_info(user_id, message_id)
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=message_id,
        text=text
    )

    await back(update, context)


async def get_report(update: Update, context) -> None:
    """Выводит сообщение для формирования отчета"""
    if not check_user(update):
        return

    if not context.user_data.get('report'):
        context.user_data['report'] = {}
        context.user_data['report']['Дата начала отчета'] = None
        context.user_data['report']['Дата окончания отчета'] = None
        context.user_data['report']['Пользователь'] = []

    text = report_get_message_text(context)
    keyboard = report_keyboard(context)

    # Если сообщение уже создано, то редактируем
    try:
        await update.message.reply_text(text=text, reply_markup=keyboard)
        user_id = update.message.from_user.id
        message_id = update.message.message_id
        await context.bot.delete_message(user_id, message_id)
    except Exception:
        query: CallbackQuery = update.callback_query
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=query.message.message_id,
            text=text,
            reply_markup=keyboard
        )


def report_get_message_text(context) -> str:
    """Формирование текста сообщения для отчета"""
    report = [
        f'{key}: {value}'
        if key != 'Пользователь'
        else f'{key}: {', '.join([user[1] for user in value])}'
        for key, value in context.user_data['report'].items()
    ]
    return f'''
    Формирование отчета:
{'\n'.join(report)}
'''


async def report_get_date(update: Update, context) -> None:
    """Выводит клавиатуру выбора дат отчета"""
    query: CallbackQuery = update.callback_query
    date_now: list = query.data.split('_')
    start_date = context.user_data['report'].get('Дата начала отчета')
    if start_date:
        keyboard = report_month_calendar(int(date_now[-2]), int(date_now[-1]), start_date)
    else:
        keyboard = report_month_calendar(int(date_now[-2]), int(date_now[-1]))

    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=keyboard
    )


async def report_select_date(update: Update, context) -> None:
    """Обрабатывает введённую дату отчета"""
    query: CallbackQuery = update.callback_query
    report_date: date = datetime.strptime(query.data.split('_')[2], '%Y-%m-%d').date()

    if not context.user_data['report']['Дата начала отчета']:
        context.user_data['report']['Дата начала отчета'] = report_date
    else:
        context.user_data['report']['Дата окончания отчета'] = report_date

    await get_report(update, context)


async def report_get_user(update: Update, context) -> None:
    """Вызывает клавиатуру выбора пользователя"""
    query: CallbackQuery = update.callback_query
    keyboard = change_user()

    await context.bot.edit_message_reply_markup(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=keyboard
    )


async def report_select_user(update: Update, context) -> None:
    """Обрабатывает выбраных пользователей"""
    query: CallbackQuery = update.callback_query
    report_user: str = re.match(r'get_user_(\d+|all)', query.data).group(1)

    if report_user == 'all':
        report_user: list[tuple] = db.get_users()
        context.user_data['report']['Пользователь'] = report_user
    else:
        report_user = int(report_user)
        user_name = db.get_name_for_id(report_user)
        context.user_data['report']['Пользователь'] = [(report_user, user_name)]

    text = report_get_message_text(context)
    query: CallbackQuery = update.callback_query
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=query.message.message_id,
        text=text
    )

    await report_get_report(update, context)


async def report_get_report(update: Update, context) -> None:
    """Формирует и отправляет файл отчета"""
    query: CallbackQuery = update.callback_query
    date_start = context.user_data['report']['Дата начала отчета']
    date_end = context.user_data['report']['Дата окончания отчета']
    user: list[tuple] = context.user_data['report']['Пользователь']
    users = ', '.join([f'{id}' for id, user in user])

    # получить данные из бд
    report_info = db.report_get_info(date_start, date_end, users)

    # сформировать эксель
    categories = [values[1] for values in db.get_categories()]
    columns = ['Дата', *categories, 'Комментарий']
    report_info = db.report_transform_report(report_info)
    report_df = DataFrame(report_info, columns=columns)
    excel_file = BytesIO()
    report_df.to_excel(excel_file, index=False)
    excel_file.seek(0)

    # отправить пользователю
    await query.message.reply_document(document=excel_file, filename='Оплата.xlsx')
    del context.user_data['report']


async def report_stop_report(update: Update, context) -> None:
    """Принудительная очистка репорта"""
    if not check_user(update):
        return
    del context.user_data['report']

    await get_report(update, context)


def check_user(update: Update) -> bool:
    """Проверка права доступа к командам бота"""
    try:
        user_id = update.message.from_user.id
    except AttributeError:
        user_id = update.callback_query.message.chat.id

    return user_id in USERS


async def delete_user_message(update: Update, context) -> None:
    """Удаляет сообщение пользователя"""
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    if user_id in USERS:
        await context.bot.delete_message(user_id, message_id)
