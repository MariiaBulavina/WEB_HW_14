from sqlalchemy import Column, ForeignKey, Integer, String, func, Date, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class Contact(Base):

    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, index=True)
    last_name = Column(String(50), nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=True, index=True)
    phone = Column(String(150), unique=True, nullable=False, index=True)
    born_date = Column(Date, nullable=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    user_id = Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), default=None)
    user = relationship('User', backref='contacts', lazy='joined')

   
class User(Base):
    
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)



