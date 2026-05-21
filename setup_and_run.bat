@echo off
echo =======================================================================
echo              ShieldMail AI - Spam Detector Setup ^& Run
echo =======================================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your PATH variables.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

echo [1/4] Installing Python dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Dependency installation failed. Retrying with --user...
    pip install -r requirements.txt --user
)

:: Check if models have been trained
echo.
echo [2/4] Checking for trained ML model files...
if not exist "model\support_vector_machine_model.pkl" (
    echo [INFO] ML models not found. Running training pipeline...
    python notebooks/train_models.py
    if %errorlevel% neq 0 (
        echo [ERROR] Model training failed. Cannot proceed.
        pause
        exit /b 1
    )
) else (
    echo [SUCCESS] Model files detected! Skipping training.
    echo If you wish to retrain them, delete the files inside the 'model' directory.
)

echo.
echo [3/4] Starting FastAPI backend server...
echo The application will be hosted at: http://127.0.0.1:8000
echo Swagger API docs are available at: http://127.0.0.1:8000/docs
echo.
echo Launching your default browser shortly...
timeout /t 3 /nobreak >nul
start http://127.0.0.1:8000

echo [4/4] Running Uvicorn server...
python backend/run.py

pause
