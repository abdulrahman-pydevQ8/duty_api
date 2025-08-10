from starlette.responses import FileResponse
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import BackgroundTasks, File, UploadFile
import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests
from dotenv import load_dotenv
from pathlib import Path
import random
import pandas as pd
from datetime import timedelta
import shutil

from datetime import timedelta
import calendar
from dateutil.relativedelta import relativedelta
from openpyxl import load_workbook
import copy
from openpyxl.styles import PatternFill, Alignment
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from .timeframe import Tframe
from .employeframe import Eframe
from.databasefunctions import *


from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional

# this class is responsible for the dates in general


load_dotenv()
# Load manually
os.environ["REDIRECT_URI"] = "http://127.0.0.1:8000/authted"

# Then retrieve it like usual
redirect_uri = os.getenv("REDIRECT_URI")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")




# Security configurations for the token
SECRET_KEY = "YOUR_SECRET_KEY"  # Generate a secure random key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30




def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Verify token
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# place for user files to be stored in the presistent disks

# creating the data base tables
create_table()
create_file_table()

app = FastAPI()
origins = [
    "http://127.0.0.1:3000",  # Allow Flask (front-end) to make requests
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"], )  # Allow all headers




class Data(BaseModel):
    e_num: int
    n_shift: int
    e_shift: int
    holi: list = Field(default=[])  # Default holidays
    monthh: int = Field(default=0)
    vac: dict = Field(default={})  # Default vacation data
    down: str = Field(default="down")

class Filee(BaseModel):
    user_id: str
    user_email: str
    original_filename: str


class servefile(BaseModel):
    user_id: str



@app.get("/auth")
async def auth():
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&scope=email%20profile"  # Requesting access to user's email and profile info
        f"&access_type=offline"  # So we can get a refresh token
        f"&prompt=consent"  # Forces the consent screen to appear every time
    )

    # Redirect user to Google's authorization page
    return RedirectResponse(url=auth_url)


@app.get("/authted")
async def authted(code: str = None, error: str = None):
    if error:
        return {"status": "error", "message": f"Authentication failed: {error}"}

        # If no code is provided, that's also an error
    if not code:
        return {"status": "error", "message": "No authentication code received"}

    try:
        # Exchange the authorization code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            ""
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        # Make the request to Google's token endpoint
        token_response = requests.post(token_url, data=token_data)

        # Check if the token request was successful
        if token_response.status_code != 200:
            return {
                "status": "error",
                "message": f"Failed to retrieve token: {token_response.text}"
            }

        # Parse the token response
        token_json = token_response.json()
        id_token_value = token_json.get("id_token")

        # Verify the ID token
        id_info = id_token.verify_oauth2_token(
            id_token_value,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        # Extract user information
        user_info = {
            "user_id": id_info["sub"],
            "email": id_info["email"],
            "name": id_info.get("name", ""),
            "picture": id_info.get("picture", "")
        }

        bol = user_exists(user_info["email"])
        if bol :
            print_user_data(user_info["email"])
        else:save_new_user(user_info['name'],user_info["email"])

        user_info = {
            "user_id": user_id(id_info["email"]),
            "email": id_info["email"],
            "name": id_info.get("name", ""),
            "picture": id_info.get("picture", "")
        }
        print('under this is the user_id')
        print(user_info['user_id'])

        # Here you would typically:
        # 1. Check if this user exists in your database
        # 2. Create a new user if they don't exist
        # 3. Generate a session or JWT for the user
        access_token = create_access_token(data=user_info, expires_delta=timedelta(minutes=15))
        # For now, just return the user information as JSON
        html_content = f"""
           <html>
               <head>
                   <script>
                       // Store the token (you can change localStorage to sessionStorage if needed)
                       localStorage.setItem("token", "{access_token}");

                       // Redirect to homepage
                       window.location.href = "/";
                   </script>
               </head>
               <body>
                   Redirecting...
               </body>
           </html>
           """
        return HTMLResponse(content=html_content)


    except Exception as e:
        return {"status": "error", "message": f"Authentication error: {str(e)}"}

@app.get("/", response_class=HTMLResponse)
async def read_root():
    path = os.path.join(os.path.dirname(__file__), "templates", "homepage.html")
    html_path = Path(path).read_text(encoding="utf-8")
    return HTMLResponse(content=html_path)



@app.get('/d', response_class=HTMLResponse)
async def dis():
    path = os.path.join(os.path.dirname(__file__), "templates", "index.html")

    html_page = Path(path).read_text()
    return HTMLResponse(content=html_page)

@app.post('/d')
async def get(data: Data, background_tasks: BackgroundTasks):
    global names_list, vacations, month_name, week_end
    #if data.e_num <=20:
    #   data.e_num = 30





    main_dic = {}  # each key is a date and contains the names of people who are working on these days
    main_keys = []  # a list of each key easier to handle
    main_keys_days = []  # names of the dates like m for monday
    week_end = []
    month_name = ''





    names_list = list(range(1, data.e_num + 1))
    vacations = {key: [] for key in names_list}
    tot = len(data.vac.keys())
    k = list(data.vac.keys())
    for h in range(tot):
        # print(f"this is vac_k[h] {data.vac[k[h]]}")
        # print(f"this is k[h] {k[h]}")

        lis = []
        # print(data.vac[k[h]][0])
        for i in range(int(data.vac[k[h]][0]), int(data.vac[k[h]][1]) + 1):  # +1 to include the end number
            lis.append(str(i))

        vacations[k[h]] = lis


    T = Tframe(main_dic, main_keys, main_keys_days, week_end, month_name)  # T will fill the necessary list to be able to distribute emps shifts
    if data.monthh == 0:
        T.next_month()
    else:
        T.next_nmonth(data.monthh)
    week_end.extend(data.holi)

    e = Eframe(main_dic, main_keys, names_list, data.e_shift, data, vacations, main_keys_days, week_end)

    e.N()
    e.PM()
    e.WK()

    excel_file = e.print()

    e.count_shifts()
    file_path = excel_file
    # Path to the file
    if data.down == 'down':
        background_tasks.add_task(os.unlink, file_path)

    '''if data.save == True:
        pass
    else:'''
    if data.down == 'down':
        return FileResponse(file_path,
                            media_type="application/octet-stream",
                            filename=f'{file_path}')
    else:return print('did gene the file but did not download')



@app.get("/files", response_class=HTMLResponse)
async def files():
    path = os.path.join(os.path.dirname(__file__), "templates", "savedfile.html")
    html_path = Path(path).read_text(encoding="utf-8")
    return HTMLResponse(content=html_path)

@app.post("/files")
async def showfile(user_iid:servefile):
    files_gen = {
        'name': 'schedule.xlsx',
        "size": (os.path.getsize(f"temp/{user_iid.user_id}/schedule.xlsx"))
    }

    return files_gen



@app.post('/savefile')
async def savefile(file_data:Filee, background_tasks: BackgroundTasks):
 save_file_metadata(user_email=file_data.user_email,
                    user_id=file_data.user_id,
                    original_filename=file_data.original_filename)


 file = file_data.original_filename
 path = f'/d/temp/{file_data.user_id}/{file_data.original_filename}'

 os.makedirs(os.path.dirname(path), exist_ok=True)

 shutil.move(file, path)
 print_all_user_data()

 return { "message": "Upload successful!" }



@app.post('/servefile')
async def servefile(user_file:servefile):
    file_path = os.path.join(f'temp/{user_file.user_id}', "schedule.xlsx")
    print(user_file.user_id)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Return the file as a streaming response

    return FileResponse(path=file_path, filename="schedule.xlsx")

@app.post('/deletefile')
async def deletefile(user_file:Filee):
    delete_user_file(user_file.user_email)




# remember use uvicorn {thjsfilename}:{fastapi varible} --reload
#uvicorn package.backend_api:app --reload

# if i dont have postman use the route /docs automaticly shows me what i need
