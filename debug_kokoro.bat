@echo off
REM Debug script to test Kokoro installation methods

echo ========================================
echo Kokoro Installation Tester
echo ========================================
echo.

REM Activate venv if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo Testing: pip install kokoro
echo ----------------------------------------
pip install kokoro
if errorlevel 1 (
    echo Result: INSTALLATION FAILED
    echo.
    echo Trying with verbose output...
    pip install kokoro -v
    pause
    exit /b 1
)

echo.
echo Testing import...
python -c "from kokoro import KPipeline; print('SUCCESS: Kokoro works!')"
if errorlevel 1 (
    echo Result: IMPORT FAILED
    echo.
    echo Checking what was installed...
    pip show kokoro
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Kokoro v0.9.4 is working
echo ========================================
echo.
echo Testing import...
python -c "from kokoro import KPipeline; print('Import works!'); p = KPipeline(lang_code='a'); print('Pipeline created!'); print('Kokoro is ready to use!')"
echo.
echo You can now run build_windows.bat successfully!
pause