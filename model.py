from pydantic import BaseModel,EmailStr
from datetime import datetime

class Blogs(BaseModel):
    heading:str
    title:str
    image_url:str
    
class Users(BaseModel):
    
    username:str
    email:EmailStr
    mobileno:str
    password :str
    is_active :bool = False
    created_at : datetime = datetime.now()
    