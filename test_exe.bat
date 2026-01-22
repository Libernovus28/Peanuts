@echo off
REM Test the built executable and show any errors

echo ========================================
echo Testing NovelNarrator.exe
echo ========================================
echo.

if not exist "dist\NovelNarrator\NovelNarrator.exe" (
    echo ERROR: NovelNarrator.exe not found!
    echo Please build first using build_windows.bat
    pause
    exit /b 1
)

echo Executable found at: dist\NovelNarrator\NovelNarrator.exe
echo.
echo Testing in console mode to see any errors...
echo Press Ctrl+C to stop if it hangs
echo.
echo ----------------------------------------
echo.

cd dist\NovelNarrator
NovelNarrator.exe

echo.
echo ----------------------------------------
echo.
echo If you saw an error above, please:
echo 1. Take a screenshot
echo 2. Rebuild with console mode (option 2 in build script)
echo.
pause