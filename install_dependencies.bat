@echo off
cd /d "%~dp0"
echo ========================================
echo   Instalando Dependencias do Sistema
echo ========================================

echo.
echo Instalando bibliotecas de requirements.txt...
python -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo.
echo Instalando PyInstaller...
python -m pip install pyinstaller
if errorlevel 1 goto failed

echo.
echo ========================================
echo    INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Para compilar: build.bat
echo Para executar: python main.py
echo.
pause
exit /b 0

:failed
echo.
echo ========================================
echo    FALHA NA INSTALACAO
echo ========================================
echo.
echo Verifique as mensagens de erro acima
echo.
pause
exit /b 1
