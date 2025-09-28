from dotenv import load_dotenv
load_dotenv()  # reads .env file, should be done once at startup
from fastapi import FastAPI
from .routers import parking

app = FastAPI(title="EasyPark UTSA")

app.include_router(parking.router)

@app.get("/")
def root():
    return {"message": "EasyPark UTSA API running"}
