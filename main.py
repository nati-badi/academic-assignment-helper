from fastapi import FastAPI, HTTPException
from schemas import RegisterRequest, LoginRequest
from security import hash_password, verify_password
from users import users_db
from jwt_utils import create_access_token
from dependencies import get_current_user
from fastapi import Depends
from fastapi import UploadFile, File, Depends
import os
import shutil
import requests
import uuid



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

@app.post("/upload")
def upload_assignment(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    os.makedirs("uploads", exist_ok=True)

    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    job_id = str(uuid.uuid4())

    payload = {
        "job_id": job_id,
        "file_path": file_path,
        "student_email": user["sub"]
    }

    try:
       requests.post(
        "http://localhost:5678/webhook-test/assignment",
        json=payload,
        timeout=5
)

    except requests.exceptions.RequestException:
        pass  # n8n may not be running yet

    return {
        "message": "File uploaded and analysis started",
        "job_id": job_id
    }
