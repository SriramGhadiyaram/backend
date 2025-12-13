from fastapi import FastAPI
from app.database.db import engine

app = FastAPI(title="Chatbot Backend API")

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
