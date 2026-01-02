from fastapi import FastAPI
from app.database.db import engine
from app.database.db import SessionLocal
from app.models.user import User
from app.database.init_db import init_db
from app.routers import auth, users
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Chatbot Backend API")
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],             # Allow all HTTP methods (GET, POST etc)
    allow_headers=["*"],             # Allow all headers (Authorization included)
)

app.include_router(auth.router)
app.include_router(users.router)

init_db()

@app.get("/")
def root():
    return {"message": "Backend is running"}

@app.get("/db-test")
def db_test():
    try:
        with engine.connect():
            return {"status": "Connected to SQL Server using Windows Authentication"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/users-test")
def users_test():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return users

