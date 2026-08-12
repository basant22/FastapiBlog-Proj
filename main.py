import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import bcrypt
import jwt
import shutil
from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from fastapi.staticfiles import StaticFiles
from database import Base,engine,sessionlocal
import dbmodel
from dbmodel import User,Blog
import auth
from model import Blogs,Users
import uvicorn
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
# =====================================================================
# 1. Database Configuration
# =====================================================================
UPLOAD_DIR = 'uploads'
FILE_URL = 'http://127.0.0.0:8000/'
DATABASE_URL = "sqlite:///./app.db"
# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()


# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True, nullable=False)
#     password = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def my_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================================
# 2. Security & Auth Utilities
# =====================================================================
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30


def get_password_hash(password: str) -> str:
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    prepared_pwd = base64.b64encode(digest)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(prepared_pwd, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    digest = hashlib.sha256(plain_password.encode("utf-8")).digest()
    prepared_pwd = base64.b64encode(digest)
    return bcrypt.checkpw(prepared_pwd, hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_from_cookie(request: Request, db: Session = Depends(my_db)) -> Optional[User]:
    token = request.cookies.get("access_token")
    print("Token from current User",token)
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("payload",payload)
        email: str = payload.get("sub")
        if email is None:
            return None
        return db.query(dbmodel.User).filter(dbmodel.User.email == email).first()
    except jwt.PyJWTError:
        return None


# =====================================================================
# 3. App Initialization & Routes
# =====================================================================
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
# app.mount("/files",StaticFiles(directory=UPLOAD_DIR),name="files")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def root():
    # Redirect visitors from http://127.0.0.1:8000/ directly to /login
    return RedirectResponse(url="/login")
# --- Registration Routes ---
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
   return templates.TemplateResponse(
    request=request, 
    name="register.html", 
    context={"error": None}
)




# --- Login Routes ---
@app.get("/login", response_class=HTMLResponse)
def login(request: Request, registered: bool = False):
    msg = "Account created successfully! Please login." if registered else None
    return templates.TemplateResponse(
        name="login.html",
        request=request,
        context={'message':msg},
        status_code=status.HTTP_302_FOUND
        )


@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(my_db),
    user:User = Depends(get_current_user_from_cookie)
):
    print(f"Login attempt - Email: {email}, Password length: {len(password)}")
    user = db.query(dbmodel.User).filter(dbmodel.User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            name="login.html",
            request=request,
            context= {"error": "Invalid email or password.", "message": None},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Generate JWT Token
    access_token = auth.create_access_token(data={"sub": email})
    refresh_token = auth.create_refresh_token(data={"sub": email})
   
    # Set HttpOnly Cookie and Redirect to Dashboard
    response = RedirectResponse(url="/create-blog", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,  # Prevents client-side JS theft
            secure=False,   # Set to True in production with HTTPS
            samesite="lax",
            max_age=1800,   # 30 minutes (optional)
            path="/",       # Cookie available for all paths
        )
    response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=604800, # 7 days
            path="/",
        )
    return response

# show profile page
@app.get("/profile",response_class=HTMLResponse)
def show_profile(request:Request,user: Optional[User] = Depends(get_current_user_from_cookie)):
    if not user:
        return RedirectResponse(url="/login",status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        name="profile.html",
        request=request,
        context={"user":user}
                                      
                                      )
    
# --- Protected Dashboard Route ---
@app.get("/blogs", response_class=HTMLResponse)
def blogs(
    request: Request,
    db:Session = Depends(my_db),
    user: User = Depends(get_current_user_from_cookie),
    success:bool = False,
):
    # Unauthenticated users are redirected back to login
    if user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    blogs = db.query(Blog).filter(Blog.user_id == user.id).all()
    if blogs :
        return templates.TemplateResponse( 
                                     name="blogs.html", 
                                      request=request,
                                      context={"user": user,'blogs':blogs},
                                      status_code=status.HTTP_302_FOUND
                                      )
                                    
    return templates.TemplateResponse( name="blogs.html", 
                                      request=request,
                                      context={"user": user,'blogs':[]},
                                      status_code=status.HTTP_302_FOUND
                                      ) 

# --- Logout Route ---
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

@app.post('/register')
def register(
    request:Request,
    username:str = Form(...),
    email:str = Form(...),
    mobilenumber:str = Form(...),
    password:str = Form(...),
    confirmpassword:str = Form(...),
    db:Session = Depends(my_db)
    ):
    try:
        print(f"Login attempt - Email: {email}, Password length: {len(password)}")
        if password != confirmpassword:
            return templates.TemplateResponse(
               name='register.html',
               request=request,
               context={'error':"Password does not matched"},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        user = db.query(dbmodel.User).filter(dbmodel.User.email==email,dbmodel.User.mobileno == mobilenumber).first() 
        if user:
            # raise HTTPException(
            #     status_code=401,
            #     detail='User already exist'
            # ) 
            return templates.TemplateResponse(
                name='register.html',
                request=request,
                context={'error':'User already exist'},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        hash_password = get_password_hash(password)
        dbuser = dbmodel.User(
            username=username,
            email=email,
            mobileno=mobilenumber,
            hashed_password=hash_password
            )
        # newuser = dbmodel.User(
        #     username=username,
        #     email=email,
        #     mobileno=mobilenumber,
        #     )
        db.add(dbuser)
        db.commit()    
        # db.refrsh(newuser)
        # return{
        #     'status':'succes',
        #     'message':'User registered successfully',
        #     'user':newuser
        # }
        return RedirectResponse(
            url='/login?registered=true',
             status_code=status.HTTP_302_FOUND
                                )
    except Exception as e:
        raise HTTPException(
                 status_code=401,
                 detail=f'Facing error:{str(e)} while register user'
             )    



@app.get('/create-blog',response_class=HTMLResponse)
def create_blog(
     request:Request,
     user: User = Depends(get_current_user_from_cookie),
    ):
    print('Create-Blog',user.id)
    # If user exists, show the create blog page
    if user:
        return templates.TemplateResponse(
            name='createblog.html',
            request=request,
            context={
                "user": user,
                # Add any other context data needed
            }
        )
    else:
        # If no user, redirect to login
        return RedirectResponse(
            url="/login", 
            status_code=status.HTTP_302_FOUND
        )

@app.post('/create-blog')
async def creat_blog(
    request: Request,
    heading: str = Form(...),          # ← Use Form() for form data
    title: str = Form(...),            # ← Use Form() for form data
    file: UploadFile = File(...),      # ← Use File() for file uploads
    db: Session = Depends(my_db),
    user:User = Depends(get_current_user_from_cookie)
):
    try:
        print(f"Creating blog - Heading: {heading}, Title: {title}")
        print(f"File: {file.filename}")
       
        print(f"user: {user.id}")
        if not user:
             return templates.TemplateResponse(
                name='createblog.html',
                 request=request,
                  context={
                    "error": "Not authorizd",
                },
                   status_code=status.HTTP_302_FOUND
            )
        if not title or not heading:
             return templates.TemplateResponse(
                name='createblog.html',
                 request=request,
                  context={
                    "error": "Heading and title are required",
                    "heading": heading,
                    "title": title
                },
                   status_code=status.HTTP_302_FOUND
            )
        if file and file.filename:
            
            os.makedirs('static/uploads',exist_ok=True)
            #create uniq name 
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fileExt = os.path.splitext(file.filename)[1]
            uniq_name = f"{timestamp}_{user.id}{fileExt}"
            file_path = f"static/uploads/{uniq_name}"
            print('file_path',file_path)
            #save file
            with open(file_path,'wb') as buffer:
                shutil.copyfileobj(file.file,buffer)
            image_url = f"/static/uploads/{uniq_name}"   
            # print('image_url',image_url)
            new_blog = Blog(heading=heading,title=title,image_url=image_url,user_id=user.id)
            db.add(new_blog)
            db.commit()
            db.refresh(new_blog)
            
            return RedirectResponse(
                url="/blogs?success=true",
                 status_code=status.HTTP_302_FOUND
            )
           
        else:
            return templates.TemplateResponse(
                 name='createblog.html',
                 request=request,
                 context={
                     'error':'No file found'
                 },
                   status_code=status.HTTP_302_FOUND
            )        
            
            return templates.TemplateResponse(
                name='createblog.html',
                 request=request,
                   status_code=status.HTTP_302_FOUND
            )
    except Exception as e:
            return templates.TemplateResponse(
                name='createblog.html',
                 request=request,
                 context={'error':str(e)},
                status_code=status.HTTP_302_FOUND
            )    
     
    

if __name__ == "__main__":
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)