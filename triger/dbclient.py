from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from sqlalchemy.sql import and_


class DBClient:

    def __init__(self, db_host, db_name, db_user, db_password):
        self.engine = create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}')
        self.metadata = MetaData()

        self.targets = Table(
            'targets', self.metadata,
            Column('creator_id', Integer),
            Column('target', String),
            Column('schedule', Integer),
            Column('tags', String)
        )

        self.user_chats = Table(
            'user_chats', self.metadata,
            Column('username', String),
            Column('chat_id', Integer)
        )

    def insert_user_chat(self, chat_id, username):
        query = insert(self.user_chats).values(username=username, chat_id=chat_id).on_conflict_do_nothing()
        with self.engine.connect() as connection:
            connection.execute(query)
            connection.commit()

    def find_user_by_name_and_type(self, username, type):
        query = select(self.targets).where(and_(self.targets.c.target == username,self.targets.c.schedule == type))
        with self.engine.connect() as connection:
            res = connection.execute(query).one_or_none()
            connection.commit()
        return res

    def find_users_by_type(self, type):
        query = select(self.targets).where(self.targets.c.schedule == type)
        with self.engine.connect() as connection:
            users = connection.execute(query)
            connection.commit()
        return users

    def find_user_chats(self, username):
        query = select(self.user_chats).where(self.user_chats.c.username == username)
        with self.engine.connect() as connection:
            chats = connection.execute(query)
            connection.commit()
        return chats