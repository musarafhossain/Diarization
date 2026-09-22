# Instructions: Virtual Environment & Execution Guide

This document describes how to create, activate, and manage the Python virtual environment, as well as how to run and build the diarization pipeline.

---

## 1. Create a Virtual Environment (Initial Setup)

> **Note**: Python 3.9 or 3.10 is recommended for compatibility with PyTorch, PyAnnote Audio, and SpeechBrain.

### Using Python directly:
```powershell
python -m venv .venv
```

### Using the Python Launcher (specifying Python 3.9 if multiple versions installed):
```powershell
py -3.9 -m venv .venv
```

---

## 2. Activate the Python Virtual Environment

The project uses the local virtual environment located at `.venv`.

### In PowerShell (Recommended / VS Code Default Terminal)
```powershell
.\.venv\Scripts\Activate.ps1
```
> **Note**: If you get a script execution policy error (`running scripts is disabled on this system`), run this once in your PowerShell terminal first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> .\.venv\Scripts\Activate.ps1
> ```

### In Command Prompt (CMD)
```cmd
.\.venv\Scripts\activate.bat
```

### In Git Bash / WSL
```bash
source .venv/Scripts/activate
```

When activated, you will see `(.venv)` at the beginning of your terminal prompt.

---

## 3. Deactivate the Environment
When you are done working:
```bash
deactivate
```

---

## 4. Download Offline Models (into `models`)

To download Pyannote segmentation and embedding models directly into `models` (and mirrored to `dist\models` if present):
```powershell
python .\src\download_models.py <YOUR_HF_TOKEN>
```
> **Note**:
> - If you have set `$env:HF_TOKEN="your_token"` or already authenticated via `huggingface-cli login`, you can simply run:
>   ```powershell
>   python .\src\download_models.py
>   ```
> - The script automatically saves the models to `.\models` (and syncs to `.\dist\models`) and ensures `config.yaml` is properly configured.

---

## 5. Running Diarization

### Option A: Using the Python Environment (Source Code)
Once `.venv` is activated:
```powershell
python .\src\diarize.py --audio_path ".\voice\21a48b5e-fb13-489a-acb9-bd952a28eca0.wav" --output_dir ".\output" --model_dir ".\models"
```

### Option B: Using the Standalone Build Executable (Distribution)
(Does not require activating `.venv`):
```powershell
.\dist\diarize.exe --audio_path ".\voice\21a48b5e-fb13-489a-acb9-bd952a28eca0.wav" --output_dir ".\output" --model_dir ".\dist\models"
```

---

## 6. Rebuilding the Executable (PyInstaller)
With `.venv` activated:
```powershell
python -m PyInstaller diarize.spec
```
*(Running via `python -m PyInstaller` prevents path launcher errors if the environment directory was moved or renamed).*

---

## 7. Requirements Management

### Generate `requirements.txt`
When `.venv` is activated:
```powershell
pip freeze > requirements.txt
```

Alternatively (without activating `.venv`):
```powershell
.\.venv\Scripts\python.exe -m pip freeze > requirements.txt
```

### Install from `requirements.txt`
In a new or existing virtual environment:
```powershell
pip install -r requirements.txt
```

