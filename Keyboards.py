from calendar import Calendar
from datetime import datetime, date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from DataBase import get_users


def inline_month_calendar(month: int, year: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора даты при изменении данных в бд."""
    calendar: Calendar = Calendar()
    weeks: list = calendar.monthdays2calendar(year=year, month=month)
    ignored_cb: str = 'ignore'
    weekdays: list = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    months = {
        1: 'Январь',
        2: 'Февраль',
        3: 'Март',
        4: 'Апрель',
        5: 'Май',
        6: 'Июнь',
        7: 'Июль',
        8: 'Август',
        9: 'Сентябрь',
        10: 'Октябрь',
        11: 'Ноябрь',
        12: 'Декабрь'
    }

    keyboard: list[list] = []
    keyboard.append([InlineKeyboardButton(text=weekday, callback_data=ignored_cb) for weekday in weekdays])

    for week in weeks:
        buttons = []
        for day in week:
            if day[0] == 0:
                buttons.append(InlineKeyboardButton(text=' ', callback_data=ignored_cb))
            else:
                date = datetime(year=year, month=month, day=day[0]).date()
                buttons.append(InlineKeyboardButton(text=day[0], callback_data=f"calendar_{date.strftime('%Y-%m-%d')}"))
        keyboard.append(buttons)

    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)
    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)

    keyboard.append([
        InlineKeyboardButton(text=f'{months[prev_month]}', callback_data=f'change_date_{prev_month}_{prev_year}'),
        InlineKeyboardButton(text=f'{months[month]} {year}', callback_data=ignored_cb),
        InlineKeyboardButton(text=f'{months[next_month]}', callback_data=f'change_date_{next_month}_{next_year}')
    ])

    keyboard.append([InlineKeyboardButton(text='Назад', callback_data='back')])
    return InlineKeyboardMarkup(keyboard)


def buttons_for_change() -> InlineKeyboardMarkup:
    """Возвращает инлайн клавиатуру для изменения записи в бд."""
    date_now = date.today()

    keyboard: list[list] = [
        [
            InlineKeyboardButton('Изменить категорию', callback_data='change_category'),
            InlineKeyboardButton('Изменить дату', callback_data=f'change_date_{date_now.month}_{date_now.year}')
        ],
        [
            InlineKeyboardButton('Удалить запись', callback_data='delete_message'),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def report_month_calendar(month: int, year: int, start_date=False) -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора даты для отчета."""
    calendar: Calendar = Calendar()
    weeks: list = calendar.monthdays2calendar(year=year, month=month)
    ignored_cb: str = 'ignore'
    weekdays: list = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    months = {
        1: 'Январь',
        2: 'Февраль',
        3: 'Март',
        4: 'Апрель',
        5: 'Май',
        6: 'Июнь',
        7: 'Июль',
        8: 'Август',
        9: 'Сентябрь',
        10: 'Октябрь',
        11: 'Ноябрь',
        12: 'Декабрь'
    }

    keyboard: list = []
    keyboard.append([InlineKeyboardButton(text=weekday, callback_data=ignored_cb) for weekday in weekdays])

    for week in weeks:
        buttons = []
        for day in week:
            date = datetime(year=year, month=month, day=1 if not day[0] else day[0]).date()
            if not day[0] or (start_date and date < start_date):
                buttons.append(InlineKeyboardButton(text=' ', callback_data=ignored_cb))
            else:
                buttons.append(
                    InlineKeyboardButton(
                        text=day[0],
                        callback_data=f"report_date_{date.strftime('%Y-%m-%d')}"
                    )
                )
        keyboard.append(buttons)

    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)
    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)

    keyboard.append([
        InlineKeyboardButton(text=f'{months[prev_month]}', callback_data=f'report_get_{prev_month}_{prev_year}'),
        InlineKeyboardButton(text=f'{months[month]} {year}', callback_data=ignored_cb),
        InlineKeyboardButton(text=f'{months[next_month]}', callback_data=f'report_get_{next_month}_{next_year}')
    ])

    return InlineKeyboardMarkup(keyboard)


def change_user() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для выбора пользователя"""
    buttons = [
        [InlineKeyboardButton(text=value[1], callback_data=f'get_user_{value[0]}')]
        for value in get_users()
    ]
    buttons.append([InlineKeyboardButton(text='Все', callback_data=f'get_user_all')])
    keyboard = InlineKeyboardMarkup(buttons)
    return keyboard


def report_keyboard(context) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру, для создания отчета"""
    START_DATE, END_DATE, USERS, CANCEL = range(4)

    date_now: date = date.today()

    buttons = {
        START_DATE: [
            InlineKeyboardButton(
                'Дата начала отчета',
                callback_data=f'report_get_{date_now.month}_{date_now.year}'
            )
        ],
        END_DATE: [
            InlineKeyboardButton(
                'Дата окончания отчета',
                callback_data=f'report_get_{date_now.month}_{date_now.year}'
            )
        ],
        USERS: [
            InlineKeyboardButton(
                'Пользователи',
                callback_data='report_get_users'
            )
        ],
        CANCEL: [
            InlineKeyboardButton(
                'Отмена',
                callback_data='stop_report'
            )
        ]

    }

    if not context.user_data['report']['Дата начала отчета']:
        buttons = [buttons[START_DATE]]
    elif not context.user_data['report']['Дата окончания отчета']:
        buttons = [buttons[END_DATE], buttons[CANCEL]]
    elif not context.user_data['report']['Пользователь']:
        buttons = [buttons[USERS], buttons[CANCEL]]

    return InlineKeyboardMarkup(buttons)
