from datetime import date
from copy import deepcopy

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from Tables import (
    Waste,
    Category,
    User
)
from Settings import engine


def get_categories():
    """Возвращает список кортежей с категориями из таблицы Категория"""
    with Session(autoflush=False, bind=engine) as db:
        return db.query(Category.id, Category.name).all()


def get_users():
    """Возвращает список кортежей с пользователями из таблицы Пользователь"""
    with Session(autoflush=False, bind=engine) as db:
        return db.query(User.id, User.name).all()


def insert_payments(context) -> None:
    """Сохраняет запись о трате из контекста"""
    with Session(autoflush=False, bind=engine) as db:
        subquery = (
            select(Category.id)
            .where(Category.name == context.user_data['Категория'])
            .scalar_subquery()
        )
        db.add(
            Waste(
                date=date.today(),
                category=subquery,
                total=context.user_data['Сумма'],
                comment=context.user_data.get('Комментарий', ''),
                user=context.user_data['Пользователь']
            )
        )
        db.commit()


def set_message_id(user: int, message_id: int) -> None:
    """Записывает id сообщения в таблицу Оплата"""
    with Session(autoflush=False, bind=engine) as db:
        key = (
            db.query(func.max(Waste.id))
            .where(Waste.user == user)
            .scalar()
        )
        waste = db.query(Waste).get(key)
        waste.message_id = message_id
        db.merge(waste)
        db.commit()


def re_set_category(user_id: int, message_id: int, category_id: int) -> None:
    """Изменяет категорию в базе данных"""
    with Session(autoflush=False, bind=engine) as db:
        Waste.get_message(db, user_id, message_id).update(
            {'Категория': category_id},
            synchronize_session=False
        )
        db.commit()


def get_waste_info(user_id: int, message_id: int) -> str:
    """Возвращает данные оплаты из базы данных в виде текста"""
    with Session(autoflush=False, bind=engine) as db:
        message = db.query(
            Waste,
            Category
        ).join(
            Category, Waste.category == Category.id
        ).filter(
            Waste.user == user_id,
            Waste.message_id == message_id
        ).first()
    return f'''Данные о покупке:
{message.Waste.date.strftime('%d-%B-%Y')}
Категория: {message.Category.name}
Сумма: {message.Waste.total}
Комментарий: {message.Waste.comment}
        '''


def del_waste(user_id: int, message_id: int) -> None:
    """Удаляет строку с оплатой из базы данных"""
    with Session(autoflush=False, bind=engine) as db:
        message = Waste.get_message(db, user_id, message_id).scalar()
        db.delete(message)
        db.commit()


def change_date(user_id: int, message_id: int, new_date) -> None:
    """Меняет дату в базе данных"""
    with Session(autoflush=False, bind=engine) as db:
        waste = Waste.get_message(db, user_id, message_id).scalar()
        waste.date = new_date
        db.merge(waste)
        db.commit()


def get_name_for_id(user_id: int) -> str:
    """Возвращает имя из базы данных по ключу"""
    with Session(autoflush=False, bind=engine) as db:
        return db.query(User.name).filter(User.id == user_id).scalar()


def report_get_info(date_start: date, date_end: date, users: str) -> list[dict]:
    """Возвращает данные из бд для отчета"""
    users = [int(user.strip()) for user in users.split(',')]
    with Session(autoflush=False, bind=engine) as db:
        results = db.query(
            Waste.date,
            Category.name.label('name'),
            Waste.total,
            Waste.comment
        ).join(
            Category, Waste.category == Category.id
        ).filter(
            Waste.user.in_(users),
            Waste.date.between(date_start, date_end)
        ).all()

    # Переводим в список словарей, дял дальнейшей обработки
    waste_info_list = []
    for result in results:
        waste_info_list.append({
            'Дата': result.date.strftime('%d-%B-%Y'),
            'Название': result.name,
            'Сумма': result.total,
            'Комментарий': result.comment
        })
    return waste_info_list


def report_transform_report(report_info: list[dict]) -> list[dict]:
    """Обрабатывает данные из бд, перед записью в файл"""
    # Получаем отсортированный список уникальных дат
    dates = sorted(
        set([waste['Дата'] for waste in report_info]),
        # key=lambda x: datetime.strptime(x, '%Y-%m-%d')
    )

    day_info = {
        'Продукты': 0,
        'Транспорт': 0,
        'Быт': 0,
        'Здоровье': 0,
        'Саша': 0,
        'Коммунальные услуги': 0,
        'Развлечения': 0,
        'Еда вне дома': 0,
        'Другое': 0,
        'Комментарий': []
    }

    report = {date: deepcopy(day_info) for date in dates}

    # Суммируем дневные траты по категориям и составляем список комментариев
    for waste in report_info:
        day = report[waste['Дата']]
        day[waste['Название']] += waste['Сумма']
        if waste['Комментарий']:
            day['Комментарий'].append(waste['Комментарий'])

    # Добавляем дату и оъединяем комментарий в строку
    for key in report:
        report[key]['Дата'] = key
        report[key]['Комментарий'] = ', '.join(report[key]['Комментарий'])

    day_info['Дата'] = 'Итого'
    report = list(report.values())

    # Суммируем траты по категориям за весь временной отрезок
    for day in report:
        for key, value in day.items():
            if key not in ('Дата', 'Комментарий'):
                day_info[key] = day_info.get(key) + value
    day_info['Комментарий'] = sum(
        [value for key, value in day_info.items() if key not in ('Дата', 'Комментарий')]
    )
    report.append(day_info)

    return report
