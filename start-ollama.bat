@echo off
set OLLAMA_HOST=0.0.0.0:9001
start "" "C:\Users\seand\AppData\Local\Programs\Ollama\ollama.exe" serve
timeout /t 8 /nobreak >nul
netstat -ano | findstr 9001
