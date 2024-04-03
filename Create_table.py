from datab import db, metadata, engine, add_new_user
from sqlalchemy.orm import sessionmaker, scoped_session


def create_category() -> None:
    """Создает таблицу в базе данных с категориями из списка categores"""
    db.Table(
        'Категория',
        metadata,
        db.Column('Ключ', db.Integer, primary_key=True),
        db.Column('Название', db.String, unique=True)
    )

    metadata.create_all(engine)

    categores = [
        'Продукты',
        'Транспорт',
        'Бытовая химия',
        'Здоровье',
        'Коммунальные услуги',
        'Развлечения',
        'Еда вне дома',
        'Другое'
    ]

    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()

    for category in categores:
        session.execute(db.text(f'''
            insert into Категория (Название)
             values ('{category}')
        '''))
    session.commit()


def create_wastes() -> None:
    """Создает таблицу в базе данных с тратами"""
    db.Table(
        'Оплата',
        metadata,
        db.Column('Ключ', db.Integer, primary_key=True),
        db.Column('Номер сообщения', db.Integer),
        db.Column('Дата', db.Date),
        db.Column('Категория', db.Integer),
        db.Column('Сумма', db.Float),
        db.Column('Комментарий', db.Text),
        db.Column('Пользователь', db.Integer)
    )

    metadata.create_all(engine)


def create_user() -> None:
    """Создает таблицу с пользователями"""
    db.Table(
        'Пользователь',
        metadata,
        db.Column('User id', db.Integer, primary_key=True),
        db.Column('Пользователь', db.String)
    )
    metadata.create_all(engine)
