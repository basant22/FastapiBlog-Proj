from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    connstr = os.getenv('conn_string')
    secretkey = os.getenv('SECRET_KEY')
    algoritham = os.getenv('ALGORITHM')
    expireinminutes = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
    expireindays = os.getenv('REFRESH_TOKEN_EXPIRE_DAYS')
    
setting = Settings()    