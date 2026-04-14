@echo off
echo Starting Ollama on all interfaces (port 9001)...
set OLLAMA_HOST=0.0.0.0:9001
start "Ollama Server" ollama serve
timeout /t 3 >nul
echo.
echo Ollama is now listening on:
echo   - Localhost: http://localhost:9001
echo   - Network:   http://0.0.0.0:9001
echo.
echo Available models:
ollama list
echo.
echo Press any key to stop Ollama...
pause >nul
taskkill /IM "ollama.exe" /F
