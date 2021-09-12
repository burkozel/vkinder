import json
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from infons import *

Base = declarative_base()
engine = sq.create_engine(db)
Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer)
    user_name = sq.Column(sq.String)
    age = sq.Column(sq.String)

class DatingUser(Base):
    __tablename__ = 'datinguser'
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer)
    user_name = sq.Column(sq.String)
    id_User = sq.Column(sq.Integer, sq.ForeignKey('user.id'))
    user = relationship(User)

def create_tables():
    Base.metadata.create_all(engine)

def add_user(user):
    session.expire_on_commit = False
    session.add(user)
    session.commit()

def view_all(user_id):
    links = []
    query = session.query(DatingUser)
    for j in query:
        links.append(j.vk_id)
    return links

def write_in_db():
    create_tables()
    with open('info.json', 'r', encoding='utf8') as f:
        data = json.load(f)
        for i in data[0]['people']:
            create_tables()
            user = User(vk_id=i['vk_id'], user_name=i['user_name'],
                        age=i['age'])
            add_user(user)
        for i in data[0]['favorite']:
            searching_user = DatingUser(vk_id=i['vk_id'], user_name=i['user_name'],
                                        id_User=user.id)
            add_user(searching_user)
