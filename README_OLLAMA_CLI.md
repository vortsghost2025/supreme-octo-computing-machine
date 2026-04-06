# Ollama Command‑Line Helper

This repository ships a tiny **Python** utility (`ollama_cli.py`) that lets you interact with the locally running Ollama server **without a graphical UI**. It is designed for users who rely on screen‑readers or copy‑paste workflows.

## Prerequisites
* Python 3.11+ installed on the machine where Ollama is running.
* The Ollama service must be active (default address `http://127.0.0.1:11434`).
* The backend already reads `OLLAMA_BASE_URL` – you can keep the default or set it to a different host/port.

## Usage
```bash
python ollama_cli.py "<your prompt>" [--model MODEL]
```
* `<your prompt>` – the text you want the model to complete.
* `--model` – optional model identifier. Defaults to `llama3:8b`.

Example:
```bash
python ollama_cli.py "Explain the difference between TCP and UDP" --model llama3:latest
```
The script prints the raw response to *stdout*, making it easy to pipe to other tools or copy‑paste into another Kilo agent.

## Why this helps you
* **No UI** – you avoid navigating the web UI, which can be difficult with limited vision.
* **Screen‑reader friendly** – the output is plain text.
* **Integrates with Kilo** – you can copy the response and feed it to any other agent via the Kilo CLI.

## Adding to your PATH (optional)
If you want to call the script from anywhere, add the repository root to your `PATH` or create a small batch file:
```bat
@echo off
python S:\supreme-octo-computing-machine-main\ollama_cli.py %*
```
Save it as `ollama.bat` and place it in a directory on your `PATH`.

---
*The backend already uses the same `OLLAMA_BASE_URL` environment variable, so the CLI and the SNAC API share the same model instance and GPU resources.*
