from sqlalchemy import (
    Integer,
    String,
    Date,
    Float,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    mapped_column,
    Session
)
from sqlalchemy.dialects.sqlite import insert
from Settings import engine, user_dict


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'Пользователь'

    id = mapped_column(
        'User id',
        Integer,
        primary_key=True
    )

    name = mapped_column('Пользователь', String)


class Category(Base):
    __tablename__ = 'Категория'

    id = mapped_column(
        'Ключ',
        Integer,
        primary_key=True
    )
    name = mapped_column(
        'Название',
        String,
        unique=True
    )


class Waste(Base):
    __tablename__ = 'Оплата'

    id = mapped_column(
        'Ключ',
        Integer,
        primary_key=True
    )
    message_id = mapped_column('Номер сообщения', Integer)
    date = mapped_column('Дата', Date)
    category = mapped_column(
        'Категория',
        Integer,
        ForeignKey('Категория.Ключ')
    )
    total = mapped_column('Сумма', Float)
    comment = mapped_column('Комментарий', Text)
    user = mapped_column('Пользователь', Integer)

    @classmethod
    def get_message(cls, db: Session, user_id: int, message_id: int):
        return db.query(cls).filter(
            Waste.user == user_id,
            Waste.message_id == message_id
        )


def add_categories():
    categories = [
        {'name': 'Продукты'},
        {'name': 'Транспорт'},
        {'name': 'Быт'},
        {'name': 'Здоровье'},
        {'name': 'Саша'},
        {'name': 'Коммунальные услуги'},
        {'name': 'Развлечения'},
        {'name': 'Еда вне дома'},
        {'name': 'Другое'}
    ]

    with Session(autoflush=False, bind=engine) as db:
        db.execute(
            (
                insert(Category)
                .prefix_with('OR IGNORE')
                .values(categories)
            )
        )
        db.commit()


def add_users():
    users = [
        {'User id': key, 'Пользователь': value}
        for key, value in user_dict.items()
    ]
    with Session(autoflush=False, bind=engine) as db:
        db.execute(
            (
                insert(User)
                .prefix_with('OR IGNORE')
                .values(users)
            )
        )
        db.commit()
