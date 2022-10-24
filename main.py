from enum import Enum
from typing import Optional, List, Dict
from uuid import UUID, uuid1

from fastapi import FastAPI, Form, Cookie, Header, Response
from pydantic import BaseModel

from bcrypt import hashpw, gensalt, checkpw
from datetime import date, datetime

from string import ascii_lowercase
from random import random

app = FastAPI()

valid_users = dict()
pending_users = dict()
valid_profiles = dict()
discussion_posts = dict()

class User(BaseModel):
    username: str
    password: str
    
class ValidUser(BaseModel):
    id: UUID
    username: str
    password: str
    passphrase: str

class UserType(str, Enum):
    admin = "admin"
    teacher = "teacher"
    alumni = "alumni"
    student = "student"

class PostType(str, Enum):
    information = "information" 
    inquiry = "inquiry"
    quote = "quote"
    twit = "twit"

class UserProfile(BaseModel):
    firstname: str
    lastname: str
    middle_initial: str
    age: Optional[int] = 0
    salary: Optional[int] = 0
    birthday: date
    user_type: UserType

class ForumPost(BaseModel):
    id: UUID
    topic: Optional[str] = None
    message: str
    post_type: PostType
    date_posted: datetime
    username: str

class ForumDiscussion(BaseModel):
    id: UUID
    main_post: ForumPost
    replies: Optional[List[ForumPost]] = None
    author: UserProfile


@app.get("/ch01/index")
def index():
 return {"message": "Welcome FastAPI Nerds"} 

@app.get("/ch01/login")
def login(username: str, password: str):
    if valid_users.get(username) == None:
        return { "message": "User does not exist" }
    user = valid_users.get(username)
    if checkpw(password.encode(), user.passphrase.encode()):
        return user
    return { "message": "Invalid user" }

@app.post("/ch01/login/signup")
def signup(uname: str, passwd: str):
    if (uname == None and passwd == None):
        return {"message": "invalid user"}
    
    if not valid_users.get(uname) == None:
        return {"message": "user exists"}
    
    user = User(username=uname, password=passwd)
    pending_users[uname] = user
    return user

@app.post("/ch01/account/profile/add", response_model=UserProfile)
def add_profile(uname: str, 
                fname: str = Form(...), 
                lname: str = Form(...),
                mid_init: str = Form(...),
                user_age: int = Form(...),
                sal: float = Form(...),
                bday: str = Form(...),
                utype: UserType = Form(...)):
    if valid_users.get(uname) == None:
        return UserProfile(firstname=None, lastname=None, middle_initial=None, age=None, birthday=None, salary=None, user_type=None)
    
    profile = UserProfile(firstname=fname, lastname=lname, middle_initial=mid_init, age=user_age, birthday=datetime.strptime(bday, '%m/%d/%Y'), salary=sal, user_type=utype)
    valid_profiles[uname] = profile
    return profile

@app.put("/ch01/account/profile/update/{username}")
def update_profile(username: str, id: UUID, new_profile: UserProfile):
    if valid_users.get(username) == None:
        return {"message": "user does not exist"}
    user = valid_users.get(username)
    if user.id == id:
        valid_profiles[username] = new_profile
        return {"message": "successfully updated"}
    return {"message": "user does not exist"}

@app.patch("/ch01/account/profile/update/names/{username}")
def update_profile_names(id: UUID, username: str = '', new_names: Optional[Dict[str, str]] = None):
    if valid_users.get(username) == None:
        return {"message": "user does not exist"}
    if new_names == None:
        return {"message": "invalid names"}
    
    user = valid_users.get(username)
    if user.id == id:
        profile = valid_profiles.get(username)
        profile.firstname = new_names.get("firstname")
        profile.lastname = new_names.get("lastname")
        profile.middle_initial = new_names.get("middle_initial")
        return {"message": "successfully updated"}
    return {"message": "user does not exist"}

@app.delete("/ch01/discussion/posts/remove/{username}")
def delete_discussion(username: str, id: UUID):
    if valid_users.get(username) == None:
        return {"message": "user does not exist"}
    if discussion_posts.get(id) == None:
        return {"message": "post does not exist"}
    del discussion_posts[id] 
    return {"message": "main post deleted"}

@app.delete("/ch01/login/remove/all")
def delete_users(usernames: List[str]):
    for username in usernames:
        del valid_users[username]
    return {"message": "users deleted"}

@app.delete("/ch01/login/remove/{username}")
def delete_user(username: str):
    if username == None:
        return {"message": "invalid user"}
    del valid_users[username]
    return {"message": "user deleted"}

@app.get("/ch01/login/details/info")
def login_info():
    return {"message": "username and password are needed"}

@app.get("/ch01/login/{username}/{password}")
def login_with_token(username: str, password: str, id: UUID):
    if valid_users.get(username) == None:
        return {"message": "user does not exist"}
    user = valid_users.get(username)
    if user.id == id and checkpw(password.encode(), user.passphrase.encode()):
        return user
    return {"message": "invalid user"}

@app.get("/ch01/delete/users/pending")
def delete_pending_users(accounts: List[str] = []):
    for user in accounts:
        del pending_users[user]
    return {"message": "pending users deleted"}

@app.get("/ch01/login/password/change")
def change_password(username: str, old_password: str, new_password: str):
    passwd_len = 8
    if valid_users.get(username) == None:
        return {"message": "user does not exist"}
    if old_password == '' or new_password == '':
        characters = ascii_lowercase
        temp_passwd = ''.join(random.choice(characters) for i in range(passwd_len))
        user = valid_users.get(username)
        user.password = temp_passwd
        user.passpharse = hashpw(temp_passwd.encode(), gensalt())
        return user
    user = valid_users.get(username)
    if user.password == old_password:
        user.password = new_password
        user.passphrase = hashpw(new_password.encode(), gensalt())
        return user
    return {"message": "invalid user"}

@app.post("/ch01/login/username/unlock")
def unlock_username(id: Optional[UUID] = None):
    if id == None:
        return {"message": "token needed"}
    for key, val in valid_users.items():
        if val.id == id:
            return {"message": val.username}
    return {"message": "invalid token"}

@app.post("/ch01/login/password/unlock")
def unlock_password(username: Optional[str] = None, id: Optional[UUID] = None):
    if username == None:
        return { "message": "username is required" }
    if valid_users.get(username) == None:
        return { "message": "user does not exist" }
    if id == None:
        return { "message": "token needed" }
    user = valid_users.get(username)
    if user.id == id:
        return { "message": user.password }
    return { "message": "invalid token" }
    
@app.post("/ch01/login/validate", response_model=ValidUser)
def approve_user(user: User):
    if not valid_users.get(user.username) == None:
        return ValidUser(id=None, username=None, password=None, passphrase=None)
    valid_user = ValidUser(id=uuid1(), username=user.username, password=user.password, passphrase=hashpw(user.password.encode(), gensalt()))
    valid_users[user.username] = valid_user
    del pending_users[user.username]
    return valid_user
