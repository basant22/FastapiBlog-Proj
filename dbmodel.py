from sqlalchemy import Column, Integer, String, Boolean, DateTime,ForeignKey
from database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key= True,index=True)
    username = Column(String,nullable=False,unique=True,index=True)
    email = Column(String,nullable=False,unique=True,index=True)
    mobileno = Column(String,nullable=False,unique=True,index=True)
    hashed_password =  Column(String,nullable=False)
    is_active = Column(Boolean,default=False)
    created_at = Column(DateTime, default=datetime.now())
    blog = relationship('Blog',back_populates='owner')
   
    
class Blog(Base):
    __tablename__ = "blogs"
    
    id = Column(Integer,primary_key=True,autoincrement=True,index=True)
    heading = Column(String,nullable=False,index=True)
    title = Column(String,nullable=False,index=True)
    image_url = Column(String,nullable=False,index=True)
    created_at = Column(DateTime, default=datetime.now())
    user_id = Column(Integer , ForeignKey('users.id'))
    owner  = relationship("User",back_populates='blog')
        