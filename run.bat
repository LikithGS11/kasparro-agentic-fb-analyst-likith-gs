@echo off
REM Kasparro Agentic FB Analyst - Windows Batch Script

if "%1"=="setup" goto setup
if "%1"=="run" goto run
if "%1"=="test" goto test
if "%1"=="lint" goto lint
goto help

:setup
echo Setting up virtual environment and installing dependencies...
python -m venv venv
"%CD%\venv\Scripts\python.exe" -m pip install --upgrade pip
"%CD%\venv\Scripts\pip.exe" install -r requirements.txt
echo Setup complete.
goto end

:run
if "%2"=="" (
    goto help
)
setlocal enabledelayedexpansion
set "QUERY=%2 %3 %4 %5"
set "QUERY=!QUERY:  = !"
set "QUERY=!QUERY: = !"
echo Running analysis for query: !QUERY!
set PYTHONHOME=
set PATH=%CD%\venv\Scripts;%PATH%
"%CD%\venv\Scripts\python.exe" src/orchestrator/run.py "!QUERY!"
endlocal
goto end

:test
echo Running tests...
"%CD%\venv\Scripts\python.exe" -m pytest tests/ -v
goto end

:lint
echo Running linter...
"%CD%\venv\Scripts\flake8.exe" src/ tests/
goto end

:help
echo Usage: run.bat [command] [args]
echo Commands:
echo   setup          - Set up virtual environment and install dependencies
echo   run "query"     - Run analysis with the given query
echo   test            - Run tests
echo   lint            - Run linter
echo Example: run.bat run "Analyze ROAS drop"
goto end

:end
