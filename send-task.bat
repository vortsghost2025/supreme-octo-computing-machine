@echo off
REM Quick task sender for SNAC v2
REM Usage: send-task.bat "QUERY: What is 2+2?"

set VPS_IP=187.77.3.56
set API_URL=http://%VPS_IP%:8000

if "%~1"=="" (
    echo Usage: send-task.bat "TASK DESCRIPTION"
    echo Example: send-task.bat "QUERY: What is 2+2?"
    exit /b 1
)

echo Sending task: %~1
curl -s -X POST "%API_URL%/agent/run" -H "Content-Type: application/json" -d "{\"task\":\"%~1\"}"
echo.
