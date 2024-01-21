from typing import Union, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

from jose import JWSError, jwt #Encriptacion - Desencriptacion
from datetime import datetime, timedelta
from config import SECRET_KEY #Importamos SECRET_KEY de config.py
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    birth_date: Optional[datetime] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None

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


# --- APP ROUTING --- #

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
    new_user = users_collection.find_one({"_id": result.inserted_id}, {'_id': 0})
   

    # Crear el token para el nuevo usuario
    token = create_token(data={"sub": new_user["username"]})

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
    existing_user = users_collection.find_one({"username": user_data.username}, {'_id': 0})
    if not existing_user or existing_user["password"] != user_data.password: #hash_password(user_data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Crear el token para el usuario autenticado
    token = create_token(data={"sub": existing_user["username"]})

    return {"token": token, "user": existing_user }

# Ruta protegida que requiere un token válido para acceder
@app.get("/protected")
def protected_route(token: str = Depends(OAuth2PasswordBearer(tokenUrl="signin"))):
    user_data = decode_token(token)
    return {"message": "This is a protected route", "user": user_data}

#def hash_password(password: str):
#    return password


@app.post("/routines")
def save_routine():
    pass 

@app.get("/routines/{routine_id}")
def get_routine():
    # I should pass and id and it should return my routine
    pass

@app.post("/routines/{routine_id}/exercises/")
def save_exercise():
    pass

@app.get("/routines/{routine_id}/exercises/{exercise_id}")
def save_exercise():
    pass
