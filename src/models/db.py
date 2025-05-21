from datetime import datetime

import bcrypt
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    _password_hash = Column(String, nullable=False)
    last_login = Column(DateTime)

    @property
    def password(self):
        raise AttributeError("password: write-only field")

    @password.setter
    def password(self, password):
        self._password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password):
        return bcrypt.checkpw(password.encode(), self._password_hash.encode())


class Chatroom(Base):
    __tablename__ = 'chatrooms'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    chatroom_id = Column(Integer, ForeignKey('chatrooms.id'))
    sender_user_id = Column(Integer, ForeignKey('users.id'))
    receiver_user_id = Column(Integer, ForeignKey('users.id'))
    text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
