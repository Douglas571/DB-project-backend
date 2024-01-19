from typing import Union

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWSError, jwt #Encriptacion - Desencriptacion
from datetime import datetime, timedelta
from config import SECRET_KEY #Importamos SECRET_KEY de config.py
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel

app = FastAPI()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Conectar a la base de datos MongoDB
DATABASE_URL = "mongodb://localhost:27017"
client = MongoClient(DATABASE_URL)
db = client["appdb"]
users_collection = db["users"]

# Modelos de datos
class UserCreate(BaseModel):
    username: str
    password: str
    #birth_date: datetime
    #weight_kg: float
    #height_cm: float

class UserLogin(BaseModel):
    username: str
    password: str

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

# Funciones auxiliares para manejar tokens
def create_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWSError:
        raise credentials_exception

@app.post("/singup")
def singup(user_data: UserCreate):
    # Verificar si el usuario ya existe
    existing_user = users_collection.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Crear un nuevo usuario en la base de datos
    user_data_dict = user_data.model_dump()
    #user_data_dict["password"] = hash_password(user_data_dict["password"])  # Recuerda implementar la función hash_password

    result = users_collection.insert_one(user_data_dict)

    # Obtener el nuevo usuario creado
    new_user = users_collection.find_one({"_id": result.inserted_id})

    # Crear el token para el nuevo usuario
    token = create_token(data={"sub": str(new_user["_id"])})
    #user = {}
    #token = create_token(data=user)
    #user = {"username": "example_user", "email": "user@example.com"}

    # regist the user
    # create the token

    return {"token": token, "user": new_user}

@app.post("/singin")
def singin(user_data: UserLogin):
    #user = {"username": "example_user", "email": "user@example.com"}
    #user = {}
    #token = create_token(data=user)

    # check the user
    # create the token

    # Verificar si el usuario existe
    existing_user = users_collection.find_one({"username": user_data.username})
    if not existing_user or existing_user["password"] != user_data.password: #hash_password(user_data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Crear el token para el usuario autenticado
    token = create_token(data={"sub": str(existing_user["_id"])})

    return {"token": token}

# Ruta protegida que requiere un token válido para acceder
@app.get("/protected")
def protected_route(token: str = Depends(OAuth2PasswordBearer(tokenUrl="signin"))):
    user_data = decode_token(token)
    return {"message": "This is a protected route", "user": user_data}

#def hash_password(password: str):
#    return password