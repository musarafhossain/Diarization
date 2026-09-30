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

## 4. Download Offline Models (into `dist\models`)

To download Pyannote segmentation and embedding models directly into `dist\models`:
```powershell
python .\src\download_models.py <YOUR_HF_TOKEN>
```
> **Note**:
> - If you have set `$env:HF_TOKEN="your_token"` or already authenticated via `huggingface-cli login`, you can simply run:
>   ```powershell
>   python .\src\download_models.py
>   ```
> - The script automatically saves the models to `.\dist\models` and ensures `config.yaml` is properly configured.

---

## 5. Running Diarization

### Option A: Using the Python Environment (Source Code)
Once `.venv` is activated:
```powershell
python .\src\diarize.py --audio_path ".\voice\21a48b5e-fb13-489a-acb9-bd952a28eca0.wav" --output_dir ".\output" --model_dir ".\dist\models"
```

### Option B: Using the Standalone Build Executable (Distribution)
(Does not require activating `.venv`):
```powershell
.\dist\diarize.exe --audio_path ".\voice\21a48b5e-fb13-489a-acb9-bd952a28eca0.wav" --output_dir ".\output" --model_dir ".\dist\models"
```

### Device Selection (CPU / GPU)
Use the `--device` flag to control whether diarization runs on CPU or GPU:

| Value  | Behavior |
|--------|----------|
| `auto` | **(Default)** Uses the best available GPU (CUDA → MPS → CPU fallback) |
| `cpu`  | Forces CPU execution even if a GPU is available |
| `cuda` | Forces NVIDIA GPU (CUDA); exits with an error if not available |
| `mps`  | Forces Apple Silicon GPU (Metal); exits with an error if not available |

Examples:
```powershell
# Force CPU (useful for debugging or machines without GPU drivers)
python .\src\diarize.py --audio_path ".\voice\audio.wav" --output_dir ".\output" --model_dir ".\dist\models" --device cpu

# Force NVIDIA GPU (Windows / Linux)
python .\src\diarize.py --audio_path ".\voice\audio.wav" --output_dir ".\output" --model_dir ".\dist\models" --device cuda

# Force Apple Silicon GPU (macOS M1/M2/M3/M4)
python src/diarize.py --audio_path "./voice/audio.wav" --output_dir "./output" --model_dir "./dist/models" --device mps

# Auto-detect (default, same as omitting --device)
.\dist\diarize.exe --audio_path ".\voice\audio.wav" --output_dir ".\output" --model_dir ".\dist\models" --device auto
```

---

## 6. Building the Executable (PyInstaller)

> **Important**: PyInstaller **cannot cross-compile**. You must build on the same OS you are targeting. A Windows machine produces `.exe`, Linux produces a Linux binary, macOS produces a macOS binary.

### Build Command

With `.venv` activated, run from the project root:
```
python -m PyInstaller diarize.spec
```
*(Running via `python -m PyInstaller` prevents path launcher errors if the environment directory was moved or renamed).*

| Platform | Output |
|----------|--------|
| Windows  | `dist\diarize.exe` |
| Linux    | `dist/diarize` |
| macOS    | `dist/diarize` |

### Common Steps (all platforms)

**Step 1 — Clone and create virtual environment:**
```bash
git clone <your-repo-url>
cd Diarization
python -m venv .venv
```

**Step 2 — Activate the virtual environment:**

| Platform           | Command |
|--------------------|---------|
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows CMD        | `.\.venv\Scripts\activate.bat` |
| Linux / macOS      | `source .venv/bin/activate` |

Then follow the section below that matches your target device.

---

### Windows — GPU Build (NVIDIA CUDA)

Requires an NVIDIA GPU and drivers on the target machine. Bundles CUDA 12.4 support.

```powershell
# Install PyTorch with CUDA 12.4
pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124

# Install remaining dependencies
pip install -r requirements.txt

# Build
python -m PyInstaller diarize.spec
```

Output: `dist\diarize.exe`
Run with: `--device cuda` or `--device auto`

---

### Windows — CPU-Only Build

Lighter build (~200 MB vs ~2 GB), no GPU dependencies. Runs on any Windows machine.

```powershell
# Install PyTorch (CPU-only)
pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt

# Build
python -m PyInstaller diarize.spec
```

Output: `dist\diarize.exe`
Run with: `--device cpu`

---

### Linux — GPU Build (NVIDIA CUDA)

Requires an NVIDIA GPU and drivers on the target machine. Bundles CUDA 12.4 support.

```bash
# Install PyTorch with CUDA 12.4
pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124

# Install remaining dependencies
pip install -r requirements.txt

# Build
python -m PyInstaller diarize.spec
```

Output: `dist/diarize`
Run with: `--device cuda` or `--device auto`

---

### Linux — CPU-Only Build

Lighter build, no GPU dependencies. Runs on any Linux machine.

```bash
# Install PyTorch (CPU-only)
pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt

# Build
python -m PyInstaller diarize.spec
```

Output: `dist/diarize`
Run with: `--device cpu`

---

### macOS (Apple Silicon M1/M2/M3/M4) — GPU Build (MPS)

Apple Silicon Macs support GPU acceleration via MPS (Metal Performance Shaders). PyTorch includes MPS support automatically.

```bash
# Install PyTorch (MPS backend is included automatically on Apple Silicon)
pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt

# Build
python -m PyInstaller diarize.spec
```

Output: `dist/diarize`
Run with: `--device mps` or `--device auto`

---

### macOS (Intel) — CPU-Only Build

Intel Macs do not support CUDA or MPS. CPU is the only option.

```bash
# Install PyTorch (CPU)
pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt

# Build
python -m PyInstaller diarize.spec
```

Output: `dist/diarize`
Run with: `--device cpu`

---

### After Building

The built binary will be in the `dist/` folder. Distribute it together with the `models/` directory.

> **Notes:**
> - The models (`dist/models/`) are **not** bundled into the executable. Distribute them alongside the binary or use `download_models.py` on the target machine.
> - The `requirements.txt` pins Windows CUDA wheels (`torch==2.6.0+cu124`). On Linux or macOS, pip will skip those since you already installed the correct PyTorch before `pip install -r requirements.txt`.

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

