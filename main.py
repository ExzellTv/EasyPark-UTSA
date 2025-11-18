import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import app.config  # Load environment variables first
import app.routers.parking as parking

app = FastAPI(title="Easy Park UTSA")

# --- Handle both cases for static directory ---
root_static = os.path.join(os.path.dirname(__file__), "static")
app_static = os.path.join(os.path.dirname(__file__), "app", "static")

if os.path.isdir(root_static):
    static_dir = root_static
elif os.path.isdir(app_static):
    static_dir = app_static
else:
    raise RuntimeError("Static directory not found")

# --- Register the parking API routes ---
app.include_router(parking.router)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

