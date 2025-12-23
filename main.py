from fastapi import FastAPI, HTTPException
from schemas import RegisterRequest, LoginRequest
from security import hash_password, verify_password
from users import users_db
from jwt_utils import create_access_token
from dependencies import get_current_user
from fastapi import Depends


app = FastAPI()

@app.post("/auth/register")
def register(data: RegisterRequest):
    # check if user exists
    for user in users_db:
        if user["email"] == data.email:
            raise HTTPException(status_code=400, detail="Email already exists")

    hashed = hash_password(data.password)

    users_db.append({
        "email": data.email,
        "password": hashed
    })

    return {"message": "User registered"}

@app.post("/auth/login")
def login(data: LoginRequest):
    for user in users_db:
        if user["email"] == data.email:
            if verify_password(data.password, user["password"]):
                token = create_access_token({
                    "sub": data.email,
                    "role": "student"
                })
                return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/protected")
def protected_route(user=Depends(get_current_user)):
    return {
        "message": "You are authorized",
        "user": user
    }


