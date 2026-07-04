from numpy.lib.utils import byte_bounds
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
os.environ["REDIRECT_URI"] = "https://duty-api-1.onrender.com/authted"

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
        return payload
    except JWTError:
        return None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# place for user files to be stored in the presistent disks

# creating the data base tables
create_table()
create_teams_table()
create_members_table()
create_complaints_table()
create_file_table()

app = FastAPI()
ENVIRONMENT = os.getenv("ENVIRONMENT")
if ENVIRONMENT == "production":
    # Production: strict security
    origins = [
        "https://yourwebsite.com",      # //Replace with your actual domain//
        "https://www.yourwebsite.com"   # //With www//
    ]
    allow_credentials = True
else:
    # Development: permissive
    origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)




class Data(BaseModel):
    e_num: int
    include_shift: list # a list contain 3 elements first is n shift second is pm third is am shift 1 mean allow 0 mean not
    emp_per_shift: list # determines the shift size for each shift
    holi: list = Field(default=[])  # Default holidays
    monthh: int = Field(default=0) #month that to schedule in
    vac: dict = Field(default={})  # Default vacation data
    down: str = Field(default="down")

class Filee(BaseModel):
    user_id: str
    user_email: str
    original_filename: str


class Team(BaseModel):
    user_id: str
    user_email: str
    team_name: str

class servemembers(BaseModel):
    team_id: int

class AddMemberRequest(BaseModel):
    team_id: int
    member_name: str
    member_role: Optional[int] = Field(default=None, ge=0, le=1)
    vacation_start: Optional[str] = None
    vacation_end: Optional[str] = None

class deletemember(BaseModel):
    member_id: int

class UpdateMemberRequest(BaseModel):
    member_id: int
    member_name: str
    member_role: Optional[int] = Field(default=None, ge=0, le=1)
    vacation_start: Optional[str] = None
    vacation_end: Optional[str] = None
class serveuser(BaseModel):
    user_id: str

class DeleteTeam(BaseModel):
    user_id: str
    team_name: str

class ComplaintRequest(BaseModel):
    message: str

class TeamScheduleData(BaseModel):
    team_id: int
    include_shift: list
    emp_per_shift: list
    holi: list = Field(default=[])
    monthh: int = Field(default=0)
    down: str = Field(default="down")



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
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10

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
        '''if user_info["email"] == 'darkiiq8@gmail.com':
            print('this has been axxeiejeoih')
            path = os.path.join(os.path.dirname(__file__), "templates", "admin.html")
            html_path = Path(path).read_text(encoding="utf-8")
            return HTMLResponse(content=html_path)
        print('under this is the user_id')
        print(user_info['user_id'])'''

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

    html_page = Path(path).read_text(encoding="utf-8")
    return HTMLResponse(content=html_page)

@app.post('/d')
async def get(data: Data, background_tasks: BackgroundTasks):
    print(data)
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


        vacations[int(k[h])] = lis
    T = Tframe(main_dic, main_keys, main_keys_days, week_end, month_name)  # T will fill the necessary list to be able to distribute emps shifts
    if data.monthh == 0:
        T.next_month()
    else:
        T.next_nmonth(data.monthh)
    week_end.extend(data.holi)

    e = Eframe(main_dic, main_keys, names_list, data.emp_per_shift, data, vacations, main_keys_days, week_end)

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



def _vacation_days_in_month(vacation_start, vacation_end, year, month):
    """Convert a vacation date range to a list of day strings within the target month."""
    if not vacation_start or not vacation_end:
        return []
    from datetime import date as _date
    vac_start = _date.fromisoformat(vacation_start)
    vac_end = _date.fromisoformat(vacation_end)
    month_start = _date(year, month, 1)
    month_end = _date(year, month, calendar.monthrange(year, month)[1])
    overlap_start = max(vac_start, month_start)
    overlap_end = min(vac_end, month_end)
    if overlap_start > overlap_end:
        return []
    days = []
    current = overlap_start
    while current <= overlap_end:
        days.append(str(current.day))
        current += timedelta(days=1)
    return days


@app.post('/schedule_team')
async def schedule_team(data: TeamScheduleData, background_tasks: BackgroundTasks):
    members = get_team_members(data.team_id)
    if not members:
        raise HTTPException(status_code=404, detail="Team has no members")

    # Resolve target year/month using the same logic as Tframe
    today = datetime.now()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_till_end = days_in_month - today.day
    if data.monthh == 0:
        target_date = today + timedelta(days=days_till_end + 1)
    else:
        temp = today + timedelta(days=days_till_end + 1)
        target_date = datetime(temp.year - 1, 12, 1) + relativedelta(months=data.monthh)
    target_year, target_month = target_date.year, target_date.month

    # Build names and vacations from team members
    names_list = [m['member_name'] for m in members]
    leaders = [m['member_name'] for m in members if m['member_role'] == 1]
    vacations = {
        m['member_name']: _vacation_days_in_month(
            m['vacation_start'], m['vacation_end'], target_year, target_month
        )
        for m in members
    }

    main_dic = {}
    main_keys = []
    main_keys_days = []
    week_end = []
    month_name = ''

    T = Tframe(main_dic, main_keys, main_keys_days, week_end, month_name)
    if data.monthh == 0:
        T.next_month()
    else:
        T.next_nmonth(data.monthh)
    week_end.extend(data.holi)

    class _ShiftConfig:
        def __init__(self, include_shift):
            self.include_shift = include_shift

    e = Eframe(main_dic, main_keys, names_list, data.emp_per_shift, _ShiftConfig(data.include_shift), vacations, main_keys_days, week_end, leaders=leaders)
    e.N()
    e.PM()
    e.WK()

    excel_file = e.print()
    e.count_shifts()

    if data.down == 'down':
        background_tasks.add_task(os.unlink, excel_file)
        return FileResponse(excel_file, media_type="application/octet-stream", filename=excel_file)


@app.get("/files", response_class=HTMLResponse)
async def files():
    path = os.path.join(os.path.dirname(__file__), "templates", "savedfile.html")
    html_path = Path(path).read_text(encoding="utf-8")
    return HTMLResponse(content=html_path)



@app.get("/team_schedule", response_class=HTMLResponse)
async def team_schedule_page():
    path = os.path.join(os.path.dirname(__file__), "templates", "team_schedule.html")
    return HTMLResponse(content=Path(path).read_text(encoding="utf-8"))

@app.get("/teams", response_class=HTMLResponse)
async def files():
    path = os.path.join(os.path.dirname(__file__), "templates", "teams.html")
    html_path = Path(path).read_text(encoding="utf-8")
    return HTMLResponse(content=html_path)
@app.get("/members", response_class=HTMLResponse)
async def files():
    path = os.path.join(os.path.dirname(__file__), "templates", "members.html")
    html_path = Path(path).read_text(encoding="utf-8")
    return HTMLResponse(content=html_path)

@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    path = os.path.join(os.path.dirname(__file__), "templates", "settings.html")
    return HTMLResponse(content=Path(path).read_text(encoding="utf-8"))


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    path = os.path.join(os.path.dirname(__file__), "templates", "admin.html")
    return HTMLResponse(content=Path(path).read_text(encoding="utf-8"))



@app.post("/user_teams")
async def get_teams(userr_id:serveuser):
    teams = serve_team(userr_id.user_id)
    print(teams)
    return {"teams": teams}

@app.post("/members")
async def adding_member(member_data: AddMemberRequest):
    create_members_table()
    save_new_member(
        member_data.team_id,
        member_data.member_name,
        member_data.member_role,
        member_data.vacation_start,
        member_data.vacation_end
    )
    return {"message": "Member added successfully", "status": "success"}

@app.post("/serve_members")
async def serve_member(serve_mem: servemembers):
    memrs = serving_members(serve_mem.team_id)
    return memrs

@app.post("/delete_members")
def deletee_member(delta: deletemember):
    delete_member(delta.member_id)

@app.post("/update_member")
async def editing_member(member_data: UpdateMemberRequest):
    update_member(
        member_data.member_id,
        member_data.member_name,
        member_data.member_role,
        member_data.vacation_start,
        member_data.vacation_end
    )
    return {"message": "Member updated successfully", "status": "success"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

async def get_current_admin(user: dict = Depends(get_current_user)):
    if user.get('email') != 'darkiiq8@gmail.com':
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

@app.get("/admin_data")
async def admin_data(admin: dict = Depends(get_current_admin)):
    create_complaints_table()
    return {
        "total_users": count_users(),
        "complaints": get_all_complaints()
    }

@app.post("/newteam")
async def newteam(team_data:Team,user: dict = Depends(get_current_user)):
    print(user)
    create_teams_table()
    print(team_data)
    print(team_data.team_name, user['user_id'])
    save_new_team(team_data.team_name, user['user_id'])


@app.post("/contact")
async def submit_complaint(complaint: ComplaintRequest, user: dict = Depends(get_current_user)):
    if not complaint.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    create_complaints_table()
    save_complaint(user['user_id'], user['email'], complaint.message.strip())
    return {"message": "Complaint submitted successfully", "status": "success"}


@app.post("/delete_team")
async def delete_team(request: DeleteTeam):
    success = delete_user_team(request.user_id, request.team_name)
    if success:
        return {"success": True, "message": "Team deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete team")


@app.post("/files")
async def showfile(user_iid:serveuser):
    filenames = get_user_files(user_iid.user_id)
    files_gen = []
    for filename in filenames:
        file_path = f"./temp/{user_iid.user_id}/{filename}"
        try:
            size = os.path.getsize(file_path)
        except OSError:
            size = 0
        files_gen.append({'name': filename, 'size': size})
    return files_gen



@app.post('/savefile')
async def savefile(file_data:Filee, background_tasks: BackgroundTasks):
 save_file_metadata(user_email=file_data.user_email,
                    user_id=file_data.user_id,
                    original_filename=file_data.original_filename)


 file = file_data.original_filename
 path = f'./temp/{file_data.user_id}/{file_data.original_filename}'

 os.makedirs(os.path.dirname(path), exist_ok=True)

 shutil.move(file, path)
 print_all_user_data()

 return { "message": "Upload successful!" }



@app.post('/servefile')
async def servefile(user_file:serveuser):
    #this line change to /d/temp in production
    file_path = os.path.join(f'./temp/{user_file.user_id}', "schedule.xlsx")
    print(user_file.user_id)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Return the file as a streaming response

    return FileResponse(path=file_path, filename="schedule.xlsx")

@app.post('/deletefile')
async def deletefile(user_file:Filee):
    delete_user_file(user_file.user_email)

'''@app.post('/admin')
async def admin(admin_id:servefile):
    if admin_id == 'darkiiq8@gmail.com':
        return 'meow'''




# remember use uvicorn {thjsfilename}:{fastapi varible} --reload
#uvicorn package.backend_api:app --reload

# if i dont have postman use the route /docs automaticly shows me what i need
