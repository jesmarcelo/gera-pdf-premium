@echo off
rem gera-pdf-premium · ponto de entrada (Windows)
rem   gerar.cmd verificar        pre-requisitos, sem depender de Python
rem   gerar.cmd <subcomando> ... repassa para gerar.py
setlocal EnableExtensions
chcp 65001 >nul
set "DIR=%~dp0"
rem tudo dentro do projeto (ambiente, caches, temporarios)
set "BASE=%CD%\.gera-pdf-premium"
if defined GERA_PDF_PREMIUM_VENV (set "VENV=%GERA_PDF_PREMIUM_VENV%") else (set "VENV=%BASE%\venv")

if /I "%~1"=="verificar" goto :verificar

rem gerar.py troca o temporario por uma subpasta por execucao e apaga ao terminar
set "TMP=%BASE%\tmp\boot"
set "TEMP=%TMP%"
set "UV_CACHE_DIR=%BASE%\cache\uv"
set "PIP_CACHE_DIR=%BASE%\cache\pip"
set "UV_PYTHON_INSTALL_DIR=%BASE%\python"
if not exist "%TMP%" mkdir "%TMP%"

if exist "%VENV%\Scripts\python.exe" (
  "%VENV%\Scripts\python.exe" "%DIR%gerar.py" %*
  exit /b %ERRORLEVEL%
)
where uv >nul 2>&1 && (
  uv run --quiet --no-project --python 3.12 "%DIR%gerar.py" %*
  exit /b %ERRORLEVEL%
)
if exist "%USERPROFILE%\.local\bin\uv.exe" (
  "%USERPROFILE%\.local\bin\uv.exe" run --quiet --no-project --python 3.12 "%DIR%gerar.py" %*
  exit /b %ERRORLEVEL%
)
where py >nul 2>&1 && (
  py -3 "%DIR%gerar.py" %*
  exit /b %ERRORLEVEL%
)
where python >nul 2>&1 && (
  python "%DIR%gerar.py" %*
  exit /b %ERRORLEVEL%
)
echo ERRO: nao encontrei Python 3.10+ nem o uv. Rode: "%DIR%gerar.cmd" verificar 1>&2
exit /b 5

:verificar
set FALTA=0
echo SISTEMA windows
set "UVOK="
where uv >nul 2>&1 && set UVOK=1
if exist "%USERPROFILE%\.local\bin\uv.exe" set UVOK=1
if defined UVOK (echo OK uv) else (echo FALTA uv ^| instalar: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex")

set "PYOK="
where py >nul 2>&1 && set PYOK=1
where python >nul 2>&1 && set PYOK=1
if defined PYOK (echo OK python) else (
  if defined UVOK (echo OK python ^(sera baixado pelo uv: uv python install 3.12^)) else (
    set FALTA=1
    echo FALTA python ^| instalar: winget install Python.Python.3.12
  )
)

set "PGOK="
where libpango-1.0-0.dll >nul 2>&1 && set PGOK=1
if exist "%VENV%\Scripts\python.exe" "%VENV%\Scripts\python.exe" -c "import weasyprint" >nul 2>&1 && set PGOK=1
if defined PGOK (echo OK pango) else (
  set FALTA=1
  echo FALTA pango ^| instalar: winget install MSYS2.MSYS2 e depois, no terminal MSYS2: pacman -S mingw-w64-ucrt-x86_64-pango ; acrescente C:\msys64\ucrt64\bin ao PATH
)

where tesseract >nul 2>&1 && (echo OK tesseract) || (echo OPCIONAL tesseract ^| instalar: winget install UB-Mannheim.TesseractOCR   ^(so para PDF escaneado^))

if exist "%VENV%\Scripts\python.exe" (echo OK ambiente %VENV%) else (echo PENDENTE ambiente ^(criado sozinho no primeiro uso: gerar.cmd setup^))
if "%FALTA%"=="0" (echo RESULTADO pronto & exit /b 0) else (echo RESULTADO faltam pre-requisitos & exit /b 1)
