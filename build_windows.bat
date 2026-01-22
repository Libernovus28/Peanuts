@echo off
REM Novel Narrator - Windows Build Script
REM Mirrors the Ubuntu setup_runner.sh functionality

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo                   NOVEL NARRATOR - WINDOWS BUILD SCRIPT
echo                  Professional Audiobook Generator - v3.2
echo ================================================================================
echo.

REM === Configuration ===
set PROJECT_ROOT=%CD%
set VENV_DIR=%PROJECT_ROOT%\venv
set PYTHON_PROGRAM=%PROJECT_ROOT%\novel_narrator_gui.py
set LOG_DIR=%PROJECT_ROOT%\logs
set OUTPUT_DIR=%PROJECT_ROOT%\output
set BUILD_DIR=%PROJECT_ROOT%\dist
set ICON_FILE=%PROJECT_ROOT%\icon.ico

REM === Colors (Windows 10+) ===
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM === Create directories ===
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM === STEP 1: Check Python ===
echo %BLUE%[1/7] Checking Python installation...%NC%
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%ERROR: Python is not installed or not in PATH%NC%
    echo.
    echo Please install Python 3.9-3.11 from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PY_VERSION=%%V
echo %GREEN%Found Python %PY_VERSION%%NC%

REM Check Python version (need 3.9+)
for /f "tokens=1,2 delims=." %%a in ("%PY_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)
if %MAJOR% LSS 3 (
    echo %RED%ERROR: Python 3.9+ required, found %PY_VERSION%%NC%
    pause
    exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% LSS 9 (
    echo %RED%ERROR: Python 3.9+ required, found %PY_VERSION%%NC%
    pause
    exit /b 1
)

echo.
REM === STEP 2: Create virtual environment ===
echo %BLUE%[2/7] Setting up virtual environment...%NC%
if exist "%VENV_DIR%" (
    echo Virtual environment exists, checking validity...
    if not exist "%VENV_DIR%\Scripts\python.exe" (
        echo %YELLOW%Corrupted venv detected, recreating...%NC%
        rmdir /s /q "%VENV_DIR%"
    )
)

if not exist "%VENV_DIR%" (
    echo Creating new virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo %RED%ERROR: Failed to create virtual environment%NC%
        pause
        exit /b 1
    )
    echo %GREEN%Virtual environment created%NC%
) else (
    echo %GREEN%Virtual environment ready%NC%
)

echo.
REM === STEP 3: Activate venv and upgrade pip ===
echo %BLUE%[3/7] Activating virtual environment...%NC%
call "%VENV_DIR%\Scripts\activate.bat"

echo Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel --quiet
echo %GREEN%Tools upgraded%NC%

echo.
REM === STEP 4: Install dependencies ===
echo %BLUE%[4/7] Installing dependencies...%NC%
echo This may take 5-15 minutes depending on your internet connection...
echo.

REM Check for NVIDIA GPU
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%No NVIDIA GPU detected - installing CPU-only PyTorch%NC%
    set TORCH_INDEX=https://download.pytorch.org/whl/cpu
    set GPU_MODE=CPU
) else (
    echo %GREEN%NVIDIA GPU detected - installing CUDA-enabled PyTorch%NC%
    set TORCH_INDEX=https://download.pytorch.org/whl/cu121
    set GPU_MODE=GPU
)

echo.
echo Installing core dependencies:
echo   - PyQt6 (GUI framework)
echo   - PyTorch + torchaudio (%GPU_MODE% version)
echo   - Kokoro TTS engine
echo   - Document readers (docx, odt)
echo.

REM Install in specific order for best compatibility
pip install --quiet PyQt6
if errorlevel 1 (
    echo %RED%ERROR: Failed to install PyQt6%NC%
    pause
    exit /b 1
)
echo %GREEN%[OK]%NC% PyQt6

pip install --quiet --index-url %TORCH_INDEX% torch torchaudio
if errorlevel 1 (
    echo %RED%ERROR: Failed to install PyTorch%NC%
    pause
    exit /b 1
)
echo %GREEN%[OK]%NC% PyTorch + torchaudio

echo Installing Kokoro TTS (this may take a moment)...
pip install --quiet kokoro
if errorlevel 1 (
    echo %RED%ERROR: Failed to install Kokoro%NC%
    pause
    exit /b 1
)
echo %GREEN%[OK]%NC% Kokoro TTS (v0.9.4)

pip install --quiet python-docx odfpy
echo %GREEN%[OK]%NC% Document readers

pip install --quiet pyinstaller
echo %GREEN%[OK]%NC% PyInstaller

echo.
echo %GREEN%All dependencies installed successfully!%NC%

echo.
REM === STEP 5: Validate program ===
echo %BLUE%[5/7] Validating program files...%NC%

if not exist "%PYTHON_PROGRAM%" (
    echo %RED%ERROR: Program file not found: %PYTHON_PROGRAM%%NC%
    echo.
    echo Please ensure novel_narrator_gui.py is in the project directory
    pause
    exit /b 1
)

echo Checking Python syntax...
python -m py_compile "%PYTHON_PROGRAM%" 2>nul
if errorlevel 1 (
    echo %RED%ERROR: Python syntax error in program%NC%
    pause
    exit /b 1
)

echo %GREEN%Program file validated%NC%

echo.
REM === STEP 6: Test imports ===
echo %BLUE%[6/7] Testing critical imports...%NC%

python -c "import PyQt6; print('PyQt6 OK')" 2>nul
if errorlevel 1 (
    echo %RED%ERROR: PyQt6 import failed%NC%
    pause
    exit /b 1
)

python -c "import torch; print('PyTorch OK')" 2>nul
if errorlevel 1 (
    echo %RED%ERROR: PyTorch import failed%NC%
    pause
    exit /b 1
)

python -c "from kokoro import KPipeline; print('Kokoro OK')" 2>nul
if errorlevel 1 (
    echo %RED%ERROR: Kokoro import failed%NC%
    pause
    exit /b 1
)

echo %GREEN%All imports verified%NC%

echo.
REM === STEP 7: Build or Run ===
echo %BLUE%[7/7] Choose action:%NC%
echo.
echo   [1] Run in development mode (no building)
echo   [2] Build standalone executable
echo   [3] Exit
echo.
set /p ACTION="Select option (1-3): "

if "%ACTION%"=="1" goto RUN_DEV
if "%ACTION%"=="2" goto BUILD_EXE
goto END

:RUN_DEV
echo.
echo %GREEN%Starting Novel Narrator in development mode...%NC%
echo %YELLOW%Press Ctrl+C to stop%NC%
echo.
python "%PYTHON_PROGRAM%"
goto END

:BUILD_EXE
echo.
echo %BLUE%Building standalone executable...%NC%
echo This will take 5-10 minutes...
echo.

REM Check for icon
if not exist "%ICON_FILE%" (
    echo %YELLOW%Warning: icon.ico not found, using default%NC%
    set ICON_PARAM=
) else (
    echo Found icon file: %ICON_FILE%
    set ICON_PARAM=--icon="%ICON_FILE%"
)

REM Clean previous builds
if exist "%BUILD_DIR%" (
    echo Cleaning previous build...
    rmdir /s /q "%BUILD_DIR%" 2>nul
)
if exist "build" (
    rmdir /s /q "build" 2>nul
)

echo.
echo Building with PyInstaller...
echo.
echo Would you like to build in:
echo   [1] Window mode (no console, normal .exe)
echo   [2] Console mode (shows errors, for debugging)
echo.
set /p BUILD_MODE="Select mode (1 or 2): "

if "%BUILD_MODE%"=="2" (
    set CONSOLE_FLAG=--console
    echo Building in CONSOLE mode for debugging...
) else (
    set CONSOLE_FLAG=--windowed
    echo Building in WINDOW mode...
)

pyinstaller --name="NovelNarrator" ^
    --onedir ^
    %CONSOLE_FLAG% ^
    %ICON_PARAM% ^
    --hidden-import=PyQt6 ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=torch ^
    --hidden-import=torchaudio ^
    --hidden-import=kokoro ^
    --hidden-import=docx ^
    --hidden-import=odf ^
    --hidden-import=odf.opendocument ^
    --hidden-import=odf.text ^
    --collect-all kokoro ^
    --collect-all PyQt6 ^
    --noconfirm ^
    --clean ^
    "%PYTHON_PROGRAM%"

if errorlevel 1 (
    echo %RED%ERROR: Build failed%NC%
    pause
    exit /b 1
)

echo.
echo %GREEN%Build complete!%NC%
echo.
echo Creating output directory structure...
mkdir "%BUILD_DIR%\NovelNarrator\output" 2>nul
mkdir "%BUILD_DIR%\NovelNarrator\logs" 2>nul

REM Create README in dist
echo Novel Narrator - Audiobook Generator> "%BUILD_DIR%\NovelNarrator\README.txt"
echo.>> "%BUILD_DIR%\NovelNarrator\README.txt"
echo INSTRUCTIONS:>> "%BUILD_DIR%\NovelNarrator\README.txt"
echo 1. Double-click NovelNarrator.exe to start>> "%BUILD_DIR%\NovelNarrator\README.txt"
echo 2. Select your book file (.txt, .docx, or .odt)>> "%BUILD_DIR%\NovelNarrator\README.txt"
echo 3. Choose a voice and reading speed>> "%BUILD_DIR%\NovelNarrator\README.txt"
echo 4. Click "Generate Audiobook">> "%BUILD_DIR%\NovelNarrator\README.txt"
echo 5. Your audiobook will be saved in the 'output' folder>> "%BUILD_DIR%\NovelNarrator\README.txt"
echo.>> "%BUILD_DIR%\NovelNarrator\README.txt"
echo REQUIREMENTS:>> "%BUILD_DIR%\NovelNarrator\README.txt"
echo - Windows 10 or 11>> "%BUILD_DIR%\NovelNarrator\README.txt"
echo - 4GB RAM minimum (8GB recommended)>> "%BUILD_DIR%\NovelNarrator\README.txt"
echo - GPU optional but recommended for faster processing>> "%BUILD_DIR%\NovelNarrator\README.txt"

echo.
echo ================================================================================
echo                           BUILD SUCCESSFUL!
echo ================================================================================
echo.
echo Location: %BUILD_DIR%\NovelNarrator\
echo Executable: NovelNarrator.exe
echo.
echo NEXT STEPS:
echo 1. Test the executable: cd "%BUILD_DIR%\NovelNarrator" ^&^& NovelNarrator.exe
echo 2. Sign the executable (optional): see signing_guide.md
echo 3. Distribute the entire NovelNarrator folder
echo.
echo To create a ZIP for distribution:
echo   - Right-click the NovelNarrator folder
echo   - Select "Send to" ^> "Compressed (zipped) folder"
echo.
pause
goto END

:END
echo.
echo %GREEN%Setup complete!%NC%
echo.
endlocal