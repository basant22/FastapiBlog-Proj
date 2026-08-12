from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from config import setting


engine = create_engine(setting.connstr,connect_args={"check_same_thread":False})
sessionlocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
