@echo off
setlocal enabledelayedexpansion

echo ================================================
echo   CCMB - build.bat (Windows)
echo ================================================

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: no se encontro "python" en el PATH. Instala Python 3.10+ primero.
    exit /b 1
)

if not exist venv (
    echo Creando entorno virtual en .\venv ...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Instalando dependencias de requirements.txt ...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: fallo la instalacion de dependencias.
    exit /b 1
)

if not exist ccmb.db (
    if not exist CC2022PART2R1.pdf (
        echo ERROR: no se encuentra CC2022PART2R1.pdf ni ccmb.db en esta carpeta.
        exit /b 1
    )
    echo.
    echo Generando ccmb.db desde el PDF ...
    python build_db.py CC2022PART2R1.pdf ccmb.db
    if errorlevel 1 (
        echo ERROR: build_db.py reporto fallos en la verificacion. Revisa el reporte arriba.
        exit /b 1
    )
) else (
    echo ccmb.db ya existe: se omite build_db.py.
    echo ^(borra ccmb.db si queres regenerarlo desde el PDF^)
)

echo.
echo Empaquetando con PyInstaller ...
pyinstaller --noconfirm --onefile --windowed --name CCMB --icon assets\icon.ico ^
    --add-data "ccmb.db;." ^
    --add-data "assets;assets" ^
    main.py

if errorlevel 1 (
    echo ERROR: fallo PyInstaller.
    exit /b 1
)

echo.
echo ================================================
echo   Ejecutable generado en: dist\CCMB.exe
echo ================================================

echo.
echo Buscando Inno Setup para generar el instalador (CCMB_Setup.exe) ...

set "ISCC="
where ISCC >nul 2>nul
if not errorlevel 1 (
    set "ISCC=ISCC"
) else if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
)

if "%ISCC%"=="" (
    echo.
    echo Inno Setup no esta instalado: se omite la generacion del instalador.
    echo Descargalo gratis de https://jrsoftware.org/isdl.php y volve a correr
    echo build.bat para obtener CCMB_Setup.exe. Mientras tanto, dist\CCMB.exe
    echo ya es un ejecutable portable que funciona por si solo.
    goto fin
)

echo Compilando el instalador con Inno Setup ...
"%ISCC%" installer.iss
if errorlevel 1 (
    echo ERROR: fallo la compilacion del instalador con Inno Setup.
    exit /b 1
)

echo.
echo ================================================
echo   Listo. Instalador generado en: installer_output\CCMB_Setup.exe
echo ================================================

:fin
endlocal
