@echo off
cd /d "%~dp0"
echo ========================================
echo    Building Python Authenticator
echo ========================================

python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
    if errorlevel 1 goto failed
)

echo.
echo Building main executable...
python -m PyInstaller --onefile ^
    --windowed ^
    --noconfirm ^
    --clean ^
    --name "PythonAuthenticator" ^
    --icon=icon.ico ^
    --add-data "icon.ico;." ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=cryptography ^
    --hidden-import=pyotp ^
    --hidden-import=sqlite3 ^
    --hidden-import=pystray ^
    --hidden-import=keyboard ^
    main.py
if errorlevel 1 goto failed
if not exist "dist\PythonAuthenticator.exe" goto failed

echo.
echo ========================================
echo   BUILD COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo Executable: dist\PythonAuthenticator.exe
echo.
echo DATA STORAGE:
echo   - All files created in same folder as executable
echo   - config.json: Application settings
echo   - authenticator.db: Encrypted account data
echo   - key.key: Encryption key
echo.
echo PORTABLE SETUP:
echo   - Copy entire dist\ folder to move application
echo   - No registry or AppData usage
echo   - Clean and portable installation
echo.
echo To run: dist\PythonAuthenticator.exe
echo.
pause
exit /b 0

:failed
echo.
echo ========================================
echo      BUILD FAILED
echo ========================================
echo.
echo Check error messages above
echo.
pause
exit /b 1
