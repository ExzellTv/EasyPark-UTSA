from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import parking

app = FastAPI(title="Easy Park UTSA")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static dashboard
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Register parking API routes
app.include_router(parking.router)
