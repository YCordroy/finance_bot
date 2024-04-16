import sqlalchemy as db
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, date
from copy import deepcopy

engine = db.create_engine('sqlite:///workdir/Myfin.db')
conn = engine.connect()
metadata = db.MetaData()


def get_categories():
    """Возвращает список кортежей с категориями из таблицы Категория"""
    result = conn.execute((db.text('select * from Категория')))
    return result.fetchall()


def get_users():
    """Возвращает список кортежей с пользователями из таблицы Пользователь"""
    result = conn.execute((db.text('select * from Пользователь')))
    return result.fetchall()


def insert_payments(context) -> None:
    """Сохраняет запись о трате из контекста"""
    sql = f'''
        insert into Оплата (Дата, Категория, Сумма, Комментарий, Пользователь)
        values
        (
        date('now'),
        (select max(Ключ) from Категория where Название = '{context.user_data['Категория']}'), 
        {context.user_data['Сумма']},
        '{context.user_data.get('Комментарий', '')}',
        {context.user_data['Пользователь']}
        )
    '''
    execute_no_return(sql)


def execute_fetchall(sql, params=None) -> list[dict]:
    """Возврат данных по запросу в виде словаря"""
    if params is None:
        params = {}

    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    with session.begin():
        result = session.execute(db.text(sql), params).fetchall()
        result = [row._asdict() for row in result]
    return result


def execute_fethone(sql: str, params=None) -> dict:
    """Возвраает словарь где ключи названия стобцов, значение данные из строки"""
    if params is None:
        params = {}

    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    with session.begin():
        result = session.execute(db.text(sql), params).fetchone()
        result = result._asdict()
    return result


def execute_no_return(sql) -> None:
    """Выполняет запрос sql, не требующий возврата"""
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    with session.begin():
        session.execute(db.text(sql))


def set_message_id(user: int, message_id: int) -> None:
    """Записывает id сообщения в таблицу Оплата"""
    sql = f'''
        select max(Ключ) Ключ
        from Оплата 
        where Пользователь = {user}
    '''
    key = execute_fethone(sql)['Ключ']

    sql = f'''
        update Оплата
        set [Номер сообщения] = {message_id}
        where Ключ = {key}
    '''
    execute_no_return(sql)


def re_set_category(user_id: int, message_id: int, category_id: int) -> None:
    """Изменяет категорию в базе данных"""
    sql = f'''
        update Оплата
        set Категория = {category_id}
        where Пользователь = {user_id} and [Номер сообщения] = {message_id}               
    '''
    execute_no_return(sql)


def get_waste_info(user_id: int, message_id: int) -> str:
    """Возвращает данные оплаты из базы данных в виде текста"""
    sql = f'''
        select О.Дата, К.Название, О.Сумма, О.Комментарий  
        from Оплата О
        join Категория К
        on О.Категория = К.Ключ
        where Пользователь = {user_id} and [Номер сообщения] = {message_id}
    '''
    waste_info: dict = execute_fethone(sql)
    date_waste = datetime.strptime(waste_info['Дата'], '%Y-%m-%d')
    return f'''Данные о покупке:
{date_waste.strftime('%d-%B-%Y')}
Категория: {waste_info['Название']}
Сумма: {waste_info['Сумма']}
Комментарий: {waste_info['Комментарий']}
        '''


def del_waste(user_id: int, message_id: int) -> None:
    """Удаляет строку с оплатой из базы данных"""
    sql = f'''
        delete 
        from Оплата
        where Пользователь = {user_id} and [Номер сообщения] = {message_id}   
    '''

    execute_no_return(sql)


def change_date(user_id: int, message_id: int, new_date) -> None:
    """Меняет дату в базе данных"""
    new_date = new_date.strftime('%Y-%m-%d')
    sql = f'''
        update Оплата
        set Дата = '{new_date}'
        where Пользователь = {user_id} and [Номер сообщения] = {message_id}
    '''
    execute_no_return(sql)


def add_new_user(user_id: int, user_name: str):
    """Записывает нового пользователя в таблицу Пользователь"""
    sql = f'''
    insert into Пользователь ([User id], Пользователь)
    values
    (
    {user_id},
    '{user_name}'
    )
    '''
    execute_no_return(sql)


def get_name_for_id(id: int) -> str:
    """Возвращает имя из базы данных по ключу"""
    sql = f'''
    select Пользователь
    from Пользователь
    where [User id] = {id}
    '''
    return execute_fethone(sql)['Пользователь']


def report_get_info(date_start: date, date_end: date, users: str) -> list[dict]:
    """Возвращает данные из бд для отчета"""

    sql = f'''
    select О.Дата, К.Название, О.Сумма, О.Комментарий
    from Оплата О
    join Категория К
    on О.Категория = К.Ключ
    where Пользователь in ({users}) and О.Дата between '{date_start}' and '{date_end}'
    '''
    return execute_fetchall(sql)


def report_transform_report(report_info: list[dict]) -> list[dict]:
    """Обрабатывает данные из бд, перед записью в файл"""
    # Получаем отсортированный список уникальных дат
    dates = sorted(
        set([waste['Дата'] for waste in report_info]),
        key=lambda x: datetime.strptime(x, '%Y-%m-%d')
    )

    day_info = {
        'Продукты': 0,
        'Транспорт': 0,
        'Бытовая химия': 0,
        'Здоровье': 0,
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
