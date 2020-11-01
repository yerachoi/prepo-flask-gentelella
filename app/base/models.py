from bcrypt import gensalt, hashpw
from flask_login import UserMixin
from sqlalchemy import Binary, Boolean, Column, Integer, String
from sqlalchemy import DateTime, ForeignKey, Text, UnicodeText
from sqlalchemy.orm import backref, relationship

from app import db, login_manager


class User(db.Model, UserMixin):

    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(Binary)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]
            if property == 'password':
                value = hashpw(value.encode('utf8'), gensalt())
            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)


@login_manager.user_loader
def user_loader(id):
    return User.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    return user if user else None


class Url(db.Model):

    __tablename__ = 'Url'

    id = Column(Integer, primary_key=True)
    url = Column(UnicodeText(), unique=True, nullable=False)
    plink_date = Column(DateTime(), nullable=False)
    saved_date = Column(DateTime())
    scrap_result = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('User.id', ondelete='CASCADE'), nullable=False)
    user = relationship('User', backref=backref('url_set'))


class Document(db.Model):

    __tablename__ = 'Document'

    id = Column(Integer, primary_key=True)
    title = Column(UnicodeText())
    publish_date = Column(DateTime())
    text_raw = Column(UnicodeText(), nullable=False)
    text_sum = Column(UnicodeText())
    text_prep = Column(UnicodeText(), nullable=False)
    clip_date = Column(DateTime(), nullable=False)
    crawl_date = Column(DateTime(), nullable=False)
    is_news = Column(Boolean())
    url_id = Column(Integer, ForeignKey('Url.id'))
    url = relationship('Url', backref=backref('doc_set'))
    # user_id = Column(Integer, ForeignKey('User.id', ondelete='CASCADE'), nullable=False)
    # user = relationship('User', backref=backref('url_set'))