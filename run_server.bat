@echo off
REM ===============================
REM  Easy Park UTSA Server Starter
REM ===============================

echo Starting Easy Park UTSA server...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Set environment variables
set VISION_MODE=real
set CAMERA_SOURCE=parking_crop_loop.mp4

REM Run FastAPI with uvicorn on port 8001
uvicorn main:app --reload --port 8001

REM Keep window open if server exits
pause
