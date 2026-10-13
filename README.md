# Drishti Care — SQLite + NVIDIA GPU development build

This Streamlit prototype uses SQLite (included with Python) and trains EfficientNet-B0 only on a CUDA-enabled NVIDIA GPU. No MySQL Server or MySQL Workbench is required for local development.

## Safety boundary
Research/demo software only; not a validated medical device. Use synthetic data in public demos. An ordinary webcam is not a retinal fundus camera. Real screening requires suitable retinal-imaging hardware, independent clinical validation, privacy/security review, and applicable regulatory/institutional review.

## Requirements
- Windows 10/11, Python 3.11 64-bit
- NVIDIA RTX 4050 and compatible NVIDIA driver
- Internet access for packages, pretrained weights, and Kaggle data

## 1. Open the correct folder
In VS Code choose File → Open Folder and select the folder containing `app.py` and `requirements.txt`. Your terminal log showed `D:\Downloads(D)\DrishtiCare-AI\DrishtiCare-AI`; do not run `cd D:\DrishtiCare-AI` unless that folder actually exists.

## 2. Install base dependencies
Run in PowerShell from the project root:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Install CUDA-enabled PyTorch
Your earlier output showed `torch 2.5.1+cpu` and `CUDA available: False`. Remove the CPU-only build and install the official CUDA 12.4 wheels:
```powershell
python -m pip uninstall -y torch torchvision torchaudio
python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
```
Official instructions: https://pytorch.org/get-started/previous-versions/
You need a compatible NVIDIA driver. The PyTorch wheel includes CUDA runtime libraries; the full CUDA Toolkit is normally not needed just to run PyTorch.

Verify:
```powershell
nvidia-smi
python scripts\check_environment.py
python -c "import torch; print('Torch:',torch.__version__); print('CUDA:',torch.cuda.is_available()); print('GPU:',torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NOT DETECTED')"
```
Do not train until CUDA is `True` and the GPU name includes RTX 4050.

## 4. Configure SQLite
```powershell
Copy-Item .env.example .env
```
The default URL is `sqlite:///./drishti_care.db`. SQLite creates this file locally; no database server or separate database app is required.

## 5. Initialize database and create admin
```powershell
python scripts\init_db.py
python scripts\create_admin.py
```
Create a strong password at the prompt.

## 6. Run the app
```powershell
streamlit run app.py
```
Open the local URL shown, usually http://localhost:8501. Upload and webcam functions are for software demonstration; a webcam is not retinal imaging hardware.

## 7. Download APTOS 2019
Download under Kaggle's terms: https://www.kaggle.com/competitions/aptos2019-blindness-detection/data
Arrange:
```text
data/
  train.csv
  train_images/
    <id_code>.png
```
The CSV must have `id_code` and `diagnosis`.

## 8. Train only on the local RTX 4050
The training script stops if CUDA is unavailable; it does not fall back to CPU. Start with batch size 8:
```powershell
python training\train.py --data-dir data --output-dir ai\artifacts --epochs 5 --batch-size 8
```
If CUDA runs out of memory, retry with `--batch-size 4` or `--batch-size 2`. Keep the laptop plugged in and monitor temperature/VRAM. Mixed precision is enabled to reduce memory usage.

Expected artifacts:
```text
ai\artifacts\
  efficientnet_b0.pth
  model_metadata.json
```

## 9. Tests
```powershell
pytest -q
```
These are starter tests, not full production security or clinical validation.

## Evaluation warning
The provided evaluation script is only a preliminary sanity check; if its images were used during training, its results are not independent test performance. Create a locked test set, prevent duplicate leakage, define the screening endpoint with clinical input, and evaluate sensitivity, specificity, calibration, image-quality failures and relevant subgroups.

## Deployment
SQLite is suitable for local development and single-machine demos. For a multi-user public deployment, migrate to a managed server database and private persistent image storage. The local RTX 4050 is available to local training, not automatically to a separately hosted cloud website. Use synthetic data for public demos and do not use this prototype for patient-care decisions.
